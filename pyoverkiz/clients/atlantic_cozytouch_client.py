from aiohttp import FormData
from pyoverkiz.client import OverkizClient
from pyoverkiz.const import COZYTOUCH_ATLANTIC_API, COZYTOUCH_CLIENT_ID
from pyoverkiz.exceptions import BadCredentialsException


class AtlanticCozytouchClient(OverkizClient):
    async def login(
        self,
        register_event_listener: bool | None = True,
    ) -> bool:
        """
        Authenticate and create an API session allowing access to the other operations.
        Caller must provide one of [userId+userPassword, userId+ssoToken, accessToken, jwt]
        """

        jwt = await self.cozytouch_login()
        payload = {"jwt": jwt}
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
            f"{COZYTOUCH_ATLANTIC_API}/token",
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
            f"{COZYTOUCH_ATLANTIC_API}/gacoma/gacomawcfservice/accounts/jwt",
            headers={"Authorization": f"Bearer {token['access_token']}"},
        ) as response:
            jwt = await response.text()

            if not jwt:
                raise CozyTouchServiceException("No JWT token provided.")

            jwt = jwt.strip('"')  # Remove surrounding quotes

            return jwt


class CozyTouchBadCredentialsException(BadCredentialsException):
    pass


class CozyTouchServiceException(Exception):
    pass
