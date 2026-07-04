"""Authentication strategies for Overkiz API."""

from __future__ import annotations

import asyncio
import base64
import binascii
import datetime
import json
import ssl
from collections.abc import Mapping
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from botocore.client import BaseClient

from aiohttp import ClientResponse, ClientSession, FormData

from pyoverkiz.auth.base import AuthContext, AuthStrategy, GatewayCandidate
from pyoverkiz.auth.credentials import (
    LocalTokenCredentials,
    RexelOAuthCodeCredentials,
    RexelTokenCredentials,
    TokenCredentials,
    UsernamePasswordCredentials,
)
from pyoverkiz.const import (
    BOB_API_KEY,
    BOB_SITE_API,
    BRANDT_MIDDLEWARE_API,
    BRANDT_PARTNER,
    COZYTOUCH_ATLANTIC_API,
    COZYTOUCH_CLIENT_ID,
    GINAITE_SUBJECT_ISSUER,
    GINAITE_SUBJECT_TOKEN_TYPE,
    GINAITE_TOKEN_EXCHANGE_GRANT,
    GINAITE_TOKEN_URL,
    NEXITY_API,
    NEXITY_COGNITO_CLIENT_ID,
    NEXITY_COGNITO_REGION,
    NEXITY_COGNITO_USER_POOL,
    REXEL_ENDUSER_API,
    REXEL_GATEWAY_HEADER,
    REXEL_OAUTH_CLIENT_ID,
    REXEL_OAUTH_SCOPE,
    REXEL_OAUTH_TOKEN_URL,
    REXEL_REQUIRED_CONSENT,
    SOMFY_API,
    SOMFY_CLIENT_ID,
    SOMFY_CLIENT_SECRET,
    SOMFY_COUNTRY_REGION,
    SOMFY_REGION_ENDPOINT,
)
from pyoverkiz.exceptions import (
    BadCredentialsError,
    BrandtBadCredentialsError,
    BrandtServiceError,
    CozyTouchBadCredentialsError,
    CozyTouchServiceError,
    InvalidTokenError,
    NexityBadCredentialsError,
    NexityServiceError,
    NoGatewaySelectedError,
    SomfyBadCredentialsError,
    SomfyServiceError,
)
from pyoverkiz.models import ServerConfig
from pyoverkiz.response_handler import check_response

MIN_JWT_SEGMENTS = 2


async def _raise_for_server_error(response: ClientResponse) -> None:
    """Map a 5xx token-endpoint response to a typed Overkiz exception.

    Token endpoints handle their own 4xx JSON error format, but on 5xx may
    serve an HTML error page. Route 5xx through ``check_response`` so it raises
    ``ServiceUnavailableError`` (or ``MaintenanceError``).
    """
    if response.status >= HTTPStatus.INTERNAL_SERVER_ERROR:
        await check_response(response)


async def _somfy_password_token(
    session: ClientSession, username: str, password: str
) -> dict[str, Any]:
    """Perform the Somfy Accounts password grant and return the raw token dict.

    Shared by SomfyAuthStrategy (single-site) and SomfyMultisiteAuthStrategy
    (which feeds the returned access_token into the Keycloak token exchange).
    """
    form = FormData(
        {
            "grant_type": "password",
            "client_id": SOMFY_CLIENT_ID,
            "client_secret": SOMFY_CLIENT_SECRET,
            "username": username,
            "password": password,
        }
    )
    async with session.post(
        f"{SOMFY_API}/oauth/oauth/v2/token/jwt",
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ) as response:
        await _raise_for_server_error(response)
        token = await response.json()

        if token.get("message") == "error.invalid.grant":
            raise SomfyBadCredentialsError(token["message"])

        if not token.get("access_token"):
            raise SomfyServiceError("No Somfy access token provided.")

        return cast(dict[str, Any], token)


