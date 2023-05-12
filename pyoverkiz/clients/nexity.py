from __future__ import annotations

import asyncio
from typing import cast

import boto3
from attr import define, field
from botocore.config import Config
from warrant_lite import WarrantLite

from pyoverkiz.clients.overkiz import OverkizClient
from pyoverkiz.exceptions import NexityBadCredentialsException, NexityServiceException

NEXITY_API = "https://api.egn.prd.aws-nexity.fr"
NEXITY_COGNITO_CLIENT_ID = "3mca95jd5ase5lfde65rerovok"
NEXITY_COGNITO_USER_POOL = "eu-west-1_wj277ucoI"
NEXITY_COGNITO_REGION = "eu-west-1"


@define(kw_only=True)
class NexityClient(OverkizClient):

    username: str
    password: str = field(repr=lambda _: "***")

    async def _login(self) -> bool:
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

        async with self.session.get(
            NEXITY_API + "/deploy/api/v1/domotic/token",
            headers={
                "Authorization": tokens["AuthenticationResult"]["IdToken"],
            },
        ) as response:
            token = await response.json()

            if "token" not in token:
                raise NexityServiceException("No Nexity SSO token provided.")

            sso_token = cast(str, token["token"])

        user_id = self.username.replace("@", "_-_")  # Replace @ for _-_
        payload = {"ssoToken": sso_token, "userId": user_id}

        post_response = await self.post("login", data=payload)

        return "success" in post_response
