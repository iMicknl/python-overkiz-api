""" Python wrapper for the OverKiz API """
from __future__ import annotations

import urllib.parse
from json import JSONDecodeError
from types import TracebackType
from typing import Any, Dict, List, Union, cast

import backoff
import humps
from aiohttp import ClientResponse, ClientSession, ServerDisconnectedError

from pyoverkiz.clients.atlantic_cozytouch_client import AtlanticCozytouchClient
from pyoverkiz.clients.nexity_client import NexityClient
from pyoverkiz.clients.simple_client import SimpleClient
from pyoverkiz.clients.somfy_client import SomfyEuropeClient
from pyoverkiz.exceptions import (
    BadCredentialsException,
    InvalidCommandException,
    InvalidEventListenerIdException,
    MaintenanceException,
    NoRegisteredEventListenerException,
    NotAuthenticatedException,
    TooManyExecutionsException,
    TooManyRequestsException,
)
from pyoverkiz.models import (
    Command,
    Device,
    Event,
    Execution,
    Gateway,
    HistoryExecution,
    OverkizServer,
    Place,
    Scenario,
    Setup,
    State,
)

JSON = Union[Dict[str, Any], List[Dict[str, Any]]]


async def relogin(invocation: dict[str, Any]) -> None:
    await invocation["args"][0].login()


async def refresh_listener(invocation: dict[str, Any]) -> None:
    await invocation["args"][0].register_event_listener()


# pylint: disable=too-many-instance-attributes


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

    @staticmethod
    def get_client(server: OverkizServer) -> OverkizClient:
        return CLIENTS.get(server, SimpleClient)

    def __init__(
        self,
        username: str,
        password: str,
        session: ClientSession | None = None,
    ) -> None:
        """
        Constructor

        :param username: the username
        :param password: the password
        :param session: optional ClientSession
        """

        self.username = username
        self.password = password

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

        response = await self.__get("setup")
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
    async def get_devices(self, refresh: bool = False) -> list[Device]:
        """
        List devices
        Per-session rate-limit : 1 calls per 1d period for this particular operation (bulk-load)
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

        response = await self.__get("setup/gateways")
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
        response = await self.__get("history/executions")
        execution_history = [HistoryExecution(**h) for h in humps.decamelize(response)]

        return execution_history

    @backoff.on_exception(
        backoff.expo, NotAuthenticatedException, max_tries=2, on_backoff=relogin
    )
    async def get_device_definition(self, deviceurl: str) -> JSON | None:
        """
        Retrieve a particular setup device definition
        """
        response: dict = await self.__get(
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
        response = await self.__get(
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
        await self.__post("setup/devices/states/refresh")

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
        response = await self.__post("events/register")
        listener_id = cast(str, response.get("id"))
        self.event_listener_id = listener_id

        return listener_id

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
        response = await self.__post(f"events/{self.event_listener_id}/fetch")
        events = [Event(**e) for e in humps.decamelize(response)]

        return events

    async def unregister_event_listener(self) -> None:
        """
        Unregister an event listener.
        API response status is always 200, even on unknown listener ids.
        """
        await self.__post(f"events/{self.event_listener_id}/unregister")
        self.event_listener_id = None

    @backoff.on_exception(
        backoff.expo, NotAuthenticatedException, max_tries=2, on_backoff=relogin
    )
    async def get_current_execution(self, exec_id: str) -> Execution:
        """Get an action group execution currently running"""
        response = await self.__get(f"exec/current/{exec_id}")
        execution = Execution(**humps.decamelize(response))

        return execution

    @backoff.on_exception(
        backoff.expo, NotAuthenticatedException, max_tries=2, on_backoff=relogin
    )
    async def get_current_executions(self) -> list[Execution]:
        """Get all action groups executions currently running"""
        response = await self.__get("exec/current")
        executions = [Execution(**e) for e in humps.decamelize(response)]

        return executions

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
        backoff.expo, NotAuthenticatedException, max_tries=2, on_backoff=relogin
    )
    async def cancel_command(self, exec_id: str) -> None:
        """Cancel a running setup-level execution"""
        await self.__delete(f"/exec/current/setup/{exec_id}")

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
        response: dict = await self.__post("exec/apply", payload)
        return cast(str, response["execId"])

    @backoff.on_exception(
        backoff.expo,
        (NotAuthenticatedException, ServerDisconnectedError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def get_scenarios(self) -> list[Scenario]:
        """List the scenarios"""
        response = await self.__get("actionGroups")
        return [Scenario(**scenario) for scenario in response]

    @backoff.on_exception(
        backoff.expo,
        (NotAuthenticatedException, ServerDisconnectedError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def get_places(self) -> Place:
        """List the places"""
        response = await self.__get("setup/places")
        places = Place(**humps.decamelize(response))
        return places

    @backoff.on_exception(
        backoff.expo, NotAuthenticatedException, max_tries=2, on_backoff=relogin
    )
    async def execute_scenario(self, oid: str) -> str:
        """Execute a scenario"""
        response = await self.__post(f"exec/{oid}")
        return cast(str, response["execId"])

    async def __get(self, path: str) -> Any:
        """Make a GET request to the OverKiz API"""
        async with self.session.get(f"{self.server.endpoint}{path}") as response:
            await self.check_response(response)
            return await response.json()

    async def __post(
        self, path: str, payload: JSON | None = None, data: JSON | None = None
    ) -> Any:
        """Make a POST request to the OverKiz API"""
        async with self.session.post(
            f"{self.server.endpoint}{path}",
            data=data,
            json=payload,
        ) as response:
            await self.check_response(response)
            return await response.json()

    async def __delete(self, path: str) -> None:
        """Make a DELETE request to the OverKiz API"""
        async with self.session.delete(f"{self.server.endpoint}{path}") as response:
            await self.check_response(response)

    @staticmethod
    async def check_response(response: ClientResponse) -> None:
        """Check the response returned by the OverKiz API"""
        if response.status in [200, 204]:
            return

        try:
            result = await response.json(content_type=None)
        except JSONDecodeError as error:
            result = await response.text()
            if "Server is down for maintenance" in result:
                raise MaintenanceException("Server is down for maintenance") from error
            raise Exception(
                f"Unknown error while requesting {response.url}. {response.status} - {result}"
            ) from error

        if result.get("errorCode"):
            message = result.get("error")

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

        raise Exception(message if message else result)