class BaseAuthStrategy(AuthStrategy):
    """Base class for authentication strategies."""

    def __init__(
        self,
        session: ClientSession,
        server: ServerConfig,
        ssl_context: ssl.SSLContext | bool,
    ) -> None:
        """Store shared auth context for Overkiz API interactions."""
        self.session = session
        self.server = server
        self._ssl = ssl_context

    @property
    def endpoint(self) -> str:
        """Return the base API endpoint; defaults to the server endpoint."""
        return self.server.endpoint

    async def login(self) -> None:
        """Perform authentication; default is a no-op for subclasses to override."""
        return

    async def refresh_if_needed(self) -> bool:
        """Refresh authentication tokens if needed; default returns False."""
        return False

    async def auth_headers(self, path: str | None = None) -> Mapping[str, str]:
        """Return authentication headers for a request path."""
        return {}

    async def close(self) -> None:
        """Close any resources held by the strategy; default is no-op."""
        return


class SessionLoginStrategy(BaseAuthStrategy):
    """Authentication strategy using session-based login."""

    def __init__(
        self,
        credentials: UsernamePasswordCredentials,
        session: ClientSession,
        server: ServerConfig,
        ssl_context: ssl.SSLContext | bool,
    ) -> None:
        """Create a session-login strategy bound to the given credentials."""
        super().__init__(session, server, ssl_context)
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
            if response.status not in (HTTPStatus.OK, HTTPStatus.NO_CONTENT):
                raise BadCredentialsError(
                    f"Login failed for {self.server.name}: {response.status}"
                )

            # A 204 No Content response cannot have a body, so skip JSON parsing.
            if response.status == HTTPStatus.NO_CONTENT:
                return

            result = await response.json()
            if not result.get("success"):
                raise BadCredentialsError("Login failed: bad credentials")


class SomfyAuthStrategy(BaseAuthStrategy):
    """Authentication strategy using Somfy OAuth2."""

    def __init__(
        self,
        credentials: UsernamePasswordCredentials,
        session: ClientSession,
        server: ServerConfig,
        ssl_context: ssl.SSLContext | bool,
    ) -> None:
        """Create a Somfy OAuth2 strategy with a fresh auth context."""
        super().__init__(session, server, ssl_context)
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

    async def auth_headers(self, path: str | None = None) -> Mapping[str, str]:
        """Return authentication headers for a request path."""
        if self.context.access_token:
            return {"Authorization": f"Bearer {self.context.access_token}"}

        return {}

    async def _request_access_token(
        self, *, grant_type: str, extra_fields: Mapping[str, str]
    ) -> None:
        if grant_type == "password":
            token = await _somfy_password_token(
                self.session,
                self.credentials.username,
                self.credentials.password,
            )
            self.context.update_from_token(token)
            return

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
            await _raise_for_server_error(response)
            token = await response.json()

            if token.get("message") == "error.invalid.grant":
                raise SomfyBadCredentialsError(token["message"])

            access_token = token.get("access_token")
            if not access_token:
                raise SomfyServiceError("No Somfy access token provided.")

            self.context.update_from_token(token)


