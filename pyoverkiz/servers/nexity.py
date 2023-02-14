from __future__ import annotations

import asyncio

from typing import cast

import boto3

from botocore.config import Config
from warrant_lite import WarrantLite

from pyoverkiz.const import (
    NEXITY_API,
    NEXITY_COGNITO_CLIENT_ID,
    NEXITY_COGNITO_REGION,
    NEXITY_COGNITO_USER_POOL,
)
from pyoverkiz.exceptions import (
    NexityBadCredentialsException,
    NexityServiceException,
)

from pyoverkiz.servers.overkiz_server import OverkizServer


class NexityServer(OverkizServer):
    async def login(self, username: str, password: str) -> bool:
        """
        Authenticate and create an API session allowing access to the other operations.
        Caller must provide one of [userId+userPassword, userId+ssoToken, accessToken, jwt]
        """

        loop = asyncio.get_event_loop()

        def _get_client() -> boto3.session.Session.client:
            return boto3.client(
                "cognito-idp", config=Config(region_name=NEXITY_COGNITO_REGION)
            )

        # Request access token
        client = await loop.run_in_executor(None, _get_client)

        aws = WarrantLite(
            username=username,
            password=password,
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

            sso_token = cast(str, token["token"])

        user_id = username.replace("@", "_-_")  # Replace @ for _-_
        payload = {"ssoToken": sso_token, "userId": user_id}

        response = await self.server.post("login", data=payload)

        if response.get("success"):
            return True

        return False
