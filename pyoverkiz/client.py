""" Python wrapper for the OverKiz API """
from __future__ import annotations

import asyncio
import datetime
import urllib.parse
from json import JSONDecodeError
from types import TracebackType
from typing import Any, cast

import backoff
import boto3
import humps
from aiohttp import ClientResponse, ClientSession, FormData, ServerDisconnectedError
from botocore.config import Config
from warrant_lite import WarrantLite

from pyoverkiz.const import (
    COZYTOUCH_ATLANTIC_API,
    COZYTOUCH_CLIENT_ID,
    NEXITY_API,
    NEXITY_COGNITO_CLIENT_ID,
    NEXITY_COGNITO_REGION,
    NEXITY_COGNITO_USER_POOL,
    SOMFY_API,
    SOMFY_CLIENT_ID,
    SOMFY_CLIENT_SECRET,
    SUPPORTED_SERVERS,
)
from pyoverkiz.exceptions import (
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
    SessionAndBearerInSameRequestException,
    SomfyBadCredentialsException,
    SomfyServiceException,
    TooManyConcurrentRequestsException,
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
from pyoverkiz.obfuscate import obfuscate_sensitive_data
from pyoverkiz.types import JSON


async def relogin(invocation: dict[str, Any]) -> None:
    await invocation["args"][0].login()


async def refresh_listener(invocation: dict[str, Any]) -> None:
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
        # Somfy TaHoma authentication using access_token
        if self.server == SUPPORTED_SERVERS["somfy_europe"]:
            await self.somfy_tahoma_get_access_token()

            if register_event_listener:
                await self.register_event_listener()

            return True

        # CozyTouch authentication using jwt
        if self.server == SUPPORTED_SERVERS["atlantic_cozytouch"]:
            jwt = await self.cozytouch_login()
            payload = {"jwt": jwt}

        # Nexity authentication using ssoToken
        elif self.server == SUPPORTED_SERVERS["nexity"]:
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

    async def somfy_tahoma_get_access_token(self) -> str:
        """
        Authenticate via Somfy identity and acquire access_token.
        """
        # Request access token
        async with self.session.post(
            SOMFY_API + "/oauth/oauth/v2/token",
            data=FormData(
                {
                    "grant_type": "password",
                    "username": self.username,
                    "password": self.password,
                    "client_id": SOMFY_CLIENT_ID,
                    "client_secret": SOMFY_CLIENT_SECRET,
                }
            ),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
        ) as response:
            token = await response.json()

            # { "message": "error.invalid.grant", "data": [], "uid": "xxx" }
            if "message" in token and token["message"] == "error.invalid.grant":
                raise SomfyBadCredentialsException(token["message"])

            if "access_token" not in token:
                raise SomfyServiceException("No Somfy access token provided.")

            self._access_token = cast(str, token["access_token"])
            self._refresh_token = token["refresh_token"]
            self._expires_in = datetime.datetime.now() + datetime.timedelta(
                seconds=token["expires_in"] - 5
            )

            return self._access_token

    async def refresh_token(self) -> None:
        """
        Update the access and the refresh token. The refresh token will be valid 14 days.
        """
        if self.server != SUPPORTED_SERVERS["somfy_europe"]:
            return

        if not self._refresh_token:
            raise ValueError("No refresh token provided. Login method must be used.")

        # &grant_type=refresh_token&refresh_token=REFRESH_TOKEN
        # Request access token
        async with self.session.post(
            SOMFY_API + "/oauth/oauth/v2/token",
            data=FormData(
                {
                    "grant_type": "refresh_token",
                    "refresh_token": self._refresh_token,
                    "client_id": SOMFY_CLIENT_ID,
                    "client_secret": SOMFY_CLIENT_SECRET,
                }
            ),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
        ) as response:
            token = await response.json()
            # { "message": "error.invalid.grant", "data": [], "uid": "xxx" }
            if "message" in token and token["message"] == "error.invalid.grant":
                raise SomfyBadCredentialsException(token["message"])

            if "access_token" not in token:
                raise SomfyServiceException("No Somfy access token provided.")

            self._access_token = cast(str, token["access_token"])
            self._refresh_token = token["refresh_token"]
            self._expires_in = datetime.datetime.now() + datetime.timedelta(
                seconds=token["expires_in"] - 5
            )

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
        loop = asyncio.get_event_loop()

        def _get_client() -> boto3.session.Session.client:
            return boto3.client(
                "cognito-idp", config=Config(region_name=NEXITY_COGNITO_REGION)
            )

        # Request access token
        client = await loop.run_in_executor(None, _get_client)

        aws = WarrantLite(
            username=self.username,
            password=self.password,
            pool_id=NEXITY_COGNITO_USER_POOL,
            client_id=NEXITY_COGNITO_CLIENT_ID,
            client=client,
        )

        try:
            tokens = await loop.run_in_executor(None, aws.authenticate_user)
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

            return cast(str, token["token"])

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
    async def get_diagnostic_data(self) -> JSON:
        """
        Get all data about the connected user setup
            -> gateways data (serial number, activation state, ...): <gateways/gateway>
            -> setup location: <location>
            -> house places (rooms and floors): <place>
            -> setup devices: <devices>

        This data will be masked to not return any confidential or PII data.
        """
        response = await self.__get("setup")

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
        response = await self.__post("events/register")
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
        await self._refresh_token_if_expired()
        response = await self.__post(f"events/{self.event_listener_id}/fetch")
        events = [Event(**e) for e in humps.decamelize(response)]

        return events

    async def unregister_event_listener(self) -> None:
        """
        Unregister an event listener.
        API response status is always 200, even on unknown listener ids.
        """
        await self._refresh_token_if_expired()
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
        headers = {}

        await self._refresh_token_if_expired()
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"

        async with self.session.get(
            f"{self.server.endpoint}{path}", headers=headers
        ) as response:
            await self.check_response(response)
            return await response.json()

    async def __post(
        self, path: str, payload: JSON | None = None, data: JSON | None = None
    ) -> Any:
        """Make a POST request to the OverKiz API"""
        headers = {}

        if path != "login" and self._access_token:
            await self._refresh_token_if_expired()
            headers["Authorization"] = f"Bearer {self._access_token}"

        async with self.session.post(
            f"{self.server.endpoint}{path}", data=data, json=payload, headers=headers
        ) as response:
            await self.check_response(response)
            return await response.json()

    async def __delete(self, path: str) -> None:
        """Make a DELETE request to the OverKiz API"""
        headers = {}

        await self._refresh_token_if_expired()

        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"

        async with self.session.delete(
            f"{self.server.endpoint}{path}", headers=headers
        ) as response:
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

            # {"errorCode": "RESOURCE_ACCESS_DENIED",  "error": "too many concurrent requests"}
            if message == "too many concurrent requests":
                raise TooManyConcurrentRequestsException(message)

            if message == "Cannot use JSESSIONID and bearer token in same request":
                raise SessionAndBearerInSameRequestException(message)

        raise Exception(message if message else result)

    async def _refresh_token_if_expired(self) -> None:
        """Check if token is expired and request a new one."""
        if (
            self._expires_in
            and self._refresh_token
            and self._expires_in <= datetime.datetime.now()
        ):
            await self.refresh_token()

            if self.event_listener_id:
                await self.register_event_listener()