class SomfyMultisiteAuthStrategy(BaseAuthStrategy):
    """Somfy multi-site auth: Keycloak token exchange + BOB site directory.

    Reuses the Somfy Accounts password grant, exchanges the SSO token for a
    Ginaite (Keycloak) token, then lists the account's sites from the BOB
    directory. Selecting a site mints a site-scoped token whose Bearer drives
    the classic Overkiz enduser API directly (no gateway header needed).
    """

    def __init__(
        self,
        credentials: UsernamePasswordCredentials,
        session: ClientSession,
        server: ServerConfig,
        ssl_context: ssl.SSLContext | bool,
    ) -> None:
        """Create a Somfy multi-site strategy with a fresh auth context."""
        super().__init__(session, server, ssl_context)
        self.credentials = credentials
        self.context = AuthContext()
        self._sites: list[GatewayCandidate] = []
        self._site_country: dict[str, str] = {}
        self._selected_site_oid: str | None = None
        self._selected_gateway: str | None = None
        self._endpoint: str | None = None

    async def login(self) -> None:
        """Password grant -> token exchange -> discover, auto-select if single."""
        token = await _somfy_password_token(
            self.session, self.credentials.username, self.credentials.password
        )
        await self._token_exchange(token["access_token"])
        await self.discover_gateways()
        if len(self._sites) == 1:
            self.select_gateway(self._sites[0].gateway_id)

    async def _token_exchange(self, sso_access_token: str) -> None:
        """Exchange a Somfy Accounts SSO token for a Ginaite token (public client)."""
        form = FormData(
            {
                "grant_type": GINAITE_TOKEN_EXCHANGE_GRANT,
                "client_id": SOMFY_CLIENT_ID,
                "subject_token": sso_access_token,
                "subject_issuer": GINAITE_SUBJECT_ISSUER,
                "subject_token_type": GINAITE_SUBJECT_TOKEN_TYPE,
            }
        )
        async with self.session.post(GINAITE_TOKEN_URL, data=form) as response:
            await _raise_for_server_error(response)
            if response.status != HTTPStatus.OK:
                raise SomfyServiceError(
                    f"Somfy token exchange failed: {response.status}"
                )
            self.context.update_from_token(await response.json())

    async def discover_gateways(self) -> list[GatewayCandidate]:
        """List the account's sites from BOB, flattened to gateway candidates."""
        data = await self._bob_get("sites?withGateways=true&limit=20&offset=0")
        candidates: list[GatewayCandidate] = []
        self._site_country = {}
        for site in data.get("results", []):
            site_oid = str(site["siteOID"])
            label = site.get("name")
            country = site.get("country")
            for sub in site.get("subSites", []):
                external_id = sub.get("externalOID")
                for gateway in sub.get("gateways", []):
                    gateway_id = str(gateway["gatewayId"])
                    if country is not None:
                        self._site_country[gateway_id] = str(country)
                    candidates.append(
                        GatewayCandidate(
                            gateway_id=gateway_id,
                            home_id=site_oid,
                            label=label,
                            external_id=(
                                str(external_id) if external_id is not None else None
                            ),
                        )
                    )
        self._sites = candidates
        return candidates

    def select_gateway(self, gateway_id: str) -> None:
        """Scope subsequent requests to the given gateway's site and region."""
        site = next(
            (s for s in self._sites if s.gateway_id == gateway_id),
            None,
        )
        if site is None:
            raise SomfyServiceError(f"Unknown gateway id: {gateway_id}")

        country = self._site_country.get(gateway_id)
        if not country:
            raise SomfyServiceError(
                f"No country known for gateway {gateway_id}; cannot resolve region."
            )
        region = self._region_for_country(country)

        self._selected_gateway = gateway_id
        self._selected_site_oid = site.home_id
        self._endpoint = SOMFY_REGION_ENDPOINT[region]
        # Force the next request to mint a site-scoped token via refresh.
        self.context.expires_at = datetime.datetime.now(datetime.UTC)

    def _region_for_country(self, country: str) -> str:
        """Map an ISO country to an Overkiz region, or raise if unmapped."""
        region = SOMFY_COUNTRY_REGION.get(country.upper())
        if region is None:
            raise SomfyServiceError(
                f"No Overkiz region mapped for Somfy site country {country!r}."
            )
        return region

    @property
    def selected_gateway(self) -> str | None:
        """Return the currently selected gateway id, or None."""
        return self._selected_gateway

    @property
    def endpoint(self) -> str:
        """Return the resolved per-site endpoint, or the server placeholder."""
        return self._endpoint or self.server.endpoint

    async def refresh_if_needed(self) -> bool:
        """Mint/refresh a site-scoped token when expired.

        Raises if a site has been selected but there is no refresh token to
        mint the site-scoped token with, rather than silently continuing to
        serve the unscoped global token against the site's region endpoint.
        """
        if not self.context.is_expired():
            return False
        if not self.context.refresh_token:
            if self._selected_site_oid:
                raise SomfyServiceError(
                    "Cannot mint a site-scoped Somfy token without a refresh token."
                )
            return False
        await self._refresh()
        return True

    async def _refresh(self) -> None:
        """Refresh grant scoped to the selected site (?siteOID)."""
        url = GINAITE_TOKEN_URL
        if self._selected_site_oid:
            url = f"{GINAITE_TOKEN_URL}?siteOID={self._selected_site_oid}"
        form = FormData(
            {
                "grant_type": "refresh_token",
                "client_id": SOMFY_CLIENT_ID,
                "refresh_token": cast(str, self.context.refresh_token),
            }
        )
        async with self.session.post(url, data=form) as response:
            await _raise_for_server_error(response)
            if response.status != HTTPStatus.OK:
                raise SomfyServiceError(
                    f"Somfy token refresh failed: {response.status}"
                )
            self.context.update_from_token(await response.json())

    async def auth_headers(self, path: str | None = None) -> Mapping[str, str]:
        """Return the Bearer header (site-scoped token), or {} before login."""
        if self.context.access_token:
            return {"Authorization": f"Bearer {self.context.access_token}"}
        return {}

    async def _bob_get(self, path: str) -> dict[str, Any]:
        """GET a BOB site-directory resource with Bearer + X-Api-Key."""
        async with self.session.get(
            f"{BOB_SITE_API}/{path}",
            headers={
                "Authorization": f"Bearer {self.context.access_token}",
                "X-Api-Key": BOB_API_KEY,
            },
            ssl=self._ssl,
        ) as response:
            await _raise_for_server_error(response)
            if response.status != HTTPStatus.OK:
                raise SomfyServiceError(f"BOB request failed: {response.status}")
            return cast(dict[str, Any], await response.json())


