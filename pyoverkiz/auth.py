from __future__ import annotations

from typing import Any

from aiohttp import ClientResponse, ClientSession, FormData, ServerDisconnectedError

from .types import JSON


class OverkizAuthentication:
    """Used as interface class"""

    _session: ClientSession
    _server: str

    def __init__(
        self,
        server: str,
        session: ClientSession,
    ) -> None:
        self._session = session
        self._server = server

    async def login(
        self,
        register_event_listener: bool | None = True,
    ) -> bool:
        """
        Authenticate and create an API session allowing access to the other operations.
        Caller must provide one of [userId+userPassword, userId+ssoToken, accessToken, jwt]
        """
        pass

    async def __get(self, path: str) -> Any:
        """Make a GET request to the OverKiz API"""
        pass

    async def __post(
        self, path: str, payload: JSON | None = None, data: JSON | None = None
    ) -> Any:
        """Make a POST request to the OverKiz API"""
        pass


class SimpleAuthentication(OverkizAuthentication):
    """userId+userPassword authentication"""

    _username: str
    _password: str

    def __init__(
        self, server: str, session: ClientSession, username: str, password: str
    ) -> None:
        super().__init__(server, session)
        self._username = username
        self._password = password

    async def login(
        self,
        register_event_listener: bool | None = True,
    ) -> bool:
        """
        Authenticate and create an API session allowing access to the other operations.
        Caller must provide one of [userId+userPassword, userId+ssoToken, accessToken, jwt]
        """
        payload = {"userId": self._username, "userPassword": self._password}

        response = await self.__post("login", data=payload)

        if response.get("success"):
            if register_event_listener:
                await self.register_event_listener()
            return True

        return False

    async def __get(self, path: str) -> Any:
        """Make a GET request to the OverKiz API"""
        async with self._session.get(f"{self.server.endpoint}{path}") as response:
            await self.check_response(response)
            return await response.json()

    async def __post(
        self, path: str, payload: JSON | None = None, data: JSON | None = None
    ) -> Any:
        """Make a POST request to the OverKiz API"""
        pass


class LocalAuthentication(OverkizAuthentication):
    """Used as interface class"""

    _host: str
    _port: int
    _certificate: str

    async def login(
        self,
        register_event_listener: bool | None = True,
    ) -> bool:
        """
        Authenticate and create an API session allowing access to the other operations.
        Caller must provide one of [userId+userPassword, userId+ssoToken, accessToken, jwt]
        """
        pass

    async def __get():
        pass

    async def __post():
        pass


class SomfyTahomaAuthentication(OverkizAuthentication):
    """Used as interface class"""

    _username: str
    _password: str

    _refresh_token: str
    _expires_in: int

    async def login(
        self,
        register_event_listener: bool | None = True,
    ) -> bool:
        """
        Authenticate and create an API session allowing access to the other operations.
        Caller must provide one of [userId+userPassword, userId+ssoToken, accessToken, jwt]
        """
        pass

    async def __get():
        pass

    async def __post():
        pass


class CozyTouchAuthentication(OverkizAuthentication):
    """Used as interface class"""

    _username: str
    _password: str

    _refresh_token: str
    _expires_in: int

    async def login(
        self,
        register_event_listener: bool | None = True,
    ) -> bool:
        """
        Authenticate and create an API session allowing access to the other operations.
        Caller must provide one of [userId+userPassword, userId+ssoToken, accessToken, jwt]
        """
        # payload = {"jwt": jwt}

        pass

    async def __get():
        pass

    async def __post():
        pass
