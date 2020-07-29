""" Python wrapper for the Tahoma API """
from __future__ import annotations

import urllib.parse
from types import TracebackType
from typing import Any, Dict, List, Optional, Type, Union

import aiohttp
import humps
from aiohttp import ClientResponse

from pyhoma.exceptions import BadCredentialsException, TooManyRequestsException
from pyhoma.models import Command, Device, Event, Execution, Scenario, State

JSON = Union[Dict[str, Any], List[Dict[str, Any]]]

API_URL = "https://tahomalink.com/enduser-mobile-web/enduserAPI/"  # /doc for API doc


class TahomaClient:
    """ Interface class for the Tahoma API """

    def __init__(self, username: str, password: str, api_url: str = API_URL) -> None:
        """
        Constructor

        :param username: the username for Tahomalink.com
        :param password: the password for Tahomalink.com
        """

        self.username = username
        self.password = password
        self.api_url = api_url

        self.devices: List[Device] = []
        self.__roles = None
        self.event_listener_id: Optional[str] = None

        self.session = aiohttp.ClientSession()

    async def __aenter__(self) -> TahomaClient:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the session."""
        if self.event_listener_id:
            await self.unregister_event_listener(self.event_listener_id)

        await self.session.close()

    async def login(self) -> bool:
        """
        Authenticate and create an API session allowing access to the other operations.
        Caller must provide one of [userId+userPassword, userId+ssoToken, accessToken, jwt]
        """
        payload = {"userId": self.username, "userPassword": self.password}
        response = await self.__post("login", data=payload)

        if response.get("success"):
            self.__roles = response.get("roles")

            return True

        return False

    async def get_devices(self, refresh: bool = False) -> List[Device]:
        """
        List devices
        """
        if self.devices and not refresh:
            return self.devices

        response = await self.__get("setup/devices")
        devices = [Device(**d) for d in humps.decamelize(response)]
        self.devices = devices

        return devices

    async def get_state(self, deviceurl: str) -> List[State]:
        """
        Retrieve states of requested device
        """
        response = await self.__get(
            f"setup/devices/{urllib.parse.quote_plus(deviceurl)}/states"
        )
        state = [State(**s) for s in humps.decamelize(response)]

        return state

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
        listener_id = response.get("id")
        self.event_listener_id = listener_id

        return listener_id

    async def fetch_event_listener(self, listener_id: str) -> List[Event]:
        """
        Fetch new events from a registered event listener. Fetched events are removed
        from the listener buffer. Return an empty response if no event is available.
        Per-session rate-limit : 1 calls per 1 SECONDS period for this particular
        operation (polling)
        """
        response = await self.__post(f"events/{listener_id}/fetch")
        events = [Event(**e) for e in humps.decamelize(response)]

        return events

    async def unregister_event_listener(self, listener_id: str) -> None:
        """
        Unregister an event listener.
        API response status is always 200, even on unknown listener ids.
        """
        await self.__post(f"events/{listener_id}/unregister")
        self.event_listener_id = None

    async def get_current_execution(self, exec_id: str) -> Execution:
        """ Get an action group execution currently running """
        response = await self.__get(f"exec/current/{exec_id}")
        execution = Execution(**humps.decamelize(response))

        return execution

    async def get_current_executions(self) -> List[Execution]:
        """ Get all action groups executions currently running """
        response = await self.__get("exec/current")
        executions = [Execution(**e) for e in humps.decamelize(response)]

        return executions

    async def execute_command(
        self,
        device_url: str,
        command: Union[Command, str],
        label: Optional[str] = "python-tahoma-api",
    ) -> str:
        """ Send a command """
        if isinstance(command, str):
            command = Command(command)
        return await self.execute_commands(device_url, [command], label)

    async def execute_commands(
        self,
        device_url: str,
        commands: List[Command],
        label: Optional[str] = "python-tahoma-api",
    ) -> str:
        """ Send several commands in one call """
        payload = {
            "label": label,
            "actions": [{"deviceURL": device_url, "commands": commands}],
        }
        response = await self.__post("exec/apply", payload)
        return response["execId"]

    async def get_scenarios(self) -> List[Scenario]:
        """ List the scenarios """
        response = await self.__get("actionGroups")
        return [Scenario(**scenario) for scenario in response]

    async def execute_scenario(self, oid: str) -> str:
        """ Execute a scenario """
        response = await self.__post(f"exec/{oid}")
        return response["execId"]

    async def __get(self, endpoint: str) -> Any:
        """ Make a GET request to the TaHoma API """
        async with self.session.get(f"{self.api_url}{endpoint}") as response:
            await self.check_response(response)
            return await response.json()

    async def __post(
        self, endpoint: str, payload: Optional[JSON] = None, data: Optional[JSON] = None
    ) -> Any:
        """ Make a POST request to the TaHoma API """
        async with self.session.post(
            f"{self.api_url}{endpoint}", data=data, json=payload
        ) as response:
            await self.check_response(response)
            return await response.json()

    @staticmethod
    async def check_response(response: ClientResponse) -> None:
        """ Check the response returned by the TaHoma API"""
        if response.status == 200:
            return
        # 401
        # {'errorCode': 'AUTHENTICATION_ERROR',
        #  'error': 'Too many requests, try again later : login with xxx@xxx.tld'}
        #  'error': 'Bad credentials'}
        #  'error': 'Your setup cannot be accessed through this application'}
        result = await response.json()
        if response.status == 401:
            if result.get("errorCode") == "AUTHENTICATION_ERROR":
                message = result.get("error")

                if "Too many requests" in message:
                    raise TooManyRequestsException(message)

                if "Your setup cannot be accessed through this application" in message:
                    raise Exception(message)

                if "Bad credentials" in message:
                    raise BadCredentialsException(message)

                raise Exception(message)

        if 400 < response.status < 500:
            message = result.get("error")

            raise Exception(message)