class CozytouchAuthStrategy(SessionLoginStrategy):
    """Authentication strategy using Cozytouch session-based login."""

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
            await _raise_for_server_error(response)
            token = await response.json()

            if token.get("error") == "invalid_grant":
                raise CozyTouchBadCredentialsError(token["error_description"])

            if "token_type" not in token:
                raise CozyTouchServiceError("No CozyTouch token provided.")

        async with self.session.get(
            f"{COZYTOUCH_ATLANTIC_API}/magellan/accounts/jwt",
            headers={"Authorization": f"Bearer {token['access_token']}"},
        ) as response:
            jwt = await response.text()

            if not jwt:
                raise CozyTouchServiceError("No JWT token provided.")

            jwt = jwt.strip('"')

        await self._post_login({"jwt": jwt})


class BrandtAuthStrategy(SessionLoginStrategy):
    """Authentication strategy for Brandt Smart Control.

    Brandt fronts Overkiz with a cookie-session middleware: authenticate
    against smartcontrol-app.com, fetch a JWT using the resulting session
    cookie, then log in to the Overkiz cloud with that JWT. The shared
    aiohttp session carries the cookie between the two middleware calls.
    """

    async def login(self) -> None:
        """Perform the Brandt middleware login, then Overkiz JWT login."""
        # 1) Middleware session login (sets the devise session cookie).
        async with self.session.post(
            f"{BRANDT_MIDDLEWARE_API}/api/v1/sessions.json",
            json={
                "client": {
                    "email": self.credentials.username,
                    "password": self.credentials.password,
                    "partner": BRANDT_PARTNER,
                }
            },
            ssl=self._ssl,
        ) as response:
            if response.status >= HTTPStatus.BAD_REQUEST:
                message = "Login failed: bad credentials"
                try:
                    body = await response.json()
                    errors = body.get("error")
                    if errors:
                        message = errors[0]
                except ValueError:
                    pass
                raise BrandtBadCredentialsError(message)

        # 2) Fetch the JWT, authenticated purely by the session cookie.
        async with self.session.get(
            f"{BRANDT_MIDDLEWARE_API}/api/v1/profile/jwt.json",
            ssl=self._ssl,
        ) as response:
            if response.status >= HTTPStatus.BAD_REQUEST:
                raise BrandtServiceError(
                    f"Brandt JWT request failed: {response.status}"
                )
            body = await response.json()
            jwt = body.get("client", {}).get("jwt")

        if not jwt:
            raise BrandtServiceError("No Brandt JWT token provided.")

        # 3) Overkiz cloud login with the JWT only (no apiKey/applicationId).
        await self._post_login({"jwt": jwt})


class NexityAuthStrategy(SessionLoginStrategy):
    """Authentication strategy using Nexity session-based login."""

    async def login(self) -> None:
        """Perform login using Nexity username and password."""
        try:
            import boto3
            from botocore.config import Config
            from botocore.exceptions import ClientError
            from warrant_lite import WarrantLite
        except ImportError as err:
            raise ImportError(
                "Nexity authentication requires the 'nexity' extra. "
                'Install it with: pip install "pyoverkiz[nexity]"'
            ) from err

        loop = asyncio.get_running_loop()

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
        except ClientError as error:
            code = error.response.get("Error", {}).get("Code")
            if code in {"NotAuthorizedException", "UserNotFoundException"}:
                raise NexityBadCredentialsError from error
            raise

        id_token = tokens["AuthenticationResult"]["IdToken"]

        async with self.session.get(
            f"{NEXITY_API}/deploy/api/v1/domotic/token",
            headers={"Authorization": id_token},
        ) as response:
            await _raise_for_server_error(response)
            token = await response.json()

            if "token" not in token:
                raise NexityServiceError("No Nexity SSO token provided.")

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
    ) -> None:
        """Create a local-token strategy bound to the given credentials."""
        super().__init__(session, server, ssl_context)
        self.credentials = credentials

    async def login(self) -> None:
        """Validate that a token is provided for local API access."""
        if not self.credentials.token:
            raise InvalidTokenError("Local API requires a token.")

    async def auth_headers(self, path: str | None = None) -> Mapping[str, str]:
        """Return authentication headers for a request path."""
        return {"Authorization": f"Bearer {self.credentials.token}"}


