"""Authentication strategies for Overkiz API."""

from __future__ import annotations

import asyncio
import base64
import binascii
import datetime
import json
import ssl
from collections.abc import Mapping
from typing import Any, cast

import boto3
from aiohttp import ClientSession, FormData
from botocore.client import BaseClient
from botocore.config import Config
from warrant_lite import WarrantLite

from pyoverkiz.auth.base import AuthContext, AuthStrategy
from pyoverkiz.auth.credentials import (
    LocalTokenCredentials,
    RexelOAuthCodeCredentials,
    TokenCredentials,
    UsernamePasswordCredentials,
)
from pyoverkiz.const import (
    COZYTOUCH_ATLANTIC_API,
    COZYTOUCH_CLIENT_ID,
    NEXITY_API,
    NEXITY_COGNITO_CLIENT_ID,
    NEXITY_COGNITO_REGION,
    NEXITY_COGNITO_USER_POOL,
    REXEL_OAUTH_CLIENT_ID,
    REXEL_OAUTH_SCOPE,
    REXEL_OAUTH_TOKEN_URL,
    REXEL_REQUIRED_CONSENT,
    SOMFY_API,
    SOMFY_CLIENT_ID,
    SOMFY_CLIENT_SECRET,
)
from pyoverkiz.enums import APIType
from pyoverkiz.exceptions import (
    BadCredentialsException,
    CozyTouchBadCredentialsException,
    CozyTouchServiceException,
    InvalidTokenException,
    NexityBadCredentialsException,
    NexityServiceException,
    SomfyBadCredentialsException,
    SomfyServiceException,
)
from pyoverkiz.models import ServerConfig


class BaseAuthStrategy(AuthStrategy):
    """Base class for authentication strategies."""

    def __init__(
        self,
        session: ClientSession,
        server: ServerConfig,
        ssl_context: ssl.SSLContext | bool,
        api_type: APIType,
    ) -> None:
        """Store shared auth context for Overkiz API interactions."""
        self.session = session
        self.server = server
        self._ssl = ssl_context
        self.api_type = api_type

    async def login(self) -> None:
        """Perform authentication; default is a no-op for subclasses to override."""
        return None

    async def refresh_if_needed(self) -> bool:
        """Refresh authentication tokens if needed; default returns False."""
        return False

    def auth_headers(self, path: str | None = None) -> Mapping[str, str]:
        """Return authentication headers for a request path."""
        return {}

    async def close(self) -> None:
        """Close any resources held by the strategy; default is no-op."""
        return None


class SessionLoginStrategy(BaseAuthStrategy):
    """Authentication strategy using session-based login."""

    def __init__(
        self,
        credentials: UsernamePasswordCredentials,
        session: ClientSession,
        server: ServerConfig,
        ssl_context: ssl.SSLContext | bool,
        api_type: APIType,
    ) -> None:
        """Initialize SessionLoginStrategy with given parameters."""
        super().__init__(session, server, ssl_context, api_type)
        self.credentials = credentials

    async def login(self) -> None:
        """Perform login using username and password."""
        payload = {
            "userId": self.credentials.username,
            "userPassword": self.credentials.password,
        }
        await self._post_login(payload)

    async def _post_login(self, data: Mapping[str, Any]) -> None:
        """Post login data to the server and handle response."""
        async with self.session.post(
            f"{self.server.endpoint}login",
            data=data,
            ssl=self._ssl,
        ) as response:
            if response.status not in (200, 204):
                raise BadCredentialsException(
                    f"Login failed for {self.server.name}: {response.status}"
                )

            result = await response.json()
            if not result.get("success"):
                raise BadCredentialsException("Login failed: bad credentials")


