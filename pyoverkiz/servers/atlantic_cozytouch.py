from __future__ import annotations


from aiohttp import FormData
from pyoverkiz.const import COZYTOUCH_ATLANTIC_API, COZYTOUCH_CLIENT_ID
from pyoverkiz.exceptions import (
    CozyTouchBadCredentialsException,
    CozyTouchServiceException,
)

from pyoverkiz.servers.overkiz_server import OverkizServer


class AtlanticCozytouch(OverkizServer):
    async def login(self, username: str, password: str) -> bool:
        """
        Authenticate and create an API session allowing access to the other operations.
        Caller must provide one of [userId+userPassword, userId+ssoToken, accessToken, jwt]
        """

        async with self.session.post(
            COZYTOUCH_ATLANTIC_API + "/token",
            data=FormData(
                {
                    "grant_type": "password",
                    "username": "GA-PRIVATEPERSON/" + username,
                    "password": password,
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
            COZYTOUCH_ATLANTIC_API + "/magellan/accounts/jwt",
            headers={"Authorization": f"Bearer {token['access_token']}"},
        ) as response:
            jwt = await response.text()

            if not jwt:
                raise CozyTouchServiceException("No JWT token provided.")

            jwt = jwt.strip('"')  # Remove surrounding quotes

        payload = {"jwt": jwt}

        response = await self.post("login", data=payload)

        if response.get("success"):
            return True

        return False
