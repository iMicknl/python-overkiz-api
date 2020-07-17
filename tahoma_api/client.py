""" Python wrapper for the Tahoma API """
import urllib.parse
from typing import Any, List, Optional

import aiohttp
import humps

from tahoma_api.exceptions import BadCredentialsException, TooManyRequestsException
from tahoma_api.models import Command, CommandMode, Device, State

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

        self.session = aiohttp.ClientSession()

    async def close(self) -> None:
        """Close the session."""
        return await self.session.close()

    async def login(self) -> bool:
        """
        Authenticate and create an API session allowing access to the other operations.
        Caller must provide one of [userId+userPassword, userId+ssoToken, accessToken, jwt]
        """
        payload = {"userId": self.username, "userPassword": self.password}
        response = await self.__do_http_request("POST", "login", payload)

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

        response = await self.__do_http_request("GET", "setup/devices")

        devices = [Device(**d) for d in response]
        self.devices = devices

        return devices

    async def get_state(self, deviceurl: str) -> List[State]:
        """
        Retrieve states of requested device
        """
        response = await self.__do_http_request(
            "GET", f"setup/devices/{urllib.parse.quote_plus(deviceurl)}/states"
        )
        state = [State(**s) for s in response]

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
        response = await self.__do_http_request("POST", "events/register")
        listener_id = response.get("id")

        return listener_id

    async def fetch_event_listener(self, listener_id: str) -> List[Any]:
        """
        Fetch new events from a registered event listener. Fetched events are removed
        from the listener buffer. Return an empty response if no event is available.
        Per-session rate-limit : 1 calls per 1 SECONDS period for this particular
        operation (polling)
        """
        response = await self.__do_http_request("POST", f"events/{listener_id}/fetch")

        return response

    async def execute_action_group(
        self,
        actions: List[Command],
        label: str = "python-tahoma-api",
        mode: Optional[CommandMode] = None,
    ) -> List[Any]:
        """ Execute a non-persistent action group.
        The executed action group does not have to be persisted on the server before
        use.
        Per-session rate-limit : 50 calls per 24 HOURS period for all operations of the
        same category (exec)
        """
        payload = {"label": label, "actions": actions}
        supported_modes = ["geolocated", "highPriority", "internal"]
        endpoint = "exec/apply"

        # TODO Change mode / supported_modes to ENUM
        if mode in supported_modes:
            endpoint = f"{endpoint}/{mode}"

        response = await self.__do_http_request("POST", endpoint, payload)

        return response

    async def get_current_execution(self, exec_id: str) -> List[Any]:
        """ Get an action group execution currently running """
        response = await self.__do_http_request("GET", f"/exec/current/{exec_id}")
        # TODO Strongly type executions

        return response

    async def get_current_executions(self) -> List[Any]:
        """ Get all action groups executions currently running """
        response = await self.__do_http_request("GET", "/exec/current")
        # TODO Strongly type executions

        return response

    async def __do_http_request(
        self, method: str, endpoint: str, payload: Optional[Any] = None
    ) -> Any:
        """Make a request to the TaHoma API"""
        supported_methods = ["GET", "POST"]
        result = response = None

        if method not in supported_methods:
            raise Exception

        if method == "GET":
            async with self.session.get(f"{self.api_url}{endpoint}") as response:
                result = await response.json()

        if method == "POST":
            async with self.session.post(
                f"{self.api_url}{endpoint}", data=payload
            ) as response:
                result = await response.json()

        if result is None or response is None:
            return  # TODO throw error

        # TODO replace by our own library
        result = humps.decamelize(result)

        if response.status == 200:
            return result

        # 401
        # {'errorCode': 'AUTHENTICATION_ERROR',
        #  'error': 'Too many requests, try again later : login with xxx@xxx.tld'}
        #  'error': 'Bad credentials'}
        #  'error': 'Your setup cannot be accessed through this application'}
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
