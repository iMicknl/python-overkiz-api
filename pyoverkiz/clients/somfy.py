from __future__ import annotations

import datetime
from typing import Any, cast

from aiohttp import FormData

from pyoverkiz.clients.overkiz import OverkizClient
from pyoverkiz.exceptions import SomfyBadCredentialsException, SomfyServiceException
from pyoverkiz.types import JSON

SOMFY_API = "https://accounts.somfy.com"
SOMFY_CLIENT_ID = "0d8e920c-1478-11e7-a377-02dd59bd3041_1ewvaqmclfogo4kcsoo0c8k4kso884owg08sg8c40sk4go4ksg"
SOMFY_CLIENT_SECRET = "12k73w1n540g8o4cokg0cw84cog840k84cwggscwg884004kgk"


class SomfyClient(OverkizClient):

    _access_token: str | None = None
    _refresh_token: str | None = None
    _expires_in: datetime.datetime | None = None

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._access_token}"}

    async def get(self, path: str) -> Any:
        """Make a GET request to the OverKiz API"""

        await self._refresh_token_if_expired()
        return await super().get(path)

    async def post(
        self, path: str, payload: JSON | None = None, data: JSON | None = None
    ) -> Any:
        """Make a POST request to the OverKiz API"""
        if path != "login":
            await self._refresh_token_if_expired()
        return await super().post(path, payload=payload, data=data)

    async def delete(self, path: str) -> None:
        """Make a DELETE request to the OverKiz API"""
        await self._refresh_token_if_expired()
        return await super().delete(path)

    async def _login(self, username: str, password: str) -> bool:
        """
        Authenticate and create an API session allowing access to the other operations.
        Caller must provide one of [userId+userPassword, userId+ssoToken, accessToken, jwt]
        """

        async with self.session.post(
            SOMFY_API + "/oauth/oauth/v2/token",
            data=FormData(
                {
                    "grant_type": "password",
                    "username": username,
                    "password": password,
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

        return True

    async def refresh_token(self) -> None:
        """
        Update the access and the refresh token. The refresh token will be valid 14 days.
        """

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
