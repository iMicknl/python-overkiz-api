""" Python wrapper for the Tahoma API """
from __future__ import annotations

import urllib.parse
from json import JSONDecodeError
from types import TracebackType
from typing import Any, Dict, List, Union

import backoff
import boto3
import humps
from aiohttp import ClientResponse, ClientSession, FormData, ServerDisconnectedError
from botocore.config import Config
from warrant.aws_srp import AWSSRP

from pyhoma.const import (
    COZYTOUCH_ATLANTIC_API,
    COZYTOUCH_CLIENT_ID,
    NEXITY_API,
    NEXITY_COGNITO_CLIENT_ID,
    NEXITY_COGNITO_REGION,
    NEXITY_COGNITO_USER_POOL,
    SUPPORTED_SERVERS,
)
from pyhoma.exceptions import (
    BadCredentialsException,
    CozyTouchBadCredentialsException,
    CozyTouchServiceException,
    InvalidCommandException,
    InvalidEventListenerIdException,
    MaintenanceException,
    NexityBadCredentialsException,
    NexityServiceException,
    NoRegisteredEventListenerException,
    NotAuthenticatedException,
    TooManyExecutionsException,
    TooManyRequestsException,
)
from pyhoma.models import (
    Command,
    Device,
    Event,
    Execution,
    Gateway,
    HistoryExecution,
    Place,
    Scenario,
    State,
)

JSON = Union[Dict[str, Any], List[Dict[str, Any]]]

DEFAULT_SERVER = SUPPORTED_SERVERS["somfy_europe"]


async def relogin(invocation: dict[str, Any]) -> None:
    await invocation["args"][0].login()


async def refresh_listener(invocation: dict[str, Any]) -> None:
    await invocation["args"][0].register_event_listener()