class SomfyAuthStrategy(BaseAuthStrategy):
    """Authentication strategy using Somfy OAuth2."""

    def __init__(
        self,
        credentials: UsernamePasswordCredentials,
        session: ClientSession,
        server: ServerConfig,
        ssl_context: ssl.SSLContext | bool,
        api_type: APIType,
    ) -> None:
        """Initialize SomfyAuthStrategy with given parameters."""
        super().__init__(session, server, ssl_context, api_type)
        self.credentials = credentials
        self.context = AuthContext()

    async def login(self) -> None:
        """Perform login using Somfy OAuth2."""
        await self._request_access_token(
            grant_type="password",
            extra_fields={
                "username": self.credentials.username,
                "password": self.credentials.password,
            },
        )

    async def refresh_if_needed(self) -> bool:
        """Refresh Somfy OAuth2 tokens if needed."""
        if not self.context.is_expired() or not self.context.refresh_token:
            return False

        await self._request_access_token(
            grant_type="refresh_token",
            extra_fields={"refresh_token": cast(str, self.context.refresh_token)},
        )
        return True

    def auth_headers(self, path: str | None = None) -> Mapping[str, str]:
        """Return authentication headers for a request path."""
        if self.context.access_token:
            return {"Authorization": f"Bearer {self.context.access_token}"}

        return {}

    async def _request_access_token(
        self, *, grant_type: str, extra_fields: Mapping[str, str]
    ) -> None:
        form = FormData(
            {
                "grant_type": grant_type,
                "client_id": SOMFY_CLIENT_ID,
                "client_secret": SOMFY_CLIENT_SECRET,
                **extra_fields,
            }
        )

        async with self.session.post(
            f"{SOMFY_API}/oauth/oauth/v2/token/jwt",
            data=form,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ) as response:
            token = await response.json()

            if token.get("message") == "error.invalid.grant":
                raise SomfyBadCredentialsException(token["message"])

            access_token = token.get("access_token")
            if not access_token:
                raise SomfyServiceException("No Somfy access token provided.")

            self.context.access_token = cast(str, access_token)
            self.context.refresh_token = token.get("refresh_token")
            expires_in = token.get("expires_in")
            if expires_in:
                self.context.expires_at = datetime.datetime.now() + datetime.timedelta(
                    seconds=cast(int, expires_in) - 5
                )


