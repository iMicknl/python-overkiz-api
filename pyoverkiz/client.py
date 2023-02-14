""" Python wrapper for the OverKiz API """
from __future__ import annotations

import datetime
import urllib.parse
from collections.abc import Mapping
from types import TracebackType
from typing import Any, cast

import backoff
import humps
from aiohttp import ClientSession, ServerDisconnectedError

from pyoverkiz.exceptions import (
    InvalidEventListenerIdException,
    NoRegisteredEventListenerException,
    NotAuthenticatedException,
    TooManyConcurrentRequestsException,
    TooManyExecutionsException,
)
from pyoverkiz.models import (
    Command,
    Device,
    Event,
    Execution,
    Gateway,
    HistoryExecution,
    LocalToken,
    Place,
    Scenario,
    Setup,
    State,
)
from pyoverkiz.obfuscate import obfuscate_sensitive_data
from pyoverkiz.servers.overkiz_server import OverkizServer
from pyoverkiz.types import JSON


async def relogin(invocation: Mapping[str, Any]) -> None:
    await invocation["args"][0].login()


async def refresh_listener(invocation: Mapping[str, Any]) -> None:
    await invocation["args"][0].register_event_listener()


# pylint: disable=too-many-instance-attributes, too-many-branches


class OverkizClient:
    """Interface class for the Overkiz API"""

    username: str
    password: str
    server: OverkizServer
    setup: Setup | None
    devices: list[Device]
    gateways: list[Gateway]
    event_listener_id: str | None
    session: ClientSession

    _refresh_token: str | None = None
    _expires_in: datetime.datetime | None = None
    _access_token: str | None = None

    def __init__(
        self,
        username: str,
        password: str,
        server: OverkizServer,
        token: str | None = None,
        session: ClientSession | None = None,
    ) -> None:
        """
        Constructor

        :param username: the username
        :param password: the password
        :param server: OverkizServer
        :param session: optional ClientSession
        """

        self.username = username
        self.password = password
        self.server = server
        self._access_token = token

        self.setup: Setup | None = None
        self.devices: list[Device] = []
        self.gateways: list[Gateway] = []
        self.event_listener_id: str | None = None

        self.session = session if session else ClientSession()

    async def __aenter__(self) -> OverkizClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the session."""
        if self.event_listener_id:
            await self.unregister_event_listener()

        await self.session.close()

    async def login(
        self,
        register_event_listener: bool | None = True,
    ) -> bool:
        """
        Authenticate and create an API session allowing access to the other operations.
        Caller must provide one of [userId+userPassword, userId+ssoToken, accessToken, jwt]
        """
        if await self.server.login(self.username, self.password):
            if register_event_listener:
                await self.register_event_listener()
        return False

    @backoff.on_exception(
        backoff.expo,
        (NotAuthenticatedException, ServerDisconnectedError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def get_setup(self, refresh: bool = False) -> Setup:
        """
        Get all data about the connected user setup
            -> gateways data (serial number, activation state, ...): <gateways/gateway>
            -> setup location: <location>
            -> house places (rooms and floors): <place>
            -> setup devices: <devices>

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

        response = await self.server.get("setup")

        setup = Setup(**humps.decamelize(response))

        # Cache response
        self.setup = setup
        self.gateways = setup.gateways
        self.devices = setup.devices

        return setup

    @backoff.on_exception(
        backoff.expo,
        (NotAuthenticatedException, ServerDisconnectedError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def get_diagnostic_data(self) -> JSON:
        """
        Get all data about the connected user setup
            -> gateways data (serial number, activation state, ...): <gateways/gateway>
            -> setup location: <location>
            -> house places (rooms and floors): <place>
            -> setup devices: <devices>

        This data will be masked to not return any confidential or PII data.
        """
        response = await self.server.get("setup")

        return obfuscate_sensitive_data(response)

    @backoff.on_exception(
        backoff.expo,
        (NotAuthenticatedException, ServerDisconnectedError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def get_devices(self, refresh: bool = False) -> list[Device]:
        """
        List devices
        Per-session rate-limit : 1 calls per 1d period for this particular operation (bulk-load)
        """
        if self.devices and not refresh:
            return self.devices

        response = await self.server.get("setup/devices")
        devices = [Device(**d) for d in humps.decamelize(response)]

        # Cache response
        self.devices = devices
        if self.setup:
            self.setup.devices = devices

        return devices

    @backoff.on_exception(
        backoff.expo,
        (NotAuthenticatedException, ServerDisconnectedError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def get_gateways(self, refresh: bool = False) -> list[Gateway]:
        """
        Get every gateways of a connected user setup
        Per-session rate-limit : 1 calls per 1d period for this particular operation (bulk-load)
        """
        if self.gateways and not refresh:
            return self.gateways

        response = await self.server.get("setup/gateways")
        gateways = [Gateway(**g) for g in humps.decamelize(response)]

        # Cache response
        self.gateways = gateways
        if self.setup:
            self.setup.gateways = gateways

        return gateways

    @backoff.on_exception(
        backoff.expo,
        (NotAuthenticatedException, ServerDisconnectedError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def get_execution_history(self) -> list[HistoryExecution]:
        """
        List execution history
        """
        response = await self.server.get("history/executions")
        execution_history = [HistoryExecution(**h) for h in humps.decamelize(response)]

        return execution_history

    @backoff.on_exception(
        backoff.expo, NotAuthenticatedException, max_tries=2, on_backoff=relogin
    )
    async def get_device_definition(self, deviceurl: str) -> JSON | None:
        """
        Retrieve a particular setup device definition
        """
        response: dict = await self.server.get(
            f"setup/devices/{urllib.parse.quote_plus(deviceurl)}"
        )

        return response.get("definition")

    @backoff.on_exception(
        backoff.expo, NotAuthenticatedException, max_tries=2, on_backoff=relogin
    )
    async def get_state(self, deviceurl: str) -> list[State]:
        """
        Retrieve states of requested device
        """
        response = await self.server.get(
            f"setup/devices/{urllib.parse.quote_plus(deviceurl)}/states"
        )
        state = [State(**s) for s in humps.decamelize(response)]

        return state

    @backoff.on_exception(
        backoff.expo, NotAuthenticatedException, max_tries=2, on_backoff=relogin
    )
    async def refresh_states(self) -> None:
        """
        Ask the box to refresh all devices states for protocols supporting that operation
        """
        await self.server.post("setup/devices/states/refresh")

    @backoff.on_exception(backoff.expo, TooManyConcurrentRequestsException, max_tries=5)
    async def register_event_listener(self) -> str:
        """
        Register a new setup event listener on the current session and return a new
        listener id.
        Only one listener may be registered on a given session.
        Registering an new listener will invalidate the previous one if any.
        Note that registering an event listener drastically reduces the session
        timeout : listening sessions are expected to call the /events/{listenerId}/fetch
        API on a regular basis.
        """
        response = await self.server.post("events/register")
        listener_id = cast(str, response.get("id"))
        self.event_listener_id = listener_id

        return listener_id

    @backoff.on_exception(backoff.expo, TooManyConcurrentRequestsException, max_tries=5)
    @backoff.on_exception(
        backoff.expo, NotAuthenticatedException, max_tries=2, on_backoff=relogin
    )
    @backoff.on_exception(
        backoff.expo,
        (InvalidEventListenerIdException, NoRegisteredEventListenerException),
        max_tries=2,
        on_backoff=refresh_listener,
    )
    async def fetch_events(self) -> list[Event]:
        """
        Fetch new events from a registered event listener. Fetched events are removed
        from the listener buffer. Return an empty response if no event is available.
        Per-session rate-limit : 1 calls per 1 SECONDS period for this particular
        operation (polling)
        """
        response = await self.server.post(f"events/{self.event_listener_id}/fetch")
        events = [Event(**e) for e in humps.decamelize(response)]

        return events

    async def unregister_event_listener(self) -> None:
        """
        Unregister an event listener.
        API response status is always 200, even on unknown listener ids.
        """
        await self.server.post(f"events/{self.event_listener_id}/unregister")
        self.event_listener_id = None

    @backoff.on_exception(
        backoff.expo, NotAuthenticatedException, max_tries=2, on_backoff=relogin
    )
    async def get_current_execution(self, exec_id: str) -> Execution:
        """Get an action group execution currently running"""
        response = await self.server.get(f"exec/current/{exec_id}")
        execution = Execution(**humps.decamelize(response))

        return execution

    @backoff.on_exception(
        backoff.expo, NotAuthenticatedException, max_tries=2, on_backoff=relogin
    )
    async def get_current_executions(self) -> list[Execution]:
        """Get all action groups executions currently running"""
        response = await self.server.get("exec/current")
        executions = [Execution(**e) for e in humps.decamelize(response)]

        return executions

    @backoff.on_exception(
        backoff.expo, NotAuthenticatedException, max_tries=2, on_backoff=relogin
    )
    async def get_api_version(self) -> str:
        """Get the API version (local only)"""
        response = await self.server.get("apiVersion")

        return cast(str, response["protocolVersion"])

    @backoff.on_exception(backoff.expo, TooManyExecutionsException, max_tries=10)
    @backoff.on_exception(
        backoff.expo, NotAuthenticatedException, max_tries=2, on_backoff=relogin
    )
    async def execute_command(
        self,
        device_url: str,
        command: Command | str,
        label: str | None = "python-overkiz-api",
    ) -> str:
        """Send a command"""
        if isinstance(command, str):
            command = Command(command)

        response: str = await self.execute_commands(device_url, [command], label)

        return response

    @backoff.on_exception(
        backoff.expo,
        (NotAuthenticatedException, ServerDisconnectedError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def cancel_command(self, exec_id: str) -> None:
        """Cancel a running setup-level execution"""
        await self.server.delete(f"/exec/current/setup/{exec_id}")

    @backoff.on_exception(
        backoff.expo, NotAuthenticatedException, max_tries=2, on_backoff=relogin
    )
    async def execute_commands(
        self,
        device_url: str,
        commands: list[Command],
        label: str | None = "python-overkiz-api",
    ) -> str:
        """Send several commands in one call"""
        payload = {
            "label": label,
            "actions": [{"deviceURL": device_url, "commands": commands}],
        }
        response: dict = await self.server.post("exec/apply", payload)
        return cast(str, response["execId"])

    @backoff.on_exception(
        backoff.expo,
        (NotAuthenticatedException, ServerDisconnectedError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def get_scenarios(self) -> list[Scenario]:
        """List the scenarios"""
        response = await self.server.get("actionGroups")
        return [Scenario(**scenario) for scenario in response]

    @backoff.on_exception(
        backoff.expo,
        (NotAuthenticatedException, ServerDisconnectedError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def get_places(self) -> Place:
        """List the places"""
        response = await self.server.get("setup/places")
        places = Place(**humps.decamelize(response))
        return places

    @backoff.on_exception(
        backoff.expo,
        (NotAuthenticatedException, ServerDisconnectedError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def generate_local_token(self, gateway_id: str) -> str:
        """
        Generates a new token
        Access scope : Full enduser API access (enduser/*)
        """
        response = await self.server.get(f"config/{gateway_id}/local/tokens/generate")

        return cast(str, response["token"])

    @backoff.on_exception(
        backoff.expo,
        (NotAuthenticatedException, ServerDisconnectedError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def activate_local_token(
        self, gateway_id: str, token: str, label: str, scope: str = "devmode"
    ) -> str:
        """
        Create a token
        Access scope : Full enduser API access (enduser/*)
        """
        response = await self.server.post(
            f"config/{gateway_id}/local/tokens",
            {"label": label, "token": token, "scope": scope},
        )

        return cast(str, response["requestId"])

    @backoff.on_exception(
        backoff.expo,
        (NotAuthenticatedException, ServerDisconnectedError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def get_local_tokens(
        self, gateway_id: str, scope: str = "devmode"
    ) -> list[LocalToken]:
        """
        Get all gateway tokens with the given scope
        Access scope : Full enduser API access (enduser/*)
        """
        response = await self.server.get(f"config/{gateway_id}/local/tokens/{scope}")
        local_tokens = [LocalToken(**lt) for lt in humps.decamelize(response)]

        return local_tokens

    @backoff.on_exception(
        backoff.expo,
        (NotAuthenticatedException, ServerDisconnectedError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def delete_local_token(self, gateway_id: str, uuid: str) -> bool:
        """
        Delete a token
        Access scope : Full enduser API access (enduser/*)
        """
        await self.server.delete(f"config/{gateway_id}/local/tokens/{uuid}")

        return True

    @backoff.on_exception(
        backoff.expo, NotAuthenticatedException, max_tries=2, on_backoff=relogin
    )
    async def execute_scenario(self, oid: str) -> str:
        """Execute a scenario"""
        response = await self.server.post(f"exec/{oid}")
        return cast(str, response["execId"])

    @backoff.on_exception(
        backoff.expo,
        (NotAuthenticatedException, ServerDisconnectedError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def execute_scheduled_scenario(self, oid: str, timestamp: int) -> str:
        """Execute a scheduled scenario"""
        response = await self.server.post(f"exec/schedule/{oid}/{timestamp}")
        return cast(str, response["triggerId"])