class TahomaClient:
    """Interface class for the Overkiz API"""

    def __init__(
        self,
        username: str,
        password: str,
        api_url: str = DEFAULT_SERVER.endpoint,
        session: ClientSession = None,
    ) -> None:
        """
        Constructor

        :param username: the username for Tahomalink.com
        :param password: the password for Tahomalink.com
        :param api_url: optional custom api url
        :param session: optional ClientSession
        """

        self.username = username
        self.password = password
        self.api_url = api_url

        self.devices: list[Device] = []
        self.gateways: list[Gateway] = []
        self.event_listener_id: str | None = None

        self.session = session if session else ClientSession()

    async def __aenter__(self) -> TahomaClient:
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

        # CozyTouch authentication using jwt
        if self.api_url == SUPPORTED_SERVERS["atlantic_cozytouch"].endpoint:
            jwt = await self.cozytouch_login()
            payload = {"jwt": jwt}

        # Nexity authentication using ssoToken
        elif self.api_url == SUPPORTED_SERVERS["nexity"].endpoint:
            sso_token = await self.nexity_login()
            user_id = self.username.replace("@", "_-_")  # Replace @ for _-_
            payload = {"ssoToken": sso_token, "userId": user_id}

        # Regular authentication using userId+userPassword
        else:
            payload = {"userId": self.username, "userPassword": self.password}

        response = await self.__post("login", data=payload)

        if response.get("success"):
            if register_event_listener:
                await self.register_event_listener()
            return True

        return False

    async def cozytouch_login(self) -> str:
        """
        Authenticate via CozyTouch identity and acquire JWT token.
        """
        # Request access token
        async with self.session.post(
            COZYTOUCH_ATLANTIC_API + "/token",
            data=FormData(
                {
                    "grant_type": "password",
                    "username": self.username,
                    "password": self.password,
                }
            ),
            headers={
                "Authorization": f"Basic {COZYTOUCH_CLIENT_ID}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        ) as response:
            token = await response.json()

            # {'error': 'invalid_grant',
            # 'error_description': 'Provided Authorization Grant is invalid.'}
            if "error" in token and token["error"] == "invalid_grant":
                raise CozyTouchBadCredentialsException(token["error_description"])

            if "token_type" not in token:
                raise CozyTouchServiceException("No CozyTouch token provided.")

        # Request JWT
        async with self.session.get(
            COZYTOUCH_ATLANTIC_API + "/gacoma/gacomawcfservice/accounts/jwt",
            headers={"Authorization": f"Bearer {token['access_token']}"},
        ) as response:
            jwt = await response.text()

            if not jwt:
                raise CozyTouchServiceException("No JWT token provided.")

            jwt = jwt.strip('"')  # Remove surrounding quotes

            return jwt

    async def nexity_login(self) -> str:
        """
        Authenticate via Nexity identity and acquire SSO token.
        """
        # Request access token
        client = boto3.client(
            "cognito-idp", config=Config(region_name=NEXITY_COGNITO_REGION)
        )
        aws = AWSSRP(
            username=self.username,
            password=self.password,
            pool_id=NEXITY_COGNITO_USER_POOL,
            client_id=NEXITY_COGNITO_CLIENT_ID,
            client=client,
        )

        try:
            tokens = aws.authenticate_user()
        except Exception as error:
            raise NexityBadCredentialsException() from error

        id_token = tokens["AuthenticationResult"]["IdToken"]

        async with self.session.get(
            NEXITY_API + "/deploy/api/v1/domotic/token",
            headers={
                "Authorization": id_token,
            },
        ) as response:
            token = await response.json()

            if "token" not in token:
                raise NexityServiceException("No Nexity SSO token provided.")

            return token["token"]

    @backoff.on_exception(
        backoff.expo,
        (NotAuthenticatedException, ServerDisconnectedError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def get_devices(self, refresh: bool = False) -> list[Device]:
        """
        List devices
        """
        if self.devices and not refresh:
            return self.devices

        response = await self.__get("setup/devices")
        devices = [Device(**d) for d in humps.decamelize(response)]
        self.devices = devices

        return devices

    @backoff.on_exception(
        backoff.expo,
        (NotAuthenticatedException, ServerDisconnectedError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def get_gateways(self, refresh: bool = False) -> list[Gateway]:
        """
        List gateways
        """
        if self.gateways and not refresh:
            return self.gateways

        response = await self.__get("setup/gateways")
        gateways = [Gateway(**g) for g in humps.decamelize(response)]
        self.gateways = gateways

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
        response = await self.__get(
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
        listener_id = response.get("id")
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
        label: str | None = "python-tahoma-api",
    ) -> str:
        """Send a command"""
        if isinstance(command, str):
            command = Command(command)
        return await self.execute_commands(device_url, [command], label)

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
        label: str | None = "python-tahoma-api",
    ) -> str:
        """Send several commands in one call"""
        payload = {
            "label": label,
            "actions": [{"deviceURL": device_url, "commands": commands}],
        }
        response = await self.__post("exec/apply", payload)
        return response["execId"]

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
        return response["execId"]

    async def __get(self, endpoint: str) -> Any:
        """Make a GET request to the TaHoma API"""
        async with self.session.get(f"{self.api_url}{endpoint}") as response:
            await self.check_response(response)
            return await response.json()

    async def __post(
        self, endpoint: str, payload: JSON | None = None, data: JSON | None = None
    ) -> Any:
        """Make a POST request to the TaHoma API"""
        async with self.session.post(
            f"{self.api_url}{endpoint}",
            data=data,
            json=payload,
        ) as response:
            await self.check_response(response)
            return await response.json()

    async def __delete(self, endpoint: str) -> None:
        """Make a DELETE request to the TaHoma API"""
        async with self.session.delete(f"{self.api_url}{endpoint}") as response:
            await self.check_response(response)

    @staticmethod
    async def check_response(response: ClientResponse) -> None:
        """Check the response returned by the TaHoma API"""
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
