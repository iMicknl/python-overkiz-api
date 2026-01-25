"""Python wrapper for the OverKiz API."""

from __future__ import annotations

import os
import ssl
import urllib.parse
from collections.abc import Mapping
from json import JSONDecodeError
from types import TracebackType
from typing import Any, cast

import backoff
import humps
from aiohttp import (
    ClientConnectorError,
    ClientResponse,
    ClientSession,
    ServerDisconnectedError,
)

from pyoverkiz.action_queue import ActionQueue, ActionQueueSettings
from pyoverkiz.auth import AuthStrategy, Credentials, build_auth_strategy
from pyoverkiz.const import SUPPORTED_SERVERS
from pyoverkiz.enums import APIType, CommandMode, Server
from pyoverkiz.exceptions import (
    AccessDeniedToGatewayException,
    BadCredentialsException,
    ExecutionQueueFullException,
    InvalidCommandException,
    InvalidEventListenerIdException,
    InvalidTokenException,
    MaintenanceException,
    MissingAPIKeyException,
    MissingAuthorizationTokenException,
    NoRegisteredEventListenerException,
    NoSuchResourceException,
    NotAuthenticatedException,
    NotSuchTokenException,
    OverkizException,
    ServiceUnavailableException,
    SessionAndBearerInSameRequestException,
    TooManyAttemptsBannedException,
    TooManyConcurrentRequestsException,
    TooManyExecutionsException,
    TooManyRequestsException,
    UnknownObjectException,
    UnknownUserException,
)
from pyoverkiz.models import (
    Action,
    ActionGroup,
    Device,
    Event,
    Execution,
    Gateway,
    HistoryExecution,
    Option,
    OptionParameter,
    Place,
    ServerConfig,
    Setup,
    State,
)
from pyoverkiz.obfuscate import obfuscate_sensitive_data
from pyoverkiz.serializers import prepare_payload
from pyoverkiz.types import JSON


async def relogin(invocation: Mapping[str, Any]) -> None:
    """Small helper used by retry decorators to re-authenticate the client."""
    await invocation["args"][0].login()


async def refresh_listener(invocation: Mapping[str, Any]) -> None:
    """Helper to refresh an event listener when retrying listener-related operations."""
    await invocation["args"][0].register_event_listener()


# Reusable backoff decorators to reduce code duplication
retry_on_auth_error = backoff.on_exception(
    backoff.expo,
    (NotAuthenticatedException, ServerDisconnectedError, ClientConnectorError),
    max_tries=2,
    on_backoff=relogin,
)

retry_on_concurrent_requests = backoff.on_exception(
    backoff.expo,
    TooManyConcurrentRequestsException,
    max_tries=5,
)

retry_on_too_many_executions = backoff.on_exception(
    backoff.expo,
    TooManyExecutionsException,
    max_tries=10,
)

retry_on_listener_error = backoff.on_exception(
    backoff.expo,
    (InvalidEventListenerIdException, NoRegisteredEventListenerException),
    max_tries=2,
    on_backoff=refresh_listener,
)


# pylint: disable=too-many-instance-attributes, too-many-branches


def _create_local_ssl_context() -> ssl.SSLContext:
    """Create SSL context.

    This method is not async-friendly and should be called from a thread
    because it will load certificates from disk and do other blocking I/O.
    """
    context = ssl.create_default_context(
        cafile=os.path.dirname(os.path.realpath(__file__)) + "/overkiz-root-ca-2048.crt"
    )

    # Disable strict validation introduced in Python 3.13, which doesn't work with
    # Overkiz self-signed gateway certificates. Applied once to the shared context.
    context.verify_flags &= ~ssl.VERIFY_X509_STRICT

    return context