class RexelGatewayMixin:
    """Shared Rexel gateway discovery/selection for Rexel auth strategies.

    The only per-strategy difference is how the access token is obtained,
    supplied by overriding ``_current_access_token``.
    """

    session: ClientSession
    _ssl: ssl.SSLContext | bool
    _gateway_id: str | None

    async def _current_access_token(self) -> str | None:
        """Return the current access token. Overridden per strategy."""
        raise NotImplementedError

    async def discover_gateways(self) -> list[GatewayCandidate]:
        """Enumerate every home x gateway available to this account."""
        candidates: list[GatewayCandidate] = []
        for home in await self._get_enduser("homes"):
            home_id = str(home["id"])
            home_label = home.get("label")
            for gateway in await self._get_enduser(f"overkizgateways?homeId={home_id}"):
                external_id = gateway.get("externalId")
                candidates.append(
                    GatewayCandidate(
                        gateway_id=str(gateway["gatewayId"]),
                        home_id=home_id,
                        label=home_label,
                        external_id=(
                            str(external_id) if external_id is not None else None
                        ),
                    )
                )
        return candidates

    def select_gateway(self, gateway_id: str) -> None:
        """Select the gateway to scope subsequent requests to.

        The caller is responsible for passing a ``gateway_id`` obtained from
        ``discover_gateways()``; an unknown id is only rejected server-side on
        the next request.
        """
        self._gateway_id = gateway_id

    @property
    def selected_gateway(self) -> str | None:
        """Return the currently selected gateway id, or None."""
        return self._gateway_id

    async def _get_enduser(self, path: str) -> list[dict[str, Any]]:
        """GET a Rexel directory resource (homes/gateways) with Bearer auth.

        Uses REXEL_ENDUSER_API, NOT the device endpoint, and a Bearer-only
        header so it works before a gateway has been selected.
        """
        async with self.session.get(
            f"{REXEL_ENDUSER_API}/{path}",
            headers={"Authorization": f"Bearer {await self._current_access_token()}"},
            ssl=self._ssl,
        ) as response:
            await check_response(response)
            return cast(list[dict[str, Any]], await response.json())

    def _gateway_headers(self) -> dict[str, str]:
        """Return the gatewayId header; raise if no gateway is selected."""
        if self._gateway_id is None:
            raise NoGatewaySelectedError(
                "Multiple Rexel gateways available; call discover_gateways() "
                "and select_gateway() before making requests."
            )
        return {REXEL_GATEWAY_HEADER: self._gateway_id}

    async def auth_headers(self, path: str | None = None) -> Mapping[str, str]:
        """Return Bearer + gatewayId headers, or {} before a token exists."""
        token = await self._current_access_token()
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}", **self._gateway_headers()}


