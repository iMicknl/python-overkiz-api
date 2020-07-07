""" Python wrapper for the Tahoma API """
from typing import Any, List, Optional

import aiohttp

from tahoma_api.models import Device

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

        self.__cookies = None
        self.devices: List[Device] = []
        self.__roles = None

    async def login(self) -> bool:

        payload = {"userId": self.username, "userPassword": self.password}

        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url + "login", data=payload) as response:

                result = await response.json()

                # 401
                # {'errorCode': 'AUTHENTICATION_ERROR',
                #  'error': 'Bad credentials'}
                # {'errorCode': 'AUTHENTICATION_ERROR',
                #  'error': 'Your setup cannot be accessed through this application'}
                if response.status == 401:
                    if result["errorCode"] == "AUTHENTICATION_ERROR":

                        if "Too many requests" in result["error"]:
                            print(result["error"])
                            raise Exception

                        if (
                            "Your setup cannot be accessed through this application"
                            in result["error"]
                        ):
                            print(result["error"])

                        if "Bad credentials" in result["error"]:
                            print(result["error"])

                        print(result["error"])

                        return False  # todo throw error

                # 401
                # {'errorCode': 'AUTHENTICATION_ERROR',
                #  'error': 'Too many requests, try again later : login with xxx@xxx.tld'}
                # TODO Add retry logic on too many requests + for debug, log requests + timespans

                # 200
                # {'success': True, 'roles': [{'name': 'ENDUSER'}]}
                if response.status == 200:
                    if result["success"]:
                        self.__roles = result["roles"]
                        self.__cookies = response.cookies

                        return True

                # Temp fallbacks
                print(response.status)
                print(result)

                return False

    async def get_devices(self, refresh: bool = False) -> List[Device]:
        if self.devices and not refresh:
            return self.devices

        response = await self.__make_http_request("GET", "setup/devices")

        devices = [Device(**d) for d in response]
        self.devices = devices

        return devices

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
        response = await self.__make_http_request("POST", "events/register")
        listener_id = response.get("id")

        return listener_id

    async def fetch_event_listener(self, listener_id: str) -> List[Any]:
        """
        Fetch new events from a registered event listener. Fetched events are removed
        from the listener buffer. Return an empty response if no event is available.
        Per-session rate-limit : 1 calls per 1 SECONDS period for this particular
        operation (polling)
        """
        response = await self.__make_http_request("POST", f"events/{listener_id}/fetch")

        return response

    async def execute_action_group(
        self, actions: List[Command], label: str = "python-tahoma-api"
    ) -> List[Any]:
        """ Execute a non-persistent action group.
        The executed action group does not have to be persisted on the server before
        use.
        Per-session rate-limit : 50 calls per 24 HOURS period for all operations of the
        same category (exec)
        """
        payload = {"label": label, "actions": actions}
        response = await self.__make_http_request("POST", "exec/apply", payload)

        return response

    async def __make_http_request(
        self, method: str, endpoint: str, payload: Optional[Any] = None
    ) -> Any:
        """Make a request to the TaHoma API"""
        cookies = self.__cookies
        supported_methods = ["GET", "POST"]

        if method not in supported_methods:
            raise Exception

        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(
                    self.api_url + endpoint, cookies=cookies
                ) as response:
                    result = await response.json()

            if method == "POST":
                async with session.post(
                    self.api_url + endpoint, cookies=cookies, data=payload
                ) as response:
                    result = await response.json()

        if response.status == 200:
            return result

        if 400 < response.status < 500:
            # implement retry logic
            print("TODO")