# The default SSLContext objects are created at import time
# since they do blocking I/O to load certificates from disk,
# and imports should always be done before the event loop starts or in a thread.
SSL_CONTEXT_LOCAL_API = _create_local_ssl_context()


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

    def __init__(
        self,
        *,
        server: ServerConfig | Server | str,
        credentials: Credentials,
        verify_ssl: bool = True,
        session: ClientSession | None = None,
        action_queue: bool | ActionQueueSettings = False,
    ) -> None:
        """Constructor.

        :param server: ServerConfig
        :param credentials: Credentials for authentication
        :param verify_ssl: Enable SSL certificate verification
        :param session: optional ClientSession
        :param action_queue: enable batching or provide queue settings (default False)
        """
        self.server_config = self._normalize_server(server)

        self.setup: Setup | None = None
        self.devices: list[Device] = []
        self.gateways: list[Gateway] = []
        self.event_listener_id: str | None = None

        self.session = (
            session
            if session
            else ClientSession(headers={"User-Agent": "python-overkiz-api"})
        )
        self._ssl = verify_ssl

        if self.server_config.type == APIType.LOCAL and verify_ssl:
            # Use the prebuilt SSL context with disabled strict validation for local API.
            self._ssl = SSL_CONTEXT_LOCAL_API

        # Initialize action queue if enabled
        queue_settings: ActionQueueSettings | None
        if isinstance(action_queue, ActionQueueSettings):
            queue_settings = action_queue
        elif isinstance(action_queue, bool):
            queue_settings = ActionQueueSettings() if action_queue else None
        else:
            raise TypeError(
                "action_queue must be a bool or ActionQueueSettings, "
                f"got {type(action_queue).__name__}"
            )

        if queue_settings:
            queue_settings.validate()
            self._action_queue = ActionQueue(
                executor=self._execute_action_group_direct,
                delay=queue_settings.delay,
                max_actions=queue_settings.max_actions,
            )

        self._auth = build_auth_strategy(
            server_config=self.server_config,
            credentials=credentials,
            session=self.session,
            ssl_context=self._ssl,
        )

    async def __aenter__(self) -> OverkizClient:
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
            raise OverkizException(
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
        register_event_listener: bool | None = True,
    ) -> bool:
        """Authenticate and create an API session allowing access to the other operations.

        Caller must provide one of [userId+userPassword, userId+ssoToken, accessToken, jwt].
        """
        await self._auth.login()

        if self.server_config.type == APIType.LOCAL:
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

        response = await self.__get("setup")

        setup = Setup(**humps.decamelize(response))

        # Cache response
        self.setup = setup
        self.gateways = setup.gateways
        self.devices = setup.devices

        return setup

    @retry_on_auth_error
    async def get_diagnostic_data(self) -> JSON:
        """Get all data about the connected user setup.

            -> gateways data (serial number, activation state, ...): <gateways/gateway>
            -> setup location: <location>
            -> house places (rooms and floors): <place>
            -> setup devices: <devices>.

        This data will be masked to not return any confidential or PII data.
        """
        response = await self.__get("setup")

        return obfuscate_sensitive_data(response)

    @retry_on_auth_error
    async def get_devices(self, refresh: bool = False) -> list[Device]:
        """List devices.

        Per-session rate-limit : 1 calls per 1d period for this particular operation (bulk-load).
        """
        if self.devices and not refresh:
            return self.devices

        response = await self.__get("setup/devices")
        devices = [Device(**d) for d in humps.decamelize(response)]

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

        response = await self.__get("setup/gateways")
        gateways = [Gateway(**g) for g in humps.decamelize(response)]

        # Cache response
        self.gateways = gateways
        if self.setup:
            self.setup.gateways = gateways

        return gateways

    @retry_on_auth_error
    async def get_execution_history(self) -> list[HistoryExecution]:
        """List execution history."""
        response = await self.__get("history/executions")
        execution_history = [HistoryExecution(**h) for h in humps.decamelize(response)]

        return execution_history

    @retry_on_auth_error
    async def get_device_definition(self, deviceurl: str) -> JSON | None:
        """Retrieve a particular setup device definition."""
        response: dict = await self.__get(
            f"setup/devices/{urllib.parse.quote_plus(deviceurl)}"
        )

        return response.get("definition")

    @retry_on_auth_error
    async def get_state(self, deviceurl: str) -> list[State]:
        """Retrieve states of requested device."""
        response = await self.__get(
            f"setup/devices/{urllib.parse.quote_plus(deviceurl)}/states"
        )
        state = [State(**s) for s in humps.decamelize(response)]

        return state

    @retry_on_auth_error
    async def refresh_states(self) -> None:
        """Ask the box to refresh all devices states for protocols supporting that operation."""
        await self.__post("setup/devices/states/refresh")

    @retry_on_auth_error
    async def refresh_device_states(self, deviceurl: str) -> None:
        """Ask the box to refresh all states of the given device for protocols supporting that operation."""
        await self.__post(
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
        response = await self.__post("events/register")
        listener_id = cast(str, response.get("id"))
        self.event_listener_id = listener_id

        return listener_id

    @retry_on_concurrent_requests
    @retry_on_auth_error
    @retry_on_listener_error
    async def fetch_events(self) -> list[Event]:
        """Fetch new events from a registered event listener. Fetched events are removed.

        from the listener buffer. Return an empty response if no event is available.
        Per-session rate-limit : 1 calls per 1 SECONDS period for this particular
        operation (polling).
        """
        await self._refresh_token_if_expired()
        response = await self.__post(f"events/{self.event_listener_id}/fetch")
        events = [Event(**e) for e in humps.decamelize(response)]

        return events

    async def unregister_event_listener(self) -> None:
        """Unregister an event listener.

        API response status is always 200, even on unknown listener ids.
        """
        await self._refresh_token_if_expired()
        await self.__post(f"events/{self.event_listener_id}/unregister")
        self.event_listener_id = None

    @retry_on_auth_error
    async def get_current_execution(self, exec_id: str) -> Execution:
        """Get an action group execution currently running."""
        response = await self.__get(f"exec/current/{exec_id}")
        execution = Execution(**humps.decamelize(response))

        return execution

    @retry_on_auth_error
    async def get_current_executions(self) -> list[Execution]:
        """Get all action groups executions currently running."""
        response = await self.__get("exec/current")
        executions = [Execution(**e) for e in humps.decamelize(response)]

        return executions

    @retry_on_auth_error
    async def get_api_version(self) -> str:
        """Get the API version (local only)."""
        response = await self.__get("apiVersion")

        return cast(str, response["protocolVersion"])

    @retry_on_too_many_executions
    @retry_on_auth_error
    async def _execute_action_group_direct(
        self,
        actions: list[Action],
        mode: CommandMode | None = None,
        label: str | None = "python-overkiz-api",
    ) -> str:
        """Execute a non-persistent action group directly (internal method).

        The executed action group does not have to be persisted on the server before use.
        Per-session rate-limit : 1 calls per 28min 48s period for all operations of the same category (exec)
        """
        # Build a logical (snake_case) payload using model helpers and convert it
        # to the exact JSON schema expected by the API (camelCase + small fixes).
        payload = {"label": label, "actions": [a.to_payload() for a in actions]}

        # Prepare final payload with camelCase keys and special abbreviation handling
        final_payload = prepare_payload(payload)

        if mode == CommandMode.GEOLOCATED:
            url = "exec/apply/geolocated"
        elif mode == CommandMode.INTERNAL:
            url = "exec/apply/internal"
        elif mode == CommandMode.HIGH_PRIORITY:
            url = "exec/apply/highPriority"
        else:
            url = "exec/apply"

        response: dict = await self.__post(url, final_payload)

        return cast(str, response["execId"])

    async def execute_action_group(
        self,
        actions: list[Action],
        mode: CommandMode | None = None,
        label: str | None = "python-overkiz-api",
    ) -> str:
        """Execute a non-persistent action group.

        When action queue is enabled, actions will be batched with other actions
        executed within the configured delay window. The method will wait for the
        batch to execute and return the exec_id.

        When action queue is disabled, executes immediately and returns exec_id.

        The API is consistent regardless of queue configuration - always returns
        exec_id string directly.

        :param actions: List of actions to execute
        :param mode: Command mode (GEOLOCATED, INTERNAL, HIGH_PRIORITY, or None)
        :param label: Label for the action group
        :return: exec_id string from the executed action group

        Example usage::

            # Works the same with or without queue
            exec_id = await client.execute_action_group([action])
        """
        if self._action_queue:
            queued = await self._action_queue.add(actions, mode, label)
            return await queued
        else:
            return await self._execute_action_group_direct(actions, mode, label)

    async def flush_action_queue(self) -> None:
        """Force flush all pending actions in the queue immediately.

        If action queue is disabled, this method does nothing.
        If there are no pending actions, this method does nothing.
        """
        if self._action_queue:
            await self._action_queue.flush()

    def get_pending_actions_count(self) -> int:
        """Get the number of actions currently waiting in the queue.

        Returns 0 if action queue is disabled.
        """
        if self._action_queue:
            return self._action_queue.get_pending_count()
        return 0

    @retry_on_auth_error
    async def cancel_command(self, exec_id: str) -> None:
        """Cancel a running setup-level execution."""
        await self.__delete(f"/exec/current/setup/{exec_id}")

    @retry_on_auth_error
    async def get_action_groups(self) -> list[ActionGroup]:
        """List the action groups (scenarios)."""
        response = await self.__get("actionGroups")
        return [
            ActionGroup(**action_group) for action_group in humps.decamelize(response)
        ]

    @retry_on_auth_error
    async def get_places(self) -> Place:
        """List the places."""
        response = await self.__get("setup/places")
        places = Place(**humps.decamelize(response))
        return places

    @retry_on_auth_error
    async def execute_scenario(self, oid: str) -> str:
        """Execute a scenario."""
        response = await self.__post(f"exec/{oid}")
        return cast(str, response["execId"])

    @retry_on_auth_error
    async def execute_scheduled_scenario(self, oid: str, timestamp: int) -> str:
        """Execute a scheduled scenario."""
        response = await self.__post(f"exec/schedule/{oid}/{timestamp}")
        return cast(str, response["triggerId"])

    @retry_on_auth_error
    async def get_setup_options(self) -> list[Option]:
        """This operation returns all subscribed options of a given setup.

        Per-session rate-limit : 1 calls per 1d period for this particular operation (bulk-load)
        Access scope : Full enduser API access (enduser/*).
        """
        response = await self.__get("setup/options")
        options = [Option(**o) for o in humps.decamelize(response)]

        return options

    @retry_on_auth_error
    async def get_setup_option(self, option: str) -> Option | None:
        """This operation returns the selected subscribed option of a given setup.

        For example `developerMode-{gateway_id}` to understand if developer mode is on.
        """
        response = await self.__get(f"setup/options/{option}")

        if response:
            return Option(**humps.decamelize(response))

        return None

    @retry_on_auth_error
    async def get_setup_option_parameter(
        self, option: str, parameter: str
    ) -> OptionParameter | None:
        """This operation returns the selected parameters of a given setup and option.

        For example `developerMode-{gateway_id}` and `gatewayId` to understand if developer mode is on.

        If the option is not available, an OverkizException will be thrown.
        If the parameter is not available you will receive None.
        """
        response = await self.__get(f"setup/options/{option}/{parameter}")

        if response:
            return OptionParameter(**humps.decamelize(response))

        return None

    async def __get(self, path: str) -> Any:
        """Make a GET request to the OverKiz API."""
        await self._refresh_token_if_expired()
        headers = dict(self._auth.auth_headers(path))

        async with self.session.get(
            f"{self.server_config.endpoint}{path}",
            headers=headers,
            ssl=self._ssl,
        ) as response:
            await self.check_response(response)
            return await response.json()

    async def __post(
        self, path: str, payload: JSON | None = None, data: JSON | None = None
    ) -> Any:
        """Make a POST request to the OverKiz API."""
        await self._refresh_token_if_expired()
        headers = dict(self._auth.auth_headers(path))

        async with self.session.post(
            f"{self.server_config.endpoint}{path}",
            data=data,
            json=payload,
            headers=headers,
            ssl=self._ssl,
        ) as response:
            await self.check_response(response)
            return await response.json()

    async def __delete(self, path: str) -> None:
        """Make a DELETE request to the OverKiz API."""
        await self._refresh_token_if_expired()
        headers = dict(self._auth.auth_headers(path))

        async with self.session.delete(
            f"{self.server_config.endpoint}{path}",
            headers=headers,
            ssl=self._ssl,
        ) as response:
            await self.check_response(response)

    @staticmethod
    async def check_response(response: ClientResponse) -> None:
        """Check the response returned by the OverKiz API."""
        if response.status in [200, 204]:
            return

        try:
            result = await response.json(content_type=None)
        except JSONDecodeError as error:
            result = await response.text()

            if "is down for maintenance" in result:
                raise MaintenanceException("Server is down for maintenance") from error

            if response.status == 503:
                raise ServiceUnavailableException(result) from error

            raise OverkizException(
                f"Unknown error while requesting {response.url}. {response.status} - {result}"
            ) from error

        if result.get("errorCode"):
            # Error messages between cloud and local Overkiz servers can be slightly different
            # To make it easier to have a strict match for these errors, we remove the double quotes and the period at the end.

            # An error message can have an empty (None) message
            message = message.strip('".') if (message := result.get("error")) else ""

            # {"errorCode": "AUTHENTICATION_ERROR",
            # "error": "Too many requests, try again later : login with xxx@xxx.tld"}
            if "Too many requests" in message:
                raise TooManyRequestsException(message)

            # {"errorCode": "AUTHENTICATION_ERROR", "error": "Bad credentials"}
            if message == "Bad credentials":
                raise BadCredentialsException(message)

            # {"errorCode": "RESOURCE_ACCESS_DENIED", "error": "Not authenticated"}
            if message == "Not authenticated":
                raise NotAuthenticatedException(message)

            # {'errorCode': 'AUTHENTICATION_ERROR', 'error': 'An API key is required to access this setup'}
            if message == "An API key is required to access this setup":
                raise MissingAPIKeyException(message)

            # {"error":"Missing authorization token.","errorCode":"RESOURCE_ACCESS_DENIED"}
            if message == "Missing authorization token":
                raise MissingAuthorizationTokenException(message)

            # {"error": "Server busy, please try again later. (Too many executions)"}
            if message == "Server busy, please try again later. (Too many executions)":
                raise TooManyExecutionsException(message)

            # {"error": "UNSUPPORTED_OPERATION", "error": "No such command : ..."}
            if "No such command" in message:
                raise InvalidCommandException(message)

            # {'errorCode': 'UNSPECIFIED_ERROR', 'error': 'Invalid event listener id : ...'}
            if "Invalid event listener id" in message:
                raise InvalidEventListenerIdException(message)

            # {'errorCode': 'UNSPECIFIED_ERROR', 'error': 'No registered event listener'}
            if message == "No registered event listener":
                raise NoRegisteredEventListenerException(message)

            # {'errorCode': 'AUTHENTICATION_ERROR', 'error': 'No such user account : xxxxx'}
            if "No such user account" in message:
                raise UnknownUserException(message)

            # {'errorCode': 'INVALID_API_CALL', 'error': 'No such resource'}
            if message == "No such resource":
                raise NoSuchResourceException(message)

            # {"errorCode": "RESOURCE_ACCESS_DENIED",  "error": "too many concurrent requests"}
            if message == "too many concurrent requests":
                raise TooManyConcurrentRequestsException(message)

            # {'errorCode': 'EXEC_QUEUE_FULL', 'error': 'Execution queue is full on gateway: #xxx-yyyy-zzzz (soft limit: 10)'}
            if "Execution queue is full on gateway" in message:
                raise ExecutionQueueFullException(message)

            if message == "Cannot use JSESSIONID and bearer token in same request":
                raise SessionAndBearerInSameRequestException(message)

            if message == "Too many attempts with an invalid token, temporarily banned":
                raise TooManyAttemptsBannedException(message)

            if "Invalid token : " in message:
                raise InvalidTokenException(message)

            if "Not such token with UUID: " in message:
                raise NotSuchTokenException(message)

            if "Unknown user :" in message:
                raise UnknownUserException(message)

            # {"error":"Unknown object.","errorCode":"UNSPECIFIED_ERROR"}
            if message == "Unknown object":
                raise UnknownObjectException(message)

            # {'errorCode': 'RESOURCE_ACCESS_DENIED', 'error': 'Access denied to gateway #1234-5678-1234 for action ADD_TOKEN'}
            if "Access denied to gateway" in message:
                raise AccessDeniedToGatewayException(message)

        # Undefined Overkiz exception
        raise OverkizException(result)

    async def _refresh_token_if_expired(self) -> None:
        """Check if token is expired and request a new one."""
        refreshed = await self._auth.refresh_if_needed()

        if refreshed and self.event_listener_id:
            await self.register_event_listener()