class RexelAuthStrategy(RexelGatewayMixin, BaseAuthStrategy):
    """Authentication strategy using Rexel OAuth2 code exchange."""

    def __init__(
        self,
        credentials: RexelOAuthCodeCredentials,
        session: ClientSession,
        server: ServerConfig,
        ssl_context: ssl.SSLContext | bool,
    ) -> None:
        """Create a Rexel OAuth2 strategy with a fresh auth context."""
        super().__init__(session, server, ssl_context)
        self.credentials = credentials
        self.context = AuthContext()
        self._gateway_id: str | None = None

    async def _current_access_token(self) -> str | None:
        """Return the access token from the OAuth2 code-exchange context."""
        return self.context.access_token

    async def login(self) -> None:
        """Exchange the authorization code, then auto-select a sole gateway."""
        await self._exchange_token(
            {
                "grant_type": "authorization_code",
                "client_id": REXEL_OAUTH_CLIENT_ID,
                "scope": REXEL_OAUTH_SCOPE,
                "code": self.credentials.code,
                "redirect_uri": self.credentials.redirect_uri,
                "code_verifier": self.credentials.code_verifier,
            }
        )
        gateways = await self.discover_gateways()
        if len(gateways) == 1:
            self.select_gateway(gateways[0].gateway_id)

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

    async def _exchange_token(self, payload: Mapping[str, str]) -> None:
        """Exchange authorization code or refresh token for access token."""
        async with self.session.post(
            REXEL_OAUTH_TOKEN_URL,
            data=payload,
        ) as response:
            await _raise_for_server_error(response)
            token = await response.json()

            # Handle OAuth error responses explicitly before accessing the access token.
            error = token.get("error")
            if error:
                description = token.get("error_description") or token.get("message")
                if description:
                    raise InvalidTokenError(
                        f"Error retrieving Rexel access token: {description}"
                    )
                raise InvalidTokenError(f"Error retrieving Rexel access token: {error}")

            access_token = token.get("access_token")
            if not access_token:
                raise InvalidTokenError("No Rexel access token provided.")

            self._ensure_consent(access_token)
            self.context.update_from_token(token)

    @staticmethod
    def _ensure_consent(access_token: str) -> None:
        """Ensure that the Rexel token has the required consent."""
        payload = _decode_jwt_payload(access_token)
        consent = payload.get("consent")
        if consent != REXEL_REQUIRED_CONSENT:
            raise InvalidTokenError("Consent is missing or revoked for Rexel token.")


class RexelTokenAuthStrategy(RexelGatewayMixin, BaseAuthStrategy):
    """Rexel strategy backed by an externally-managed access token.

    The OAuth2 lifecycle (authorize, exchange, refresh, persistence) is owned
    by the caller. This strategy only sources the current token and applies the
    Rexel gateway selection + header logic from RexelGatewayMixin.
    """

    def __init__(
        self,
        credentials: RexelTokenCredentials,
        session: ClientSession,
        server: ServerConfig,
        ssl_context: ssl.SSLContext | bool,
    ) -> None:
        """Create a token-backed Rexel strategy bound to the credentials."""
        super().__init__(session, server, ssl_context)
        self.credentials = credentials
        self._gateway_id: str | None = None

    async def login(self) -> None:
        """Apply a stored gateway, or auto-select a sole discovered gateway."""
        if self.credentials.gateway_id:
            self.select_gateway(self.credentials.gateway_id)
            return
        gateways = await self.discover_gateways()
        if len(gateways) == 1:
            self.select_gateway(gateways[0].gateway_id)

    async def _current_access_token(self) -> str | None:
        """Return a token from the callback, or the static fallback."""
        if self.credentials.access_token_callback:
            return await self.credentials.access_token_callback()
        return self.credentials.access_token


class BearerTokenAuthStrategy(BaseAuthStrategy):
    """Authentication strategy using a static bearer token."""

    def __init__(
        self,
        credentials: TokenCredentials,
        session: ClientSession,
        server: ServerConfig,
        ssl_context: ssl.SSLContext | bool,
    ) -> None:
        """Create a bearer-token strategy bound to the given credentials."""
        super().__init__(session, server, ssl_context)
        self.credentials = credentials

    async def auth_headers(self, path: str | None = None) -> Mapping[str, str]:
        """Return authentication headers for a request path."""
        if self.credentials.token:
            return {"Authorization": f"Bearer {self.credentials.token}"}
        return {}


def _decode_jwt_payload(token: str) -> dict[str, Any]:
    """Decode the payload of a JWT token."""
    parts = token.split(".")
    if len(parts) < MIN_JWT_SEGMENTS:
        raise InvalidTokenError("Malformed JWT received.")

    payload_segment = parts[1]
    padding = "=" * (-len(payload_segment) % 4)
    try:
        decoded = base64.urlsafe_b64decode(payload_segment + padding)
        return cast(dict[str, Any], json.loads(decoded))
    except (binascii.Error, json.JSONDecodeError) as error:
        raise InvalidTokenError("Malformed JWT received.") from error