class CozytouchAuthStrategy(SessionLoginStrategy):
    """Authentication strategy using Cozytouch session-based login."""

    def __init__(
        self,
        credentials: UsernamePasswordCredentials,
        session: ClientSession,
        server: ServerConfig,
        ssl_context: ssl.SSLContext | bool,
        api_type: APIType,
    ) -> None:
        """Initialize CozytouchAuthStrategy with given parameters."""
        super().__init__(credentials, session, server, ssl_context, api_type)

    async def login(self) -> None:
        """Perform login using Cozytouch username and password."""
        form = FormData(
            {
                "grant_type": "password",
                "username": f"GA-PRIVATEPERSON/{self.credentials.username}",
                "password": self.credentials.password,
            }
        )
        async with self.session.post(
            f"{COZYTOUCH_ATLANTIC_API}/token",
            data=form,
            headers={
                "Authorization": f"Basic {COZYTOUCH_CLIENT_ID}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        ) as response:
            token = await response.json()

            if token.get("error") == "invalid_grant":
                raise CozyTouchBadCredentialsException(token["error_description"])

            if "token_type" not in token:
                raise CozyTouchServiceException("No CozyTouch token provided.")

        async with self.session.get(
            f"{COZYTOUCH_ATLANTIC_API}/magellan/accounts/jwt",
            headers={"Authorization": f"Bearer {token['access_token']}"},
        ) as response:
            jwt = await response.text()

            if not jwt:
                raise CozyTouchServiceException("No JWT token provided.")

            jwt = jwt.strip('"')

        await self._post_login({"jwt": jwt})


class NexityAuthStrategy(SessionLoginStrategy):
    """Authentication strategy using Nexity session-based login."""

    def __init__(
        self,
        credentials: UsernamePasswordCredentials,
        session: ClientSession,
        server: ServerConfig,
        ssl_context: ssl.SSLContext | bool,
        api_type: APIType,
    ) -> None:
        """Initialize NexityAuthStrategy with given parameters."""
        super().__init__(credentials, session, server, ssl_context, api_type)

    async def login(self) -> None:
        """Perform login using Nexity username and password."""
        loop = asyncio.get_event_loop()

        def _client() -> BaseClient:
            return boto3.client(
                "cognito-idp", config=Config(region_name=NEXITY_COGNITO_REGION)
            )

        client = await loop.run_in_executor(None, _client)
        aws = WarrantLite(
            username=self.credentials.username,
            password=self.credentials.password,
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
            headers={"Authorization": id_token},
        ) as response:
            token = await response.json()

            if "token" not in token:
                raise NexityServiceException("No Nexity SSO token provided.")

            user_id = self.credentials.username.replace("@", "_-_")
            await self._post_login({"ssoToken": token["token"], "userId": user_id})


class LocalTokenAuthStrategy(BaseAuthStrategy):
    """Authentication strategy using a local API token."""

    def __init__(
        self,
        credentials: LocalTokenCredentials,
        session: ClientSession,
        server: ServerConfig,
        ssl_context: ssl.SSLContext | bool,
        api_type: APIType,
    ) -> None:
        """Initialize LocalTokenAuthStrategy with given parameters."""
        super().__init__(session, server, ssl_context, api_type)
        self.credentials = credentials

    async def login(self) -> None:
        """Validate that a token is provided for local API access."""
        if not self.credentials.token:
            raise InvalidTokenException("Local API requires a token.")

    def auth_headers(self, path: str | None = None) -> Mapping[str, str]:
        """Return authentication headers for a request path."""
        return {"Authorization": f"Bearer {self.credentials.token}"}


class RexelAuthStrategy(BaseAuthStrategy):
    """Authentication strategy using Rexel OAuth2."""

    def __init__(
        self,
        credentials: RexelOAuthCodeCredentials,
        session: ClientSession,
        server: ServerConfig,
        ssl_context: ssl.SSLContext | bool,
        api_type: APIType,
    ) -> None:
        """Initialize RexelAuthStrategy with given parameters."""
        super().__init__(session, server, ssl_context, api_type)
        self.credentials = credentials
        self.context = AuthContext()

    async def login(self) -> None:
        """Perform login using Rexel OAuth2 authorization code."""
        await self._exchange_token(
            {
                "grant_type": "authorization_code",
                "client_id": REXEL_OAUTH_CLIENT_ID,
                "scope": REXEL_OAUTH_SCOPE,
                "code": self.credentials.code,
                "redirect_uri": self.credentials.redirect_uri,
            }
        )

    async def refresh_if_needed(self) -> bool:
        """Refresh Rexel OAuth2 tokens if needed."""
        if not self.context.is_expired() or not self.context.refresh_token:
            return False

        await self._exchange_token(
            {
                "grant_type": "refresh_token",
                "client_id": REXEL_OAUTH_CLIENT_ID,
                "scope": REXEL_OAUTH_SCOPE,
                "refresh_token": cast(str, self.context.refresh_token),
            }
        )
        return True

    def auth_headers(self, path: str | None = None) -> Mapping[str, str]:
        """Return authentication headers for a request path."""
        if self.context.access_token:
            return {"Authorization": f"Bearer {self.context.access_token}"}
        return {}

    async def _exchange_token(self, payload: Mapping[str, str]) -> None:
        """Exchange authorization code or refresh token for access token."""
        form = FormData(payload)
        async with self.session.post(
            REXEL_OAUTH_TOKEN_URL,
            data=form,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ) as response:
            token = await response.json()

            access_token = token.get("access_token")
            if not access_token:
                raise InvalidTokenException("No Rexel access token provided.")

            self._ensure_consent(access_token)
            self.context.access_token = cast(str, access_token)
            self.context.refresh_token = token.get("refresh_token")
            expires_in = token.get("expires_in")
            if expires_in:
                self.context.expires_at = datetime.datetime.now() + datetime.timedelta(
                    seconds=cast(int, expires_in) - 5
                )

    @staticmethod
    def _ensure_consent(access_token: str) -> None:
        """Ensure that the Rexel token has the required consent."""
        payload = _decode_jwt_payload(access_token)
        consent = payload.get("consent")
        if consent != REXEL_REQUIRED_CONSENT:
            raise InvalidTokenException(
                "Consent is missing or revoked for Rexel token."
            )


class BearerTokenAuthStrategy(BaseAuthStrategy):
    """Authentication strategy using a static bearer token."""

    def __init__(
        self,
        credentials: TokenCredentials,
        session: ClientSession,
        server: ServerConfig,
        ssl_context: ssl.SSLContext | bool,
        api_type: APIType,
    ) -> None:
        """Initialize BearerTokenAuthStrategy with given parameters."""
        super().__init__(session, server, ssl_context, api_type)
        self.credentials = credentials

    def auth_headers(self, path: str | None = None) -> Mapping[str, str]:
        """Return authentication headers for a request path."""
        if self.credentials.token:
            return {"Authorization": f"Bearer {self.credentials.token}"}
        return {}


def _decode_jwt_payload(token: str) -> dict[str, Any]:
    """Decode the payload of a JWT token."""
    parts = token.split(".")
    if len(parts) < 2:
        raise InvalidTokenException("Malformed JWT received.")

    payload_segment = parts[1]
    padding = "=" * (-len(payload_segment) % 4)
    try:
        decoded = base64.urlsafe_b64decode(payload_segment + padding)
        return cast(dict[str, Any], json.loads(decoded))
    except (binascii.Error, json.JSONDecodeError) as error:
        raise InvalidTokenException("Malformed JWT received.") from error
