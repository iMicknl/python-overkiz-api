import asyncio
from typing import cast

import boto3
from botocore.config import Config
from warrant_lite import WarrantLite

from pyoverkiz.client import OverkizClient
from pyoverkiz.const import (
    NEXITY_API,
    NEXITY_COGNITO_CLIENT_ID,
    NEXITY_COGNITO_REGION,
    NEXITY_COGNITO_USER_POOL,
)
from pyoverkiz.exceptions import BadCredentialsException


class NexityClient(OverkizClient):
    async def login(
        self,
        register_event_listener: bool | None = True,
    ) -> bool:
        """
        Authenticate and create an API session allowing access to the other operations.
        Caller must provide one of [userId+userPassword, userId+ssoToken, accessToken, jwt]
        """

        sso_token = await self.nexity_login()
        user_id = self.username.replace("@", "_-_")  # Replace @ for _-_
        payload = {"ssoToken": sso_token, "userId": user_id}
        response = await self.__post("login", data=payload)

        if response.get("success"):
            if register_event_listener:
                await self.register_event_listener()
            return True

        return False

    async def nexity_login(self) -> str:
        """
        Authenticate via Nexity identity and acquire SSO token.
        """
        loop = asyncio.get_event_loop()

        # Request access token
        client = boto3.client(
            "cognito-idp", config=Config(region_name=NEXITY_COGNITO_REGION)
        )
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
            f"{NEXITY_API}/deploy/api/v1/domotic/token",
            headers={
                "Authorization": id_token,
            },
        ) as response:
            token = await response.json()

            if "token" not in token:
                raise NexityServiceException("No Nexity SSO token provided.")

            return cast(str, token["token"])


class NexityBadCredentialsException(BadCredentialsException):
    pass


class NexityServiceException(Exception):
    pass
