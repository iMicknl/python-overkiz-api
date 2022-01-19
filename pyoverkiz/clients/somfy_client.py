from aiohttp import FormData

from pyoverkiz.client import OverkizClient
from pyoverkiz.const import SOMFY_API, SOMFY_CLIENT_ID, SOMFY_CLIENT_SECRET
from pyoverkiz.exceptions import BadCredentialsException


class SomfyEuropeClient(OverkizClient):
    async def login(
        self,
        register_event_listener: bool | None = True,
    ) -> bool:
        """
        Authenticate and create an API session allowing access to the other operations.
        Caller must provide one of [userId+userPassword, userId+ssoToken, accessToken, jwt]
        """

        access_token = await self.somfy_tahoma_login()
        payload = {"accessToken": access_token}
        response = await self.__post("login", data=payload)

        if response.get("success"):
            if register_event_listener:
                await self.register_event_listener()
            return True

        return False

    async def somfy_tahoma_login(self) -> str:
        """
        Authenticate via Somfy identity and acquire access_token.
        """
        # Request access token
        async with self.session.post(
            f"{SOMFY_API}/oauth/oauth/v2/token",
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

            return str(token["access_token"])


class SomfyBadCredentialsException(BadCredentialsException):
    pass


class SomfyServiceException(Exception):
    pass
