"""Python wrapper for the OverKiz API."""

from __future__ import annotations

import asyncio
import logging
import ssl
import urllib.parse
from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path
from types import TracebackType
from typing import Any, Self, cast

import backoff
from aiohttp import (
    ClientConnectorError,
    ClientResponse,
    ClientSession,
    ServerDisconnectedError,
)
from backoff.types import Details

from pyoverkiz._case import decamelize
from pyoverkiz.action_queue import ActionQueue, ActionQueueSettings
from pyoverkiz.auth import AuthStrategy, Credentials, build_auth_strategy
from pyoverkiz.const import SUPPORTED_SERVERS, USER_AGENT
from pyoverkiz.converter import converter
from pyoverkiz.enums import APIType, ExecutionMode, Protocol, Server
from pyoverkiz.exceptions import (
    ExecutionQueueFullError,
    InvalidEventListenerIdError,
    NoRegisteredEventListenerError,
    NotAuthenticatedError,
    OverkizError,
    TooManyConcurrentRequestsError,
    TooManyExecutionsError,
    UnsupportedOperationError,
)
from pyoverkiz.models import (
    Action,
    Command,
    Device,
    Event,
    Execution,
    FirmwareStatus,
    Gateway,
    HistoryExecution,
    Option,
    OptionParameter,
    PersistedActionGroup,
    Place,
    ProtocolType,
    ServerConfig,
    Setup,
    State,
    UIProfileDefinition,
)
from pyoverkiz.obfuscate import obfuscate_sensitive_data
from pyoverkiz.response_handler import check_response
from pyoverkiz.serializers import prepare_payload
from pyoverkiz.types import JSON

_LOGGER = logging.getLogger(__name__)


def _get_client_from_invocation(invocation: Details) -> OverkizClient:
    """Return the `OverkizClient` instance from a backoff invocation."""
    return cast(OverkizClient, invocation["args"][0])


async def relogin(invocation: Details) -> None:
    """Re-authenticate using the main `OverkizClient` instance."""
    await _get_client_from_invocation(invocation).login()


async def refresh_listener(invocation: Details) -> None:
    """Refresh the listener using the main `OverkizClient` instance."""
    await _get_client_from_invocation(invocation).register_event_listener()


# Reusable backoff decorators with max_tries and max_time to cap total retry duration.
retry_on_auth_error = backoff.on_exception(
    backoff.expo,
    (NotAuthenticatedError, ServerDisconnectedError),
    max_tries=2,
    max_time=60,  # safety net for hung requests
    jitter=backoff.full_jitter,
    on_backoff=relogin,
    logger=_LOGGER,
)

retry_on_connection_failure = backoff.on_exception(
    backoff.expo,
    (TimeoutError, ClientConnectorError),
    max_tries=5,
    max_time=120,
    jitter=backoff.full_jitter,
    logger=_LOGGER,
)

retry_on_concurrent_requests = backoff.on_exception(
    backoff.expo,
    TooManyConcurrentRequestsError,
    max_tries=5,
    max_time=120,
    jitter=backoff.full_jitter,
    logger=_LOGGER,
)

retry_on_too_many_executions = backoff.on_exception(
    backoff.expo,
    TooManyExecutionsError,
    max_tries=5,
    max_time=300,
    jitter=backoff.full_jitter,
    logger=_LOGGER,
)

retry_on_listener_error = backoff.on_exception(
    backoff.expo,
    (InvalidEventListenerIdError, NoRegisteredEventListenerError),
    max_tries=2,
    max_time=30,
    jitter=backoff.full_jitter,
    on_backoff=refresh_listener,
    logger=_LOGGER,
)

retry_on_execution_queue_full = backoff.on_exception(
    backoff.expo,
    ExecutionQueueFullError,
    max_tries=5,
    max_time=120,
    jitter=backoff.full_jitter,
    logger=_LOGGER,
)

# pylint: disable=too-many-instance-attributes, too-many-branches


def _create_local_ssl_context() -> ssl.SSLContext:
    """Create SSL context.

    This method is not async-friendly and should be called from a thread
    because it will load certificates from disk and do other blocking I/O.
    """
    context = ssl.create_default_context(
        cafile=str(Path(__file__).resolve().parent / "overkiz-root-ca-2048.crt")
    )

    # Disable strict validation introduced in Python 3.13, which doesn't work with
    # Overkiz self-signed gateway certificates. Applied once to the shared context.
    context.verify_flags &= ~ssl.VERIFY_X509_STRICT

    return context


# The default SSLContext objects are created at import time
# since they do blocking I/O to load certificates from disk,
# and imports should always be done before the event loop starts or in a thread.
SSL_CONTEXT_LOCAL_API = _create_local_ssl_context()


@dataclass(frozen=True, slots=True)
class OverkizClientSettings:
    """Behavioral configuration for OverkizClient.

    All fields are optional and default to passive behavior.
    """

    action_queue: ActionQueueSettings | None = None
    rts_command_duration: int | None = None


class OverkizClient:
    """Interface class for the Overkiz API."""

    server_config: ServerConfig
    setup: Setup | None
    devices: list[Device]
    gateways: list[Gateway]
    event_listener_id: str | None
    session: ClientSession
    _ssl: ssl.SSLContext | bool = True
    _auth: AuthStrategy
    _action_queue: ActionQueue | None = None
    settings: OverkizClientSettings

    def __init__(
        self,
        *,
        server: ServerConfig | Server | str,
        credentials: Credentials,
        verify_ssl: bool = True,
        session: ClientSession | None = None,
        settings: OverkizClientSettings | None = None,
    ) -> None:
        """Constructor.

        :param server: ServerConfig
        :param credentials: Credentials for authentication
        :param verify_ssl: Enable SSL certificate verification
        :param session: optional ClientSession
        :param settings: behavioral settings for the client (default None)
        """
        self.server_config = self._normalize_server(server)

        self.setup: Setup | None = None
        self.devices: list[Device] = []
        self.gateways: list[Gateway] = []
        self.event_listener_id: str | None = None

        self.session = session or ClientSession(headers={"User-Agent": USER_AGENT})
        self._ssl = verify_ssl

        if self.server_config.api_type == APIType.LOCAL and verify_ssl:
            # Use the prebuilt SSL context with disabled strict validation for local API.
            self._ssl = SSL_CONTEXT_LOCAL_API

        self.settings = settings or OverkizClientSettings()

        if self.settings.action_queue:
            self.settings.action_queue.validate()
            self._action_queue = ActionQueue(
                executor=self._execute_action_group_direct,
                settings=self.settings.action_queue,
            )

        self._auth = build_auth_strategy(
            server_config=self.server_config,
            credentials=credentials,
            session=self.session,
            ssl_context=self._ssl,
        )

    async def __aenter__(self) -> Self:
        """Enter async context manager and return the client instance."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Exit the async context manager and close the client session."""
        await self.close()

    @staticmethod
    def _normalize_server(server: ServerConfig | Server | str) -> ServerConfig:
        """Resolve user-provided server identifiers into a `ServerConfig`."""
        if isinstance(server, ServerConfig):
            return server

        server_key = server.value if isinstance(server, Server) else str(server)

        try:
            return SUPPORTED_SERVERS[server_key]
        except KeyError as error:
            raise OverkizError(
                f"Unknown server '{server_key}'. Provide a supported server key or ServerConfig instance."
            ) from error

    async def close(self) -> None:
        """Close the session."""
        # Flush any pending actions in queue
        if self._action_queue:
            await self._action_queue.shutdown()

        if self.event_listener_id:
            await self.unregister_event_listener()

        await self._auth.close()
        await self.session.close()

    async def login(
        self,
        register_event_listener: bool = True,
    ) -> bool:
        """Authenticate and create an API session allowing access to the other operations.

        Caller must provide one of [userId+userPassword, userId+ssoToken, accessToken, jwt].
        """
        await self._auth.login()

        if self.server_config.api_type == APIType.LOCAL:
            if register_event_listener:
                await self.register_event_listener()
            else:
                # Validate local API token by calling a simple endpoint
                await self.get_gateways()

            return True

        if register_event_listener:
            await self.register_event_listener()

        return True

    @retry_on_auth_error
    async def get_setup(self, refresh: bool = False) -> Setup:
        """Get all data about the connected user setup.

            -> gateways data (serial number, activation state, ...): <gateways/gateway>
            -> setup location: <location>
            -> house places (rooms and floors): <place>
            -> setup devices: <devices>.

        A gateway may be in different modes (mode) regarding to the activated functions (functions).
        A house may be composed of several floors and rooms. The house, floors and rooms are viewed as a place.
        Devices in the house are grouped by type called uiClass. Each device has an associated widget.
        The widget is used to control or to know the device state, whatever the device protocol (controllable): IO, RTS, X10, ... .
        A device can be either an actuator (type=1) or a sensor (type=2).
        Data of one or several devices can be also get by setting the device(s) url as request parameter.

        Per-session rate-limit : 1 calls per 1d period for this particular operation (bulk-load)
        """
        if self.setup and not refresh:
            return self.setup

        response = await self._get("setup")

        setup = converter.structure(decamelize(response), Setup)

        # Cache response
        self.setup = setup
        self.gateways = setup.gateways
        self.devices = setup.devices

        return setup

    @retry_on_auth_error
    async def get_diagnostic_data(
        self, mask_sensitive_data: bool = True
    ) -> dict[str, Any]:
        """Get diagnostic data for the connected user setup.

            -> gateways data (serial number, activation state, ...): <gateways/gateway>
            -> setup location: <location>
            -> house places (rooms and floors): <place>
            -> setup devices: <devices>
            -> action groups: <actionGroups>

        By default, this data is masked to not return confidential or PII data.
        Set `mask_sensitive_data` to `False` to return the raw payloads.
        """
        setup, action_groups = await asyncio.gather(
            self._get("setup"),
            self._get("actionGroups"),
        )

        if mask_sensitive_data:
            setup = obfuscate_sensitive_data(setup)
            action_groups = obfuscate_sensitive_data(action_groups)

        return {
            "setup": setup,
            "action_groups": action_groups,
        }

    @retry_on_auth_error
    async def get_devices(self, refresh: bool = False) -> list[Device]:
        """List devices.

        Per-session rate-limit : 1 calls per 1d period for this particular operation (bulk-load).
        """
        if self.devices and not refresh:
            return self.devices

        response = await self._get("setup/devices")
        devices = converter.structure(decamelize(response), list[Device])

        # Cache response
        self.devices = devices
        if self.setup:
            self.setup.devices = devices

        return devices

    @retry_on_auth_error
    async def get_gateways(self, refresh: bool = False) -> list[Gateway]:
        """Get every gateways of a connected user setup.

        Per-session rate-limit : 1 calls per 1d period for this particular operation (bulk-load).
        """
        if self.gateways and not refresh:
            return self.gateways

        response = await self._get("setup/gateways")
        gateways = converter.structure(decamelize(response), list[Gateway])

        # Cache response
        self.gateways = gateways
        if self.setup:
            self.setup.gateways = gateways

        return gateways

    @retry_on_auth_error
    async def get_execution_history(self) -> list[HistoryExecution]:
        """List past executions and their outcomes."""
        response = await self._get("history/executions")
        return converter.structure(decamelize(response), list[HistoryExecution])

    @retry_on_auth_error
    async def get_device_definition(self, deviceurl: str) -> JSON | None:
        """Retrieve a particular setup device definition."""
        response: dict = await self._get(
            f"setup/devices/{urllib.parse.quote_plus(deviceurl)}"
        )

        return response.get("definition")

    @retry_on_auth_error
    async def get_state(self, deviceurl: str) -> list[State]:
        """Retrieve states of requested device."""
        response = await self._get(
            f"setup/devices/{urllib.parse.quote_plus(deviceurl)}/states"
        )
        return converter.structure(decamelize(response), list[State])

    @retry_on_auth_error
    async def refresh_states(self) -> None:
        """Ask the box to refresh all devices states for protocols supporting that operation."""
        await self._post("setup/devices/states/refresh")

    @retry_on_auth_error
    async def refresh_device_states(self, deviceurl: str) -> None:
        """Ask the box to refresh all states of the given device for protocols supporting that operation."""
        await self._post(
            f"setup/devices/{urllib.parse.quote_plus(deviceurl)}/states/refresh"
        )

    @retry_on_concurrent_requests
    async def register_event_listener(self) -> str:
        """Register a new setup event listener on the current session and return a new.

        listener id.
        Only one listener may be registered on a given session.
        Registering an new listener will invalidate the previous one if any.
        Note that registering an event listener drastically reduces the session
        timeout : listening sessions are expected to call the /events/{listenerId}/fetch
        API on a regular basis.
        """
        response = await self._post("events/register")
        listener_id = cast(str, response.get("id"))
        self.event_listener_id = listener_id

        return listener_id

    @retry_on_concurrent_requests
    @retry_on_auth_error
    @retry_on_listener_error
    @retry_on_connection_failure
    async def fetch_events(self) -> list[Event]:
        """Fetch new events from a registered event listener. Fetched events are removed.

        from the listener buffer. Return an empty response if no event is available.
        Per-session rate-limit : 1 calls per 1 SECONDS period for this particular
        operation (polling).
        """
        response = await self._post(f"events/{self.event_listener_id}/fetch")
        return converter.structure(decamelize(response), list[Event])

    async def unregister_event_listener(self) -> None:
        """Unregister an event listener.

        API response status is always 200, even on unknown listener ids.
        """
        await self._post(f"events/{self.event_listener_id}/unregister")
        self.event_listener_id = None

    @retry_on_auth_error
    async def get_current_execution(self, exec_id: str) -> Execution | None:
        """Get a currently running execution by its exec_id.

        Returns None if the execution does not exist.
        """
        response = await self._get(f"exec/current/{exec_id}")
        if not response or not isinstance(response, dict):
            return None

        return converter.structure(decamelize(response), Execution)

    @retry_on_auth_error
    async def get_current_executions(self) -> list[Execution]:
        """Get all currently running executions."""
        response = await self._get("exec/current")
        return converter.structure(decamelize(response), list[Execution])

    @retry_on_auth_error
    async def get_api_version(self) -> str:
        """Get the API version (local only)."""
        response = await self._get("apiVersion")

        return cast(str, response["protocolVersion"])

    def _apply_rts_duration(self, actions: list[Action]) -> list[Action]:
        """Set the execution duration for RTS commands that support it.

        The default execution duration for RTS devices is 30 seconds, which
        blocks consecutive commands. This injects the configured duration
        (typically 0) into commands that accept it, based on the device
        command definition (nparams).
        """
        duration = self.settings.rts_command_duration
        if duration is None:
            return actions

        device_index: dict[str, Device] = {d.device_url: d for d in self.devices}

        result: list[Action] = []
        for action in actions:
            device = device_index.get(action.device_url)

            if device is None or device.identifier.protocol != Protocol.RTS:
                result.append(action)
                continue

            updated_commands: list[Command] = []
            for cmd in action.commands:
                cmd_def = device.get_command_definition(str(cmd.name))
                current_count = len(cmd.parameters) if cmd.parameters else 0

                if cmd_def and current_count < cmd_def.nparams:
                    updated_commands.append(
                        Command(
                            name=cmd.name,
                            parameters=[*(cmd.parameters or []), duration],
                            type=cmd.type,
                        )
                    )
                else:
                    updated_commands.append(cmd)

            result.append(
                Action(device_url=action.device_url, commands=updated_commands)
            )

        return result

    @retry_on_too_many_executions
    @retry_on_auth_error
    async def _execute_action_group_direct(
        self,
        actions: list[Action],
        mode: ExecutionMode | None = None,
        label: str | None = "python-overkiz-api",
    ) -> str:
        """Execute a non-persistent action group directly (internal method).

        The executed action group does not have to be persisted on the server before use.
        Per-session rate-limit : 1 calls per 28min 48s period for all operations of the same category (exec)
        """
        payload = {"label": label, "actions": [a.to_payload() for a in actions]}
        url = f"exec/apply/{mode.value}" if mode else "exec/apply"

        response: dict = await self._post(url, prepare_payload(payload))

        return cast(str, response["execId"])

    async def execute_action_group(
        self,
        actions: list[Action],
        mode: ExecutionMode | None = None,
        label: str | None = "python-overkiz-api",
    ) -> str:
        """Execute an ad-hoc action group built from the given actions.

        An action group is a batch of device actions submitted as a single
        execution. Each ``Action`` targets one device and contains one or more
        ``Command`` instances (e.g. ``open``, ``setClosure(50)``). The gateway
        allows at most one action per device per action group.

        When the action queue is enabled, actions are held for a short delay
        and merged with other actions submitted in the same window. Commands
        targeting the same device are combined into a single action. The method
        blocks until the batch executes and returns the resulting exec_id.

        When the action queue is disabled, the action group is sent immediately.

        Args:
            actions: One or more actions to execute. Each action targets a
                single device and holds one or more commands.
            mode: Optional execution mode (``HIGH_PRIORITY``, ``GEOLOCATED``,
                or ``INTERNAL``).
            label: Human-readable label for the execution.

        Returns:
            The ``exec_id`` identifying the execution on the server.
        """
        actions = self._apply_rts_duration(actions)

        if self._action_queue:
            queued = await self._action_queue.add(actions, mode, label)
            return await queued
        return await self._execute_action_group_direct(actions, mode, label)

    async def flush_action_queue(self) -> None:
        """Force flush all pending actions in the queue immediately.

        If action queue is disabled, this method does nothing.
        If there are no pending actions, this method does nothing.
        """
        if self._action_queue:
            await self._action_queue.flush()

    def get_pending_actions_count(self) -> int:
        """Get the approximate number of actions currently waiting in the queue.

        Returns 0 if action queue is disabled. This is a best-effort snapshot
        and may be stale if other coroutines modify the queue concurrently.
        """
        if self._action_queue:
            return self._action_queue.get_pending_count()
        return 0

    @retry_on_auth_error
    async def cancel_execution(self, exec_id: str) -> None:
        """Cancel a running execution by its exec_id."""
        await self._delete(f"exec/current/setup/{exec_id}")

    @retry_on_auth_error
    async def get_action_groups(self) -> list[PersistedActionGroup]:
        """List action groups persisted on the server."""
        response = await self._get("actionGroups")
        return converter.structure(decamelize(response), list[PersistedActionGroup])

    @retry_on_auth_error
    async def get_places(self) -> Place:
        """Get the hierarchical structure of places (house, rooms, areas, zones).

        The Place model represents a hierarchical organization where the root place is
        typically the house/property, and `sub_places` contains nested child places
        (floors, rooms, areas). This structure can be recursively navigated to build
        a complete map of all locations in the setup. Each place has:
        - `label`: Human-readable name for the place
        - `type`: Numeric identifier for the place type
        - `sub_places`: List of nested places within this location
        """
        response = await self._get("setup/places")
        return converter.structure(decamelize(response), Place)

    @retry_on_auth_error
    async def execute_persisted_action_group(self, oid: str) -> str:
        """Execute a server-side action group by its OID (see ``get_action_groups``)."""
        response = await self._post(f"exec/{oid}")
        return cast(str, response["execId"])

    @retry_on_auth_error
    async def schedule_persisted_action_group(self, oid: str, timestamp: int) -> str:
        """Schedule a server-side action group for execution at the given timestamp."""
        response = await self._post(f"exec/schedule/{oid}/{timestamp}")
        return cast(str, response["triggerId"])

    @retry_on_auth_error
    async def get_setup_options(self) -> list[Option]:
        """This operation returns all subscribed options of a given setup.

        Per-session rate-limit : 1 calls per 1d period for this particular operation (bulk-load)
        Access scope : Full enduser API access (enduser/*).
        """
        response = await self._get("setup/options")
        return converter.structure(decamelize(response), list[Option])

    @retry_on_auth_error
    async def get_setup_option(self, option: str) -> Option | None:
        """This operation returns the selected subscribed option of a given setup.

        For example `developerMode-{gateway_id}` to understand if developer mode is on.
        """
        response = await self._get(f"setup/options/{option}")

        if response:
            return converter.structure(decamelize(response), Option)

        return None

    @retry_on_auth_error
    async def get_setup_option_parameter(
        self, option: str, parameter: str
    ) -> OptionParameter | None:
        """This operation returns the selected parameters of a given setup and option.

        For example `developerMode-{gateway_id}` and `gatewayId` to understand if developer mode is on.

        If the option is not available, an OverkizError will be thrown.
        If the parameter is not available you will receive None.
        """
        response = await self._get(f"setup/options/{option}/{parameter}")

        if response:
            return converter.structure(decamelize(response), OptionParameter)

        return None

    @retry_on_auth_error
    async def get_reference_controllable(self, controllable_name: str) -> JSON:
        """Get a controllable definition."""
        return await self._get(
            f"reference/controllable/{urllib.parse.quote_plus(controllable_name)}"
        )

    @retry_on_auth_error
    async def get_reference_controllable_types(self) -> JSON:
        """Get details about all supported controllable types."""
        return await self._get("reference/controllableTypes")

    @retry_on_auth_error
    async def search_reference_devices_model(self, payload: JSON) -> JSON:
        """Search reference device models using a POST payload."""
        return await self._post("reference/devices/search", payload)

    @retry_on_auth_error
    async def get_reference_protocol_types(self) -> list[ProtocolType]:
        """Get details about supported protocol types on that server instance.

        Returns a list of protocol type definitions, each containing:
        - id: Numeric protocol identifier
        - prefix: URL prefix used in device addresses
        - name: Internal protocol name
        - label: Human-readable protocol label
        """
        response = await self._get("reference/protocolTypes")
        # No decamelize — ProtocolType fields are all single-word lowercase already.
        return converter.structure(response, list[ProtocolType])

    @retry_on_auth_error
    async def get_reference_timezones(self) -> JSON:
        """Get timezones list."""
        return await self._get("reference/timezones")

    @retry_on_auth_error
    async def get_reference_ui_classes(self) -> list[str]:
        """Get a list of all defined UI classes."""
        return await self._get("reference/ui/classes")

    @retry_on_auth_error
    async def get_reference_ui_classifiers(self) -> list[str]:
        """Get a list of all defined UI classifiers."""
        return await self._get("reference/ui/classifiers")

    @retry_on_auth_error
    async def get_reference_ui_profile(self, profile_name: str) -> UIProfileDefinition:
        """Get a description of a given UI profile (or form-factor variant).

        Returns a profile definition containing:
        - name: Profile name
        - commands: Available commands with parameters and descriptions
        - states: Available states with value types and descriptions
        - form_factor: Whether profile is tied to a specific physical device type
        """
        response = await self._get(
            f"reference/ui/profile/{urllib.parse.quote_plus(profile_name)}"
        )
        return converter.structure(decamelize(response), UIProfileDefinition)

    @retry_on_auth_error
    async def get_reference_ui_profile_names(self) -> list[str]:
        """Get a list of all defined UI profiles (and form-factor variants)."""
        return await self._get("reference/ui/profileNames")

    @retry_on_auth_error
    async def get_reference_ui_widgets(self) -> list[str]:
        """Get a list of all defined UI widgets."""
        return await self._get("reference/ui/widgets")

    @retry_on_auth_error
    async def get_devices_not_up_to_date(self) -> list[Device]:
        """Get all devices whose firmware is not up to date."""
        response = await self._get("setup/devices/notUpToDate")
        return converter.structure(decamelize(response), list[Device])

    @retry_on_auth_error
    async def get_device_firmware_status(self, deviceurl: str) -> FirmwareStatus | None:
        """Check if a device's firmware is up to date.

        Returns None if the device does not support firmware status checks.
        """
        try:
            response = await self._get(
                f"setup/devices/{urllib.parse.quote_plus(deviceurl)}/firmwareUpToDate"
            )
        except UnsupportedOperationError:
            return None
        return converter.structure(decamelize(response), FirmwareStatus)

    @retry_on_auth_error
    async def get_device_firmware_update_capability(self, deviceurl: str) -> bool:
        """Check if a device supports firmware updates.

        Returns False if the device does not support this query.
        """
        try:
            response = await self._get(
                f"setup/devices/{urllib.parse.quote_plus(deviceurl)}/firmwareUpdateCapability"
            )
        except UnsupportedOperationError:
            return False
        return cast(bool, response["supportsFirmwareUpdate"])

    @retry_on_auth_error
    async def update_device_firmware(self, deviceurl: str) -> None:
        """Update a device's firmware to the next available version."""
        await self._put(
            f"setup/devices/{urllib.parse.quote_plus(deviceurl)}/updateFirmware"
        )

    @retry_on_auth_error
    async def update_all_device_firmwares(self) -> None:
        """Update firmware for all devices that are not up to date."""
        await self._put("setup/devices/updateFirmwares")

    async def _get(self, path: str) -> Any:
        """Make a GET request to the OverKiz API."""
        await self._refresh_token_if_expired()

        async with self.session.get(
            f"{self.server_config.endpoint}{path}",
            headers=self._auth.auth_headers(path),
            ssl=self._ssl,
        ) as response:
            return await self._parse_response(response)

    async def _post(
        self, path: str, payload: JSON | None = None, data: JSON | None = None
    ) -> Any:
        """Make a POST request to the OverKiz API."""
        await self._refresh_token_if_expired()

        async with self.session.post(
            f"{self.server_config.endpoint}{path}",
            data=data,
            json=payload,
            headers=self._auth.auth_headers(path),
            ssl=self._ssl,
        ) as response:
            return await self._parse_response(response)

    async def _put(self, path: str, payload: JSON | None = None) -> Any:
        """Make a PUT request to the OverKiz API."""
        await self._refresh_token_if_expired()

        async with self.session.put(
            f"{self.server_config.endpoint}{path}",
            json=payload,
            headers=self._auth.auth_headers(path),
            ssl=self._ssl,
        ) as response:
            return await self._parse_response(response)

    async def _delete(self, path: str) -> None:
        """Make a DELETE request to the OverKiz API."""
        await self._refresh_token_if_expired()

        async with self.session.delete(
            f"{self.server_config.endpoint}{path}",
            headers=self._auth.auth_headers(path),
            ssl=self._ssl,
        ) as response:
            await check_response(response)

    @staticmethod
    async def _parse_response(response: ClientResponse) -> Any:
        """Check response status and parse JSON body (returns None for 204)."""
        await check_response(response)
        if response.status == HTTPStatus.NO_CONTENT:
            return None
        return await response.json()

    async def _refresh_token_if_expired(self) -> None:
        """Check if token is expired and request a new one."""
        refreshed = await self._auth.refresh_if_needed()

        if refreshed and self.event_listener_id:
            await self.register_event_listener()
