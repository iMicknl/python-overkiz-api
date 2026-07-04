"""Tests for authentication module."""

# ruff: noqa: S105, S106, S107
# S105/S106/S107: Test credentials use dummy values.

from __future__ import annotations

import base64
import datetime
import importlib.util
import json
import logging
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientSession

from pyoverkiz.auth.base import AuthContext
from pyoverkiz.auth.credentials import (
    LocalTokenCredentials,
    RexelOAuthCodeCredentials,
    RexelTokenCredentials,
    TokenCredentials,
    UsernamePasswordCredentials,
)
from pyoverkiz.auth.factory import (
    _ensure_credentials,
    build_auth_strategy,
)
from pyoverkiz.auth.strategies import (
    BearerTokenAuthStrategy,
    CozytouchAuthStrategy,
    LocalTokenAuthStrategy,
    NexityAuthStrategy,
    RexelAuthStrategy,
    RexelTokenAuthStrategy,
    SessionLoginStrategy,
    SomfyAuthStrategy,
    _decode_jwt_payload,
)
from pyoverkiz.enums import APIType, Server
from pyoverkiz.exceptions import (
    InvalidTokenError,
    NexityBadCredentialsError,
    NoGatewaySelectedError,
)
from pyoverkiz.models import ServerConfig

HAS_NEXITY_DEPS = importlib.util.find_spec("boto3") is not None

if HAS_NEXITY_DEPS:
    from botocore.exceptions import ClientError


class TestAuthContext:
    """Test AuthContext functionality."""

    def test_not_expired_no_expiration(self):
        """Test that context without expiration is not expired."""
        context = AuthContext(access_token="test_token")
        assert not context.is_expired()

    def test_not_expired_future_expiration(self):
        """Test that context with future expiration is not expired."""
        future = datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)
        context = AuthContext(access_token="test_token", expires_at=future)
        assert not context.is_expired()

    def test_expired_past_expiration(self):
        """Test that context with past expiration is expired."""
        past = datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=1)
        context = AuthContext(access_token="test_token", expires_at=past)
        assert context.is_expired()

    def test_expired_with_skew(self):
        """Test that context respects skew time."""
        # Expires in 3 seconds, but default skew is 5
        soon = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=3)
        context = AuthContext(access_token="test_token", expires_at=soon)
        assert context.is_expired()

    def test_not_expired_with_custom_skew(self):
        """Test that custom skew time can be provided."""
        soon = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=3)
        context = AuthContext(access_token="test_token", expires_at=soon)
        assert not context.is_expired(skew_seconds=1)


class TestCredentials:
    """Test credential dataclasses."""

    def test_username_password_credentials(self):
        """Test UsernamePasswordCredentials creation."""
        creds = UsernamePasswordCredentials("user@example.com", "password123")
        assert creds.username == "user@example.com"
        assert creds.password == "password123"

    def test_token_credentials(self):
        """Test TokenCredentials creation."""
        creds = TokenCredentials("my_token_123")
        assert creds.token == "my_token_123"

    def test_local_token_credentials(self):
        """Test LocalTokenCredentials creation."""
        creds = LocalTokenCredentials("local_token_456")
        assert creds.token == "local_token_456"
        assert isinstance(creds, TokenCredentials)

    def test_rexel_oauth_credentials(self):
        """Test RexelOAuthCodeCredentials creation."""
        creds = RexelOAuthCodeCredentials(
            "auth_code_xyz", "http://redirect.uri", "code_verifier_123"
        )
        assert creds.code == "auth_code_xyz"
        assert creds.redirect_uri == "http://redirect.uri"
        assert creds.code_verifier == "code_verifier_123"

    def test_rexel_token_credentials_with_static_token(self):
        """RexelTokenCredentials accepts a static access token."""
        creds = RexelTokenCredentials(access_token="static-token")
        assert creds.access_token == "static-token"
        assert creds.access_token_callback is None
        assert creds.gateway_id is None

    def test_rexel_token_credentials_with_callback(self):
        """RexelTokenCredentials accepts an async access-token callback."""

        async def _token() -> str:
            return "fresh-token"

        creds = RexelTokenCredentials(access_token_callback=_token, gateway_id="g1")
        assert creds.access_token_callback is _token
        assert creds.gateway_id == "g1"
        assert creds.access_token is None

    def test_rexel_token_credentials_requires_a_token_source(self):
        """Constructing with neither callback nor static token raises ValueError."""
        with pytest.raises(ValueError, match="access_token_callback or access_token"):
            RexelTokenCredentials()


def test_brandt_constants_and_exceptions():
    """Brandt middleware constants and exceptions are exported correctly."""
    from pyoverkiz.const import BRANDT_MIDDLEWARE_API, BRANDT_PARTNER
    from pyoverkiz.exceptions import (
        BadCredentialsError,
        BaseOverkizError,
        BrandtBadCredentialsError,
        BrandtServiceError,
    )

    assert BRANDT_MIDDLEWARE_API == "https://www.smartcontrol-app.com"
    assert BRANDT_PARTNER == "brandt-electromenager"
    assert issubclass(BrandtBadCredentialsError, BadCredentialsError)
    assert issubclass(BrandtServiceError, BaseOverkizError)


class TestAuthFactory:
    """Test authentication factory functions."""

    def test_ensure_credentials_username_password_valid(self):
        """Test that valid username/password credentials pass validation."""
        creds = UsernamePasswordCredentials("user", "pass")
        result = _ensure_credentials(creds, UsernamePasswordCredentials)
        assert result is creds

    def test_ensure_credentials_username_password_invalid(self):
        """Test that invalid credentials raise TypeError."""
        creds = TokenCredentials("token")
        with pytest.raises(TypeError, match="UsernamePasswordCredentials are required"):
            _ensure_credentials(creds, UsernamePasswordCredentials)

    def test_ensure_credentials_token_valid(self):
        """Test that valid token credentials pass validation."""
        creds = TokenCredentials("token")
        result = _ensure_credentials(creds, TokenCredentials)
        assert result is creds

    def test_ensure_credentials_token_local_valid(self):
        """Test that LocalTokenCredentials also pass token validation."""
        creds = LocalTokenCredentials("local_token")
        result = _ensure_credentials(creds, TokenCredentials)
        assert result is creds

    def test_ensure_credentials_token_invalid(self):
        """Test that invalid credentials raise TypeError."""
        creds = UsernamePasswordCredentials("user", "pass")
        with pytest.raises(TypeError, match="TokenCredentials are required"):
            _ensure_credentials(creds, TokenCredentials)

    def test_ensure_credentials_rexel_valid(self):
        """Test that valid Rexel credentials pass validation."""
        creds = RexelOAuthCodeCredentials("code", "uri", "verifier")
        result = _ensure_credentials(creds, RexelOAuthCodeCredentials)
        assert result is creds

    def test_ensure_credentials_rexel_invalid(self):
        """Test that invalid credentials raise TypeError."""
        creds = UsernamePasswordCredentials("user", "pass")
        with pytest.raises(TypeError, match="RexelOAuthCodeCredentials are required"):
            _ensure_credentials(creds, RexelOAuthCodeCredentials)

    @pytest.mark.asyncio
    async def test_build_auth_strategy_somfy(self):
        """Test building Somfy auth strategy."""
        server_config = ServerConfig(
            server=Server.SOMFY_EUROPE,
            name="Somfy",
            endpoint="https://api.somfy.com",
            manufacturer="Somfy",
            api_type=APIType.CLOUD,
        )
        credentials = UsernamePasswordCredentials("user", "pass")
        session = AsyncMock(spec=ClientSession)

        strategy = build_auth_strategy(
            server_config=server_config,
            credentials=credentials,
            session=session,
            ssl_context=True,
        )

        assert isinstance(strategy, SomfyAuthStrategy)

    @pytest.mark.asyncio
    async def test_build_auth_strategy_somfy_multisite(self):
        """Server.SOMFY + username/password builds SomfyMultisiteAuthStrategy."""
        from pyoverkiz.auth.strategies import SomfyMultisiteAuthStrategy
        from pyoverkiz.const import SUPPORTED_SERVERS

        strategy = build_auth_strategy(
            server_config=SUPPORTED_SERVERS[Server.SOMFY],
            credentials=UsernamePasswordCredentials("user", "pass"),
            session=AsyncMock(spec=ClientSession),
            ssl_context=True,
        )

        assert isinstance(strategy, SomfyMultisiteAuthStrategy)

    @pytest.mark.asyncio
    async def test_build_auth_strategy_cozytouch(self):
        """Test building Cozytouch auth strategy."""
        server_config = ServerConfig(
            server=Server.ATLANTIC_COZYTOUCH,
            name="Cozytouch",
            endpoint="https://api.cozytouch.com",
            manufacturer="Atlantic",
            api_type=APIType.CLOUD,
        )
        credentials = UsernamePasswordCredentials("user", "pass")
        session = AsyncMock(spec=ClientSession)

        strategy = build_auth_strategy(
            server_config=server_config,
            credentials=credentials,
            session=session,
            ssl_context=True,
        )

        assert isinstance(strategy, CozytouchAuthStrategy)

    @pytest.mark.asyncio
    async def test_build_auth_strategy_brandt(self):
        """Test building Brandt auth strategy."""
        from pyoverkiz.auth.strategies import BrandtAuthStrategy

        server_config = ServerConfig(
            server=Server.BRANDT,
            name="Brandt Smart Control",
            endpoint="https://ha3-1.overkiz.com/enduser-mobile-web/enduserAPI/",
            manufacturer="Brandt",
            api_type=APIType.CLOUD,
        )
        credentials = UsernamePasswordCredentials("user", "pass")
        session = AsyncMock(spec=ClientSession)

        strategy = build_auth_strategy(
            server_config=server_config,
            credentials=credentials,
            session=session,
            ssl_context=True,
        )

        assert isinstance(strategy, BrandtAuthStrategy)

    @pytest.mark.asyncio
    async def test_build_auth_strategy_nexity(self):
        """Test building Nexity auth strategy."""
        server_config = ServerConfig(
            server=Server.NEXITY,
            name="Nexity",
            endpoint="https://api.nexity.com",
            manufacturer="Nexity",
            api_type=APIType.CLOUD,
        )
        credentials = UsernamePasswordCredentials("user", "pass")
        session = AsyncMock(spec=ClientSession)

        strategy = build_auth_strategy(
            server_config=server_config,
            credentials=credentials,
            session=session,
            ssl_context=True,
        )

        assert isinstance(strategy, NexityAuthStrategy)

    @pytest.mark.asyncio
    async def test_build_auth_strategy_rexel(self):
        """Test building Rexel auth strategy."""
        server_config = ServerConfig(
            server=Server.REXEL,
            name="Rexel",
            endpoint="https://api.rexel.com",
            manufacturer="Rexel",
            api_type=APIType.CLOUD,
        )
        credentials = RexelOAuthCodeCredentials(
            "code", "http://redirect.uri", "verifier"
        )
        session = AsyncMock(spec=ClientSession)

        strategy = build_auth_strategy(
            server_config=server_config,
            credentials=credentials,
            session=session,
            ssl_context=True,
        )

        assert isinstance(strategy, RexelAuthStrategy)

    @pytest.mark.asyncio
    async def test_build_auth_strategy_rexel_token(self):
        """RexelTokenCredentials build a RexelTokenAuthStrategy for Rexel."""
        server_config = ServerConfig(
            server=Server.REXEL,
            name="Rexel",
            endpoint="https://api.rexel.com",
            manufacturer="Rexel",
            api_type=APIType.CLOUD,
        )
        credentials = RexelTokenCredentials(access_token="static-token")
        session = AsyncMock(spec=ClientSession)

        strategy = build_auth_strategy(
            server_config=server_config,
            credentials=credentials,
            session=session,
            ssl_context=True,
        )

        assert isinstance(strategy, RexelTokenAuthStrategy)

    @pytest.mark.asyncio
    async def test_build_auth_strategy_rexel_code_still_works(self):
        """RexelOAuthCodeCredentials still build the code-exchange strategy."""
        server_config = ServerConfig(
            server=Server.REXEL,
            name="Rexel",
            endpoint="https://api.rexel.com",
            manufacturer="Rexel",
            api_type=APIType.CLOUD,
        )
        credentials = RexelOAuthCodeCredentials("code", "uri", "verifier")
        session = AsyncMock(spec=ClientSession)

        strategy = build_auth_strategy(
            server_config=server_config,
            credentials=credentials,
            session=session,
            ssl_context=True,
        )

        assert isinstance(strategy, RexelAuthStrategy)

    @pytest.mark.asyncio
    async def test_build_auth_strategy_local_token(self):
        """Test building local token auth strategy."""
        server_config = ServerConfig(
            server=None,
            name="Local",
            endpoint="https://gateway.local",
            manufacturer="Overkiz",
            api_type=APIType.LOCAL,
        )
        credentials = LocalTokenCredentials("local_token")
        session = AsyncMock(spec=ClientSession)

        strategy = build_auth_strategy(
            server_config=server_config,
            credentials=credentials,
            session=session,
            ssl_context=True,
        )

        assert isinstance(strategy, LocalTokenAuthStrategy)

    @pytest.mark.asyncio
    async def test_build_auth_strategy_local_token_with_cloud_server(self):
        """A local config keeps local routing even when server is a cloud id.

        Local API routing keys off api_type, so a config labelled with a
        cloud-mapped server (e.g. Server.REXEL) must still select the local
        token strategy rather than the Rexel OAuth strategy.
        """
        server_config = ServerConfig(
            server=Server.REXEL,
            name="Rexel Energeasy Connect (local)",
            endpoint="https://gateway.local",
            manufacturer="Rexel",
            api_type=APIType.LOCAL,
        )
        credentials = LocalTokenCredentials("local_token")
        session = AsyncMock(spec=ClientSession)

        strategy = build_auth_strategy(
            server_config=server_config,
            credentials=credentials,
            session=session,
            ssl_context=True,
        )

        assert isinstance(strategy, LocalTokenAuthStrategy)

    @pytest.mark.asyncio
    async def test_build_auth_strategy_local_bearer(self):
        """Test building local bearer token auth strategy."""
        server_config = ServerConfig(
            server=None,
            name="Local",
            endpoint="https://gateway.local",
            manufacturer="Overkiz",
            api_type=APIType.LOCAL,
        )
        credentials = TokenCredentials("bearer_token")
        session = AsyncMock(spec=ClientSession)

        strategy = build_auth_strategy(
            server_config=server_config,
            credentials=credentials,
            session=session,
            ssl_context=True,
        )

        assert isinstance(strategy, BearerTokenAuthStrategy)

    @pytest.mark.asyncio
    async def test_build_auth_strategy_cloud_bearer(self):
        """Test building cloud bearer token auth strategy."""
        server_config = ServerConfig(
            server=Server.SOMFY_OCEANIA,
            name="Somfy Oceania",
            endpoint="https://api.somfy.com.au",
            manufacturer="Somfy",
            api_type=APIType.CLOUD,
        )
        credentials = TokenCredentials("bearer_token")
        session = AsyncMock(spec=ClientSession)

        strategy = build_auth_strategy(
            server_config=server_config,
            credentials=credentials,
            session=session,
            ssl_context=True,
        )

        assert isinstance(strategy, BearerTokenAuthStrategy)

    @pytest.mark.asyncio
    async def test_build_auth_strategy_session_login(self):
        """Test building generic session login auth strategy."""
        server_config = ServerConfig(
            server=Server.SOMFY_OCEANIA,
            name="Somfy Oceania",
            endpoint="https://api.somfy.com.au",
            manufacturer="Somfy",
            api_type=APIType.CLOUD,
        )
        credentials = UsernamePasswordCredentials("user", "pass")
        session = AsyncMock(spec=ClientSession)

        strategy = build_auth_strategy(
            server_config=server_config,
            credentials=credentials,
            session=session,
            ssl_context=True,
        )

        assert isinstance(strategy, SessionLoginStrategy)

    @pytest.mark.asyncio
    async def test_build_auth_strategy_wrong_credentials_type(self):
        """Test that wrong credentials type raises TypeError."""
        server_config = ServerConfig(
            server=Server.SOMFY_EUROPE,
            name="Somfy",
            endpoint="https://api.somfy.com",
            manufacturer="Somfy",
            api_type=APIType.CLOUD,
        )
        credentials = TokenCredentials("token")  # Wrong type for Somfy
        session = AsyncMock(spec=ClientSession)

        with pytest.raises(TypeError, match="UsernamePasswordCredentials are required"):
            build_auth_strategy(
                server_config=server_config,
                credentials=credentials,
                session=session,
                ssl_context=True,
            )


class TestSessionLoginStrategy:
    """Test SessionLoginStrategy."""

    @pytest.mark.asyncio
    async def test_login_success(self):
        """Test successful login with 200 response."""
        server_config = ServerConfig(
            server=Server.SOMFY_OCEANIA,
            name="Test",
            endpoint="https://api.test.com/",
            manufacturer="Test",
            api_type=APIType.CLOUD,
        )
        credentials = UsernamePasswordCredentials("user", "pass")
        session = AsyncMock(spec=ClientSession)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"success": True})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        session.post = MagicMock(return_value=mock_response)

        strategy = SessionLoginStrategy(credentials, session, server_config, True)
        await strategy.login()

        session.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_204_no_content(self):
        """Test login with 204 No Content response."""
        server_config = ServerConfig(
            server=Server.SOMFY_OCEANIA,
            name="Test",
            endpoint="https://api.test.com/",
            manufacturer="Test",
            api_type=APIType.CLOUD,
        )
        credentials = UsernamePasswordCredentials("user", "pass")
        session = AsyncMock(spec=ClientSession)

        mock_response = MagicMock()
        mock_response.status = 204
        mock_response.json = AsyncMock()
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        session.post = MagicMock(return_value=mock_response)

        strategy = SessionLoginStrategy(credentials, session, server_config, True)
        await strategy.login()

        # Should not call json() for 204 response
        assert not mock_response.json.called

    @pytest.mark.asyncio
    async def test_refresh_if_needed_no_refresh(self):
        """Test that refresh_if_needed returns False when no refresh needed."""
        server_config = ServerConfig(
            server=Server.SOMFY_OCEANIA,
            name="Test",
            endpoint="https://api.test.com/",
            manufacturer="Test",
            api_type=APIType.CLOUD,
        )
        credentials = UsernamePasswordCredentials("user", "pass")
        session = AsyncMock(spec=ClientSession)

        strategy = SessionLoginStrategy(credentials, session, server_config, True)
        result = await strategy.refresh_if_needed()

        assert not result

    @pytest.mark.asyncio
    async def test_auth_headers_no_token(self):
        """Test that auth headers return empty dict when no token."""
        server_config = ServerConfig(
            server=Server.SOMFY_OCEANIA,
            name="Test",
            endpoint="https://api.test.com/",
            manufacturer="Test",
            api_type=APIType.CLOUD,
        )
        credentials = UsernamePasswordCredentials("user", "pass")
        session = AsyncMock(spec=ClientSession)

        strategy = SessionLoginStrategy(credentials, session, server_config, True)
        headers = await strategy.auth_headers()

        assert headers == {}


class TestBrandtAuthStrategy:
    """Test BrandtAuthStrategy."""

    @staticmethod
    def _server_config():
        return ServerConfig(
            server=Server.BRANDT,
            name="Brandt Smart Control",
            endpoint="https://ha3-1.overkiz.com/enduser-mobile-web/enduserAPI/",
            manufacturer="Brandt",
            api_type=APIType.CLOUD,
        )

    @staticmethod
    def _json_response(status, payload):
        resp = MagicMock()
        resp.status = status
        resp.json = AsyncMock(return_value=payload)
        resp.__aenter__ = AsyncMock(return_value=resp)
        resp.__aexit__ = AsyncMock(return_value=None)
        return resp

    @pytest.mark.asyncio
    async def test_login_success_flow(self):
        """Full flow: sessions.json -> profile/jwt.json -> Overkiz login."""
        from pyoverkiz.auth.strategies import BrandtAuthStrategy

        session = AsyncMock(spec=ClientSession)
        # 1) POST sessions.json  2) Overkiz POST login (inherited _post_login)
        session.post = MagicMock(
            side_effect=[
                self._json_response(200, {"client": {"email": "a@b.c"}}),
                self._json_response(200, {"success": True}),
            ]
        )
        # GET profile/jwt.json
        session.get = MagicMock(
            return_value=self._json_response(200, {"client": {"jwt": "the.jwt.token"}})
        )

        credentials = UsernamePasswordCredentials("a@b.c", "pass")
        strategy = BrandtAuthStrategy(credentials, session, self._server_config(), True)
        await strategy.login()

        # First POST is to the middleware with the partner field.
        first_post = session.post.call_args_list[0]
        assert (
            first_post.args[0]
            == "https://www.smartcontrol-app.com/api/v1/sessions.json"
        )
        assert first_post.kwargs["json"] == {
            "client": {
                "email": "a@b.c",
                "password": "pass",
                "partner": "brandt-electromenager",
            }
        }
        # JWT fetched from the cookie-authenticated GET.
        session.get.assert_called_once_with(
            "https://www.smartcontrol-app.com/api/v1/profile/jwt.json", ssl=True
        )
        # Final POST is the Overkiz login carrying only the jwt.
        last_post = session.post.call_args_list[-1]
        assert last_post.args[0] == (
            "https://ha3-1.overkiz.com/enduser-mobile-web/enduserAPI/login"
        )
        assert last_post.kwargs["data"] == {"jwt": "the.jwt.token"}

    @pytest.mark.asyncio
    async def test_login_bad_credentials(self):
        """A wrong-password 400 from sessions.json raises BrandtBadCredentialsError.

        Pins the real middleware contract: status 400 with an ``error`` array;
        the first element is surfaced as the exception message.
        """
        from pyoverkiz.auth.strategies import BrandtAuthStrategy
        from pyoverkiz.exceptions import BrandtBadCredentialsError

        session = AsyncMock(spec=ClientSession)
        session.post = MagicMock(
            return_value=self._json_response(
                400, {"error": ["Password wrong password"], "status": 400}
            )
        )

        credentials = UsernamePasswordCredentials("a@b.c", "wrong")
        strategy = BrandtAuthStrategy(credentials, session, self._server_config(), True)
        with pytest.raises(BrandtBadCredentialsError, match="Password wrong password"):
            await strategy.login()

    @pytest.mark.asyncio
    async def test_login_missing_jwt_raises_service_error(self):
        """Login OK but no jwt in the profile response -> BrandtServiceError."""
        from pyoverkiz.auth.strategies import BrandtAuthStrategy
        from pyoverkiz.exceptions import BrandtServiceError

        session = AsyncMock(spec=ClientSession)
        session.post = MagicMock(return_value=self._json_response(200, {"client": {}}))
        session.get = MagicMock(return_value=self._json_response(200, {"client": {}}))

        credentials = UsernamePasswordCredentials("a@b.c", "pass")
        strategy = BrandtAuthStrategy(credentials, session, self._server_config(), True)
        with pytest.raises(BrandtServiceError):
            await strategy.login()


class TestBearerTokenAuthStrategy:
    """Test BearerTokenAuthStrategy."""

    @pytest.mark.asyncio
    async def test_login_no_op(self):
        """Test that login is a no-op for bearer tokens."""
        server_config = ServerConfig(
            server=None,
            name="Test",
            endpoint="https://api.test.com/",
            manufacturer="Test",
            api_type=APIType.CLOUD,
        )
        credentials = TokenCredentials("my_bearer_token")
        session = AsyncMock(spec=ClientSession)

        strategy = BearerTokenAuthStrategy(credentials, session, server_config, True)
        result = await strategy.login()

        # Login should be a no-op
        assert result is None

    @pytest.mark.asyncio
    async def test_auth_headers_with_token(self):
        """Test that auth headers include Bearer token."""
        server_config = ServerConfig(
            server=None,
            name="Test",
            endpoint="https://api.test.com/",
            manufacturer="Test",
            api_type=APIType.CLOUD,
        )
        credentials = TokenCredentials("my_bearer_token")
        session = AsyncMock(spec=ClientSession)

        strategy = BearerTokenAuthStrategy(credentials, session, server_config, True)
        headers = await strategy.auth_headers()

        assert headers == {"Authorization": "Bearer my_bearer_token"}


class TestNexityAuthStrategy:
    """Tests for Nexity auth error mapping behavior."""

    def test_boto3_not_imported_at_module_load(self):
        """Verify boto3 and warrant_lite are lazy-imported, not at module load."""
        saved = {}
        for mod in ("boto3", "botocore", "warrant_lite"):
            saved[mod] = sys.modules.pop(mod, None)

        try:
            import importlib

            import pyoverkiz.auth.strategies

            importlib.reload(pyoverkiz.auth.strategies)

            assert "boto3" not in sys.modules
            assert "warrant_lite" not in sys.modules
        finally:
            for mod, value in saved.items():
                if value is not None:
                    sys.modules[mod] = value

    @pytest.mark.asyncio
    async def test_login_raises_import_error_without_nexity_extra(self):
        """Login raises ImportError with install hint when nexity extra is missing."""
        server_config = ServerConfig(
            server=Server.NEXITY,
            name="Nexity",
            endpoint="https://api.nexity.com",
            manufacturer="Nexity",
            api_type=APIType.CLOUD,
        )
        credentials = UsernamePasswordCredentials("user", "pass")
        session = AsyncMock(spec=ClientSession)

        strategy = NexityAuthStrategy(credentials, session, server_config, True)

        with (
            patch.dict(sys.modules, {"boto3": None}),
            pytest.raises(ImportError, match="pyoverkiz\\[nexity\\]"),
        ):
            await strategy.login()

    @pytest.mark.asyncio
    @pytest.mark.skipif(not HAS_NEXITY_DEPS, reason="nexity extra not installed")
    async def test_login_maps_invalid_credentials_client_error(self):
        """Map Cognito bad-credential errors to NexityBadCredentialsError."""
        server_config = ServerConfig(
            server=Server.NEXITY,
            name="Nexity",
            endpoint="https://api.nexity.com",
            manufacturer="Nexity",
            api_type=APIType.CLOUD,
        )
        credentials = UsernamePasswordCredentials("user", "pass")
        session = AsyncMock(spec=ClientSession)

        bad_credentials_error = ClientError(
            error_response={"Error": {"Code": "NotAuthorizedException"}},
            operation_name="InitiateAuth",
        )
        warrant_instance = MagicMock()
        warrant_instance.authenticate_user.side_effect = bad_credentials_error

        with (
            patch("boto3.client", return_value=MagicMock()),
            patch("warrant_lite.WarrantLite", return_value=warrant_instance),
        ):
            strategy = NexityAuthStrategy(credentials, session, server_config, True)
            with pytest.raises(NexityBadCredentialsError):
                await strategy.login()

    @pytest.mark.asyncio
    @pytest.mark.skipif(not HAS_NEXITY_DEPS, reason="nexity extra not installed")
    async def test_login_propagates_non_auth_client_error(self):
        """Propagate non-auth Cognito errors to preserve failure context."""
        server_config = ServerConfig(
            server=Server.NEXITY,
            name="Nexity",
            endpoint="https://api.nexity.com",
            manufacturer="Nexity",
            api_type=APIType.CLOUD,
        )
        credentials = UsernamePasswordCredentials("user", "pass")
        session = AsyncMock(spec=ClientSession)

        service_error = ClientError(
            error_response={"Error": {"Code": "InternalErrorException"}},
            operation_name="InitiateAuth",
        )
        warrant_instance = MagicMock()
        warrant_instance.authenticate_user.side_effect = service_error

        with (
            patch("boto3.client", return_value=MagicMock()),
            patch("warrant_lite.WarrantLite", return_value=warrant_instance),
        ):
            strategy = NexityAuthStrategy(credentials, session, server_config, True)
            with pytest.raises(ClientError, match="InternalErrorException"):
                await strategy.login()


def _server_error_response(status: int = 502):
    """Return a mock token-endpoint response with a 5xx HTML body.

    Mirrors aiohttp: ``response.json()`` (the default, content-type-checked
    call the strategies use) raises ContentTypeError on an HTML body, while
    ``response.json(content_type=None)`` (used by check_response) raises
    JSONDecodeError when it tries to parse the HTML as JSON.
    """
    from json import JSONDecodeError

    from aiohttp import ContentTypeError

    html = "<html><head><title>502 Bad Gateway</title></head></html>"

    async def _json(content_type: str | None = "application/json"):
        if content_type is None:
            raise JSONDecodeError("Expecting value", html, 0)
        raise ContentTypeError(
            request_info=MagicMock(),
            history=(),
            message="Attempt to decode JSON with unexpected mimetype: text/html",
        )

    response = MagicMock()
    response.status = status
    response.url = "https://apis.groupe-atlantic.com/token"
    response.json = AsyncMock(side_effect=_json)
    response.text = AsyncMock(return_value=html)
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=None)
    return response


class TestTokenEndpointServerErrors:
    """A 5xx HTML body from a token endpoint must raise a typed Overkiz error."""

    @pytest.mark.asyncio
    async def test_somfy_token_502_raises_service_unavailable(self):
        """Somfy token endpoint 502 maps to ServiceUnavailableError, not aiohttp."""
        from pyoverkiz.exceptions import ServiceUnavailableError

        server_config = ServerConfig(
            server=Server.SOMFY_EUROPE,
            name="Somfy",
            endpoint="https://api.somfy.com",
            manufacturer="Somfy",
            api_type=APIType.CLOUD,
        )
        credentials = UsernamePasswordCredentials("user", "pass")
        session = AsyncMock(spec=ClientSession)
        session.post = MagicMock(return_value=_server_error_response(502))

        strategy = SomfyAuthStrategy(credentials, session, server_config, True)

        with pytest.raises(ServiceUnavailableError):
            await strategy.login()

    @pytest.mark.asyncio
    async def test_cozytouch_token_502_raises_service_unavailable(self):
        """Cozytouch token endpoint 502 maps to ServiceUnavailableError."""
        from pyoverkiz.exceptions import ServiceUnavailableError

        server_config = ServerConfig(
            server=Server.ATLANTIC_COZYTOUCH,
            name="Cozytouch",
            endpoint="https://api.cozytouch.com",
            manufacturer="Atlantic",
            api_type=APIType.CLOUD,
        )
        credentials = UsernamePasswordCredentials("user", "pass")
        session = AsyncMock(spec=ClientSession)
        session.post = MagicMock(return_value=_server_error_response(502))

        strategy = CozytouchAuthStrategy(credentials, session, server_config, True)

        with pytest.raises(ServiceUnavailableError):
            await strategy.login()

    @pytest.mark.asyncio
    async def test_rexel_token_504_raises_service_unavailable(self):
        """Rexel token exchange 504 maps to ServiceUnavailableError."""
        from pyoverkiz.exceptions import ServiceUnavailableError

        server_config = ServerConfig(
            server=Server.REXEL,
            name="Rexel",
            endpoint="https://api.rexel.com",
            manufacturer="Rexel",
            api_type=APIType.CLOUD,
        )
        credentials = RexelOAuthCodeCredentials("code", "https://redirect", "verifier")
        session = AsyncMock(spec=ClientSession)
        session.post = MagicMock(return_value=_server_error_response(504))

        strategy = RexelAuthStrategy(credentials, session, server_config, True)

        with pytest.raises(ServiceUnavailableError):
            await strategy._exchange_token({"grant_type": "authorization_code"})


class TestRexelAuthStrategy:
    """Tests for Rexel auth specifics."""

    @pytest.mark.asyncio
    async def test_exchange_token_error_response(self):
        """Ensure OAuth error payloads raise InvalidTokenError before parsing access token."""
        server_config = ServerConfig(
            server=Server.REXEL,
            name="Rexel",
            endpoint="https://api.rexel.com",
            manufacturer="Rexel",
            api_type=APIType.CLOUD,
        )
        credentials = RexelOAuthCodeCredentials(
            "code", "https://redirect", "code_verifier_value"
        )
        session = AsyncMock(spec=ClientSession)

        mock_response = MagicMock()
        mock_response.status = 400
        mock_response.json = AsyncMock(
            return_value={"error": "invalid_grant", "error_description": "bad grant"}
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        session.post = MagicMock(return_value=mock_response)

        strategy = RexelAuthStrategy(credentials, session, server_config, True)

        with pytest.raises(InvalidTokenError, match="bad grant"):
            await strategy._exchange_token({"grant_type": "authorization_code"})

    def test_ensure_consent_missing(self):
        """Raising when JWT consent claim is missing or incorrect."""
        payload_segment = (
            base64.urlsafe_b64encode(json.dumps({"consent": "other"}).encode())
            .decode()
            .rstrip("=")
        )
        token = f"header.{payload_segment}.sig"

        with pytest.raises(InvalidTokenError, match="Consent is missing"):
            RexelAuthStrategy._ensure_consent(token)

    def test_decode_jwt_payload_invalid_format(self):
        """Malformed tokens raise InvalidTokenError during decoding."""
        with pytest.raises(InvalidTokenError):
            _decode_jwt_payload("invalid.token")


def test_base_strategy_endpoint_defaults_to_server_endpoint():
    """Endpoint property defaults to the server config endpoint."""
    from unittest.mock import AsyncMock

    from aiohttp import ClientSession

    from pyoverkiz.auth.strategies import BaseAuthStrategy
    from pyoverkiz.enums.server import APIType
    from pyoverkiz.models import ServerConfig

    server = ServerConfig(
        server=None,
        name="Test",
        endpoint="https://example.test/api/",
        manufacturer="Test",
        api_type=APIType.CLOUD,
    )
    strategy = BaseAuthStrategy(
        session=AsyncMock(spec=ClientSession),
        server=server,
        ssl_context=True,
    )
    assert strategy.endpoint == "https://example.test/api/"


def test_gateway_candidate_fields():
    """GatewayCandidate holds gateway_id with optional home_id, label, external_id."""
    from pyoverkiz.auth.base import GatewayCandidate

    candidate = GatewayCandidate(
        gateway_id="42760",
        home_id="44571",
        label="Demo",
        external_id="0201-0012-0000",
    )
    assert candidate.gateway_id == "42760"
    assert candidate.home_id == "44571"
    assert candidate.label == "Demo"
    assert candidate.external_id == "0201-0012-0000"


def test_gateway_candidate_optional_fields_default_none():
    """home_id, label and external_id default to None."""
    from pyoverkiz.auth.base import GatewayCandidate

    candidate = GatewayCandidate(gateway_id="g1")
    assert candidate.home_id is None
    assert candidate.label is None
    assert candidate.external_id is None


def test_no_gateway_selected_error_is_overkiz_error():
    """NoGatewaySelectedError subclasses BaseOverkizError."""
    from pyoverkiz.exceptions import BaseOverkizError

    assert issubclass(NoGatewaySelectedError, BaseOverkizError)


def test_rexel_enduser_api_strips_overkiz_suffix():
    """REXEL_ENDUSER_API points one level up from the overkiz device base."""
    from pyoverkiz.const import (
        REXEL_BACKEND_API,
        REXEL_ENDUSER_API,
        REXEL_GATEWAY_HEADER,
    )

    # Device control goes to .../api/enduser/overkiz/{command};
    # the homes/gateways directory lives at .../api/enduser.
    assert (
        REXEL_BACKEND_API
        == "https://econnect-api.rexelservices.fr/api/enduser/overkiz/"
    )
    assert REXEL_ENDUSER_API == "https://econnect-api.rexelservices.fr/api/enduser"
    assert REXEL_BACKEND_API.rsplit("/overkiz/", 1)[0] == REXEL_ENDUSER_API
    assert not REXEL_ENDUSER_API.endswith("/")
    assert REXEL_GATEWAY_HEADER == "gatewayId"


def _build_rexel_strategy_with_token(json_bodies):
    """Return a RexelAuthStrategy with a fake token and a session.

    json_bodies (a list) are returned in order from session.get().
    """
    from unittest.mock import AsyncMock, MagicMock

    from aiohttp import ClientSession

    from pyoverkiz.auth.credentials import RexelOAuthCodeCredentials
    from pyoverkiz.auth.strategies import RexelAuthStrategy
    from pyoverkiz.enums.server import APIType
    from pyoverkiz.models import ServerConfig

    server = ServerConfig(
        server=None,
        name="Rexel",
        endpoint="https://econnect-api.rexelservices.fr/api/enduser/overkiz/",
        manufacturer="Rexel",
        api_type=APIType.CLOUD,
    )
    session = MagicMock(spec=ClientSession)

    responses = []
    for body in json_bodies:
        resp = MagicMock()
        resp.status = 200
        resp.json = AsyncMock(return_value=body)
        resp.text = AsyncMock(return_value="")
        ctx = MagicMock()
        ctx.__aenter__ = AsyncMock(return_value=resp)
        ctx.__aexit__ = AsyncMock(return_value=None)
        responses.append(ctx)
    session.get = MagicMock(side_effect=responses)

    strategy = RexelAuthStrategy(
        credentials=RexelOAuthCodeCredentials("code", "uri", "verifier"),
        session=session,
        server=server,
        ssl_context=True,
    )
    strategy.context.access_token = "fake-jwt"
    return strategy, session


@pytest.mark.asyncio
async def test_rexel_discover_gateways_flattens_homes_and_gateways():
    """discover_gateways returns one GatewayCandidate per gateway across homes."""
    strategy, _ = _build_rexel_strategy_with_token(
        [
            [{"id": 44571, "label": "Demo"}],  # GET /homes (id is an int)
            [  # GET /overkizgateways?homeId=44571
                {"gatewayId": 42760, "externalId": "0201-0012-0000"},
                {"gatewayId": 99999, "externalId": "0201-0012-9999"},
            ],
        ]
    )

    candidates = await strategy.discover_gateways()

    assert len(candidates) == 2
    assert candidates[0].gateway_id == "42760"
    assert candidates[0].home_id == "44571"
    assert candidates[0].label == "Demo"
    assert candidates[0].external_id == "0201-0012-0000"
    assert candidates[1].gateway_id == "99999"
    assert candidates[1].external_id == "0201-0012-9999"


@pytest.mark.asyncio
async def test_rexel_discover_gateways_empty_when_no_homes():
    """discover_gateways returns [] when the account has no homes."""
    strategy, _ = _build_rexel_strategy_with_token([[]])  # GET /homes -> []

    assert await strategy.discover_gateways() == []


@pytest.mark.asyncio
async def test_rexel_login_with_no_gateways_leaves_unselected():
    """Login does not select anything when discovery yields zero gateways."""
    from unittest.mock import AsyncMock

    strategy, _ = _build_rexel_strategy_with_token([])
    strategy._exchange_token = AsyncMock(return_value=None)
    strategy.discover_gateways = AsyncMock(return_value=[])

    await strategy.login()

    assert strategy.selected_gateway is None
    # A subsequent device request must then fail loudly rather than silently.
    with pytest.raises(NoGatewaySelectedError):
        await strategy.auth_headers()


@pytest.mark.asyncio
async def test_rexel_auth_headers_includes_gateway_when_selected():
    """auth_headers includes Authorization and gatewayId after selection."""
    strategy, _ = _build_rexel_strategy_with_token([])
    strategy.select_gateway("1111-2222-3333")

    headers = await strategy.auth_headers()

    assert headers["Authorization"] == "Bearer fake-jwt"
    assert headers["gatewayId"] == "1111-2222-3333"


@pytest.mark.asyncio
async def test_rexel_auth_headers_raises_when_unselected():
    """auth_headers raises NoGatewaySelectedError when no gateway is selected."""
    strategy, _ = _build_rexel_strategy_with_token([])

    with pytest.raises(NoGatewaySelectedError):
        await strategy.auth_headers()


@pytest.mark.asyncio
async def test_rexel_auth_headers_empty_without_token():
    """auth_headers returns empty mapping before login (no token)."""
    strategy, _ = _build_rexel_strategy_with_token([])
    strategy.context.access_token = None

    assert await strategy.auth_headers() == {}


@pytest.mark.asyncio
async def test_rexel_login_auto_selects_single_gateway():
    """Login auto-selects the only gateway when exactly one is found."""
    from unittest.mock import AsyncMock

    from pyoverkiz.auth.base import GatewayCandidate

    strategy, _ = _build_rexel_strategy_with_token([])
    strategy._exchange_token = AsyncMock(return_value=None)
    strategy.discover_gateways = AsyncMock(
        return_value=[GatewayCandidate(gateway_id="only-one")]
    )

    await strategy.login()

    assert strategy.selected_gateway == "only-one"


@pytest.mark.asyncio
async def test_rexel_login_does_not_auto_select_multiple_gateways():
    """Login leaves selection unset when multiple gateways are found."""
    from unittest.mock import AsyncMock

    from pyoverkiz.auth.base import GatewayCandidate

    strategy, _ = _build_rexel_strategy_with_token([])
    strategy._exchange_token = AsyncMock(return_value=None)
    strategy.discover_gateways = AsyncMock(
        return_value=[
            GatewayCandidate(gateway_id="a"),
            GatewayCandidate(gateway_id="b"),
        ]
    )

    await strategy.login()

    assert strategy.selected_gateway is None


def test_auth_package_exports_gateway_selection_types():
    """GatewayCandidate and SupportsGatewaySelection are exported from auth."""
    from pyoverkiz.auth import GatewayCandidate, SupportsGatewaySelection

    assert GatewayCandidate is not None
    assert SupportsGatewaySelection is not None


def test_auth_package_exports_rexel_token_credentials():
    """RexelTokenCredentials is importable from pyoverkiz.auth."""
    from pyoverkiz.auth import RexelTokenCredentials

    assert RexelTokenCredentials is not None


def _build_rexel_token_strategy(json_bodies, *, credentials):
    """Return a RexelTokenAuthStrategy whose session.get yields json_bodies."""
    from unittest.mock import AsyncMock, MagicMock

    from aiohttp import ClientSession

    from pyoverkiz.enums.server import APIType
    from pyoverkiz.models import ServerConfig

    server = ServerConfig(
        server=None,
        name="Rexel",
        endpoint="https://econnect-api.rexelservices.fr/api/enduser/overkiz/",
        manufacturer="Rexel",
        api_type=APIType.CLOUD,
    )
    session = MagicMock(spec=ClientSession)

    responses = []
    for body in json_bodies:
        resp = MagicMock()
        resp.status = 200
        resp.json = AsyncMock(return_value=body)
        resp.text = AsyncMock(return_value="")
        ctx = MagicMock()
        ctx.__aenter__ = AsyncMock(return_value=resp)
        ctx.__aexit__ = AsyncMock(return_value=None)
        responses.append(ctx)
    session.get = MagicMock(side_effect=responses)

    strategy = RexelTokenAuthStrategy(
        credentials=credentials,
        session=session,
        server=server,
        ssl_context=True,
    )
    return strategy, session


@pytest.mark.asyncio
async def test_rexel_token_auth_headers_uses_static_token():
    """auth_headers builds Bearer + gatewayId from a static access token."""
    creds = RexelTokenCredentials(access_token="static-token")
    strategy, _ = _build_rexel_token_strategy([], credentials=creds)
    strategy.select_gateway("gw-1")

    headers = await strategy.auth_headers()

    assert headers["Authorization"] == "Bearer static-token"
    assert headers["gatewayId"] == "gw-1"


@pytest.mark.asyncio
async def test_rexel_token_auth_headers_invokes_callback():
    """auth_headers awaits the callback to obtain a fresh token each call."""
    calls = []

    async def _token() -> str:
        calls.append(1)
        return f"token-{len(calls)}"

    creds = RexelTokenCredentials(access_token_callback=_token)
    strategy, _ = _build_rexel_token_strategy([], credentials=creds)
    strategy.select_gateway("gw-1")

    first = await strategy.auth_headers()
    second = await strategy.auth_headers()

    # Callback is re-invoked per request: proves no caching / no staleness.
    assert first["Authorization"] == "Bearer token-1"
    assert second["Authorization"] == "Bearer token-2"
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_rexel_token_auth_headers_raises_when_unselected():
    """auth_headers raises NoGatewaySelectedError before a gateway is chosen."""
    creds = RexelTokenCredentials(access_token="static-token")
    strategy, _ = _build_rexel_token_strategy([], credentials=creds)

    with pytest.raises(NoGatewaySelectedError):
        await strategy.auth_headers()


@pytest.mark.asyncio
async def test_rexel_token_login_applies_stored_gateway_without_discovery():
    """login() with credentials.gateway_id selects it and skips discovery."""
    creds = RexelTokenCredentials(access_token="static-token", gateway_id="stored-gw")
    # No json bodies: discovery would raise StopIteration on session.get if called.
    strategy, session = _build_rexel_token_strategy([], credentials=creds)

    await strategy.login()

    assert strategy.selected_gateway == "stored-gw"
    session.get.assert_not_called()


@pytest.mark.asyncio
async def test_rexel_token_login_auto_selects_single_gateway():
    """login() without a stored gateway auto-selects a sole discovered gateway."""
    creds = RexelTokenCredentials(access_token="static-token")
    strategy, _ = _build_rexel_token_strategy(
        [
            [{"id": 1, "label": "Home"}],  # GET /homes
            [{"gatewayId": "only-gw", "externalId": "x"}],  # GET /overkizgateways
        ],
        credentials=creds,
    )

    await strategy.login()

    assert strategy.selected_gateway == "only-gw"


@pytest.mark.asyncio
async def test_rexel_token_login_leaves_multiple_unselected():
    """login() leaves selection unset when several gateways are discovered."""
    creds = RexelTokenCredentials(access_token="static-token")
    strategy, _ = _build_rexel_token_strategy(
        [
            [{"id": 1, "label": "Home"}],  # GET /homes
            [  # GET /overkizgateways
                {"gatewayId": "a", "externalId": "x"},
                {"gatewayId": "b", "externalId": "y"},
            ],
        ],
        credentials=creds,
    )

    await strategy.login()

    assert strategy.selected_gateway is None


@pytest.mark.asyncio
async def test_rexel_token_discovery_uses_callback_token():
    """discover_gateways works using the callback-supplied token."""

    async def _token() -> str:
        return "callback-token"

    creds = RexelTokenCredentials(access_token_callback=_token)
    strategy, _ = _build_rexel_token_strategy(
        [
            [{"id": 7, "label": "H"}],
            [{"gatewayId": "g7", "externalId": "e7"}],
        ],
        credentials=creds,
    )

    candidates = await strategy.discover_gateways()

    assert [c.gateway_id for c in candidates] == ["g7"]


def test_rexel_token_strategy_supports_gateway_selection():
    """RexelTokenAuthStrategy satisfies the SupportsGatewaySelection protocol."""
    from pyoverkiz.auth import SupportsGatewaySelection

    creds = RexelTokenCredentials(access_token="static-token")
    strategy, _ = _build_rexel_token_strategy([], credentials=creds)
    assert isinstance(strategy, SupportsGatewaySelection)


def test_somfy_multisite_constants_and_server():
    """Server.SOMFY and the Ginaite/BOB constants are defined and consistent."""
    from pyoverkiz.const import (
        SOMFY_BOB_API_KEY,
        SOMFY_BOB_SITE_API,
        SOMFY_COUNTRY_REGION,
        SOMFY_GINAITE_SUBJECT_ISSUER,
        SOMFY_GINAITE_SUBJECT_TOKEN_TYPE,
        SOMFY_GINAITE_TOKEN_EXCHANGE_GRANT,
        SOMFY_GINAITE_TOKEN_URL,
        SOMFY_REGION_ENDPOINT,
        SUPPORTED_SERVERS,
    )
    from pyoverkiz.enums import Server

    assert Server.SOMFY == "somfy"
    assert SOMFY_GINAITE_TOKEN_URL.endswith("/protocol/openid-connect/token")
    assert SOMFY_GINAITE_SUBJECT_ISSUER == "somfy-customer"
    assert SOMFY_GINAITE_TOKEN_EXCHANGE_GRANT == (
        "urn:ietf:params:oauth:grant-type:token-exchange"
    )
    assert (
        SOMFY_GINAITE_SUBJECT_TOKEN_TYPE
        == "urn:ietf:params:oauth:token-type:access_token"
    )
    assert SOMFY_BOB_SITE_API.endswith("/site-api/public/v1")
    assert SOMFY_BOB_API_KEY == "184638B3FBE874ACD24C14FBD657B"

    # All three regions are enumerated; every mapped region has an endpoint.
    assert SOMFY_COUNTRY_REGION["NL"] == "EMEA"
    assert SOMFY_COUNTRY_REGION["US"] == "SNABA"
    assert SOMFY_COUNTRY_REGION["JP"] == "APAC"
    for region in SOMFY_COUNTRY_REGION.values():
        assert region in SOMFY_REGION_ENDPOINT
    assert SOMFY_REGION_ENDPOINT["EMEA"] == (
        "https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/"
    )

    config = SUPPORTED_SERVERS[Server.SOMFY]
    assert config.server == Server.SOMFY
    assert config.name == "Somfy"


@pytest.mark.asyncio
async def test_somfy_password_token_returns_token_dict():
    """_somfy_password_token posts the password grant and returns the token dict."""
    from unittest.mock import AsyncMock, MagicMock

    from aiohttp import ClientSession

    from pyoverkiz.auth.strategies import _somfy_password_token

    resp = MagicMock()
    resp.status = 200
    resp.json = AsyncMock(
        return_value={"access_token": "sso-abc", "refresh_token": "r1"}
    )
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=None)
    session = MagicMock(spec=ClientSession)
    session.post = MagicMock(return_value=resp)

    token = await _somfy_password_token(session, "user", "pass")

    assert token["access_token"] == "sso-abc"


@pytest.mark.asyncio
async def test_somfy_password_token_bad_credentials():
    """error.invalid.grant maps to SomfyBadCredentialsError."""
    from unittest.mock import AsyncMock, MagicMock

    from aiohttp import ClientSession

    from pyoverkiz.auth.strategies import _somfy_password_token
    from pyoverkiz.exceptions import SomfyBadCredentialsError

    resp = MagicMock()
    resp.status = 200
    resp.json = AsyncMock(return_value={"message": "error.invalid.grant"})
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=None)
    session = MagicMock(spec=ClientSession)
    session.post = MagicMock(return_value=resp)

    with pytest.raises(SomfyBadCredentialsError):
        await _somfy_password_token(session, "user", "bad")


def _build_somfy_multisite_strategy():
    """Return a SomfyMultisiteAuthStrategy with a MagicMock session."""
    from unittest.mock import MagicMock

    from aiohttp import ClientSession

    from pyoverkiz.auth.credentials import UsernamePasswordCredentials
    from pyoverkiz.auth.strategies import SomfyMultisiteAuthStrategy
    from pyoverkiz.const import SUPPORTED_SERVERS
    from pyoverkiz.enums import Server

    session = MagicMock(spec=ClientSession)
    strategy = SomfyMultisiteAuthStrategy(
        credentials=UsernamePasswordCredentials("user", "pass"),
        session=session,
        server=SUPPORTED_SERVERS[Server.SOMFY],
        ssl_context=True,
    )
    return strategy, session


def _json_ctx(body, status=200):
    """A MagicMock aiohttp response context manager returning `body` as JSON."""
    from unittest.mock import AsyncMock, MagicMock

    resp = MagicMock()
    resp.status = status
    resp.json = AsyncMock(return_value=body)
    resp.text = AsyncMock(return_value=str(body))
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=resp)
    ctx.__aexit__ = AsyncMock(return_value=None)
    return ctx


@pytest.mark.asyncio
async def test_somfy_multisite_token_exchange_populates_context():
    """_token_exchange stores the Ginaite access + refresh token."""
    strategy, session = _build_somfy_multisite_strategy()
    session.post = MagicMock(
        return_value=_json_ctx(
            {"access_token": "ginaite-1", "refresh_token": "r-1", "expires_in": 900}
        )
    )

    await strategy._token_exchange("sso-access")

    assert strategy.context.access_token == "ginaite-1"
    assert strategy.context.refresh_token == "r-1"


@pytest.mark.asyncio
async def test_somfy_multisite_token_exchange_error_raises():
    """A non-200 token exchange raises SomfyServiceError."""
    from pyoverkiz.exceptions import SomfyServiceError

    strategy, session = _build_somfy_multisite_strategy()
    session.post = MagicMock(return_value=_json_ctx({"error": "bad"}, status=400))

    with pytest.raises(SomfyServiceError):
        await strategy._token_exchange("sso-access")


_BOB_SITES = {
    "totalCount": 2,
    "results": [
        {
            "siteOID": "site-a",
            "name": "Mick",
            "country": "NL",
            "currentUserRoles": [{"roleOID": "owner"}],
            "subSites": [
                {
                    "externalOID": "ext-a",
                    "type": "SETUP",
                    "gateways": [{"gatewayId": "2025-0000-0001", "type": 98}],
                }
            ],
        },
        {
            "siteOID": "site-b",
            "name": "Smientstraat",
            "country": "NL",
            "currentUserRoles": [{"roleOID": "owner"}],
            "subSites": [
                {
                    "externalOID": "ext-b",
                    "type": "SETUP",
                    "gateways": [{"gatewayId": "1225-0000-0002", "type": 29}],
                }
            ],
        },
    ],
}


@pytest.mark.asyncio
async def test_somfy_multisite_discover_flattens_sites():
    """discover_gateways returns one GatewayCandidate per gateway across sites."""
    strategy, session = _build_somfy_multisite_strategy()
    strategy.context.access_token = "ginaite-1"
    session.get = MagicMock(return_value=_json_ctx(_BOB_SITES))

    candidates = await strategy.discover_gateways()

    assert [c.gateway_id for c in candidates] == ["2025-0000-0001", "1225-0000-0002"]
    assert candidates[0].home_id == "site-a"
    assert candidates[0].label == "Mick"
    assert candidates[0].external_id == "ext-a"


@pytest.mark.asyncio
async def test_somfy_multisite_select_resolves_region_endpoint():
    """Selecting a gateway resolves its country to the EMEA endpoint."""
    strategy, session = _build_somfy_multisite_strategy()
    strategy.context.access_token = "ginaite-1"
    session.get = MagicMock(return_value=_json_ctx(_BOB_SITES))
    await strategy.discover_gateways()

    strategy.select_gateway("2025-0000-0001")

    assert strategy.selected_gateway == "2025-0000-0001"
    assert strategy._selected_site_oid == "site-a"
    assert strategy.endpoint == (
        "https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/"
    )


@pytest.mark.asyncio
async def test_somfy_multisite_select_maps_non_default_region():
    """A country in the map resolves to its non-default region endpoint."""
    strategy, session = _build_somfy_multisite_strategy()
    strategy.context.access_token = "ginaite-1"
    us_site = {
        "totalCount": 1,
        "results": [
            {
                "siteOID": "site-us",
                "name": "Denver",
                "country": "US",
                "currentUserRoles": [{"roleOID": "owner"}],
                "subSites": [
                    {"externalOID": "ext-us", "gateways": [{"gatewayId": "gw-us"}]}
                ],
            }
        ],
    }
    session.get = MagicMock(return_value=_json_ctx(us_site))
    await strategy.discover_gateways()

    strategy.select_gateway("gw-us")

    assert strategy.endpoint == (
        "https://ha401-1.overkiz.com/enduser-mobile-web/enduserAPI/"
    )


@pytest.mark.asyncio
async def test_somfy_multisite_select_unknown_country_falls_back_to_emea(caplog):
    """An unknown country resolves to EMEA and logs a warning (matches the app)."""
    strategy, session = _build_somfy_multisite_strategy()
    strategy.context.access_token = "ginaite-1"
    unknown = {
        "totalCount": 1,
        "results": [
            {
                "siteOID": "site-x",
                "name": "Mars",
                "country": "ZZ",
                "currentUserRoles": [{"roleOID": "owner"}],
                "subSites": [
                    {"externalOID": "ext-x", "gateways": [{"gatewayId": "gw-x"}]}
                ],
            }
        ],
    }
    session.get = MagicMock(return_value=_json_ctx(unknown))
    await strategy.discover_gateways()

    with caplog.at_level(logging.WARNING):
        strategy.select_gateway("gw-x")

    assert strategy.endpoint == (
        "https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/"
    )
    assert "ZZ" in caplog.text
    assert "EMEA" in caplog.text


@pytest.mark.asyncio
async def test_somfy_multisite_select_missing_country_falls_back_to_emea(caplog):
    """A site without a country resolves to EMEA and logs a warning."""
    strategy, session = _build_somfy_multisite_strategy()
    strategy.context.access_token = "ginaite-1"
    missing = {
        "totalCount": 1,
        "results": [
            {
                "siteOID": "site-x",
                "name": "Mystery",
                "currentUserRoles": [{"roleOID": "owner"}],
                "subSites": [
                    {"externalOID": "ext-x", "gateways": [{"gatewayId": "gw-x"}]}
                ],
            }
        ],
    }
    session.get = MagicMock(return_value=_json_ctx(missing))
    await strategy.discover_gateways()

    with caplog.at_level(logging.WARNING):
        strategy.select_gateway("gw-x")

    assert strategy.endpoint == (
        "https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/"
    )
    assert "EMEA" in caplog.text


@pytest.mark.asyncio
async def test_somfy_multisite_endpoint_defaults_to_placeholder_before_select():
    """Before selection, endpoint falls back to the server config placeholder."""
    strategy, _ = _build_somfy_multisite_strategy()
    assert strategy.endpoint == (
        "https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/"
    )


@pytest.mark.asyncio
async def test_somfy_multisite_auth_headers():
    """auth_headers returns the Bearer token, or {} when absent (no gateway header)."""
    strategy, _ = _build_somfy_multisite_strategy()
    assert await strategy.auth_headers() == {}
    strategy.context.access_token = "ginaite-1"
    headers = await strategy.auth_headers()
    assert headers == {"Authorization": "Bearer ginaite-1"}
    assert "gatewayId" not in headers


@pytest.mark.asyncio
async def test_somfy_multisite_refresh_scopes_to_selected_site():
    """refresh_if_needed posts a refresh grant to the ?siteOID URL."""
    strategy, session = _build_somfy_multisite_strategy()
    strategy.context.access_token = "ginaite-1"
    strategy.context.refresh_token = "r-1"
    session.get = MagicMock(return_value=_json_ctx(_BOB_SITES))
    await strategy.discover_gateways()
    strategy.select_gateway("2025-0000-0001")  # forces expiry

    posted = _json_ctx({"access_token": "scoped-1", "refresh_token": "r-2"})
    session.post = MagicMock(return_value=posted)

    refreshed = await strategy.refresh_if_needed()

    assert refreshed is True
    assert strategy.context.access_token == "scoped-1"
    # The refresh URL must carry ?siteOID=<selected site oid>.
    called_url = session.post.call_args.args[0]
    assert "siteOID=site-a" in called_url


@pytest.mark.asyncio
async def test_somfy_multisite_refresh_without_refresh_token_raises():
    """No refresh_token after site selection must raise, not silently no-op.

    Without a refresh token, refresh_if_needed() can't mint the site-scoped
    token, so it must not return False and let auth_headers() keep serving
    the unscoped global token against the site's region endpoint.
    """
    from pyoverkiz.exceptions import SomfyServiceError

    strategy, session = _build_somfy_multisite_strategy()
    strategy.context.access_token = "ginaite-1"
    strategy.context.refresh_token = None
    session.get = MagicMock(return_value=_json_ctx(_BOB_SITES))
    await strategy.discover_gateways()

    strategy.select_gateway("2025-0000-0001")  # forces expiry, no refresh_token

    with pytest.raises(SomfyServiceError):
        await strategy.refresh_if_needed()


def _patch_somfy_login_tokens(strategy, *, ginaite_access_token="ginaite-fresh"):
    """Patch the password grant + token exchange so login() can run offline.

    Returns a context manager patching the module-level password grant to a
    fixed SSO token, and ``strategy._token_exchange`` to install a fresh,
    unscoped, non-expired Ginaite token via the real ``update_from_token``.
    """

    def _install_fresh_token(_sso_access_token):
        strategy.context.update_from_token(
            {
                "access_token": ginaite_access_token,
                "refresh_token": "r-fresh",
                "expires_in": 900,
            }
        )

    return (
        patch(
            "pyoverkiz.auth.strategies._somfy_password_token",
            AsyncMock(return_value={"access_token": "sso-fresh"}),
        ),
        patch.object(
            strategy,
            "_token_exchange",
            AsyncMock(side_effect=_install_fresh_token),
        ),
    )


@pytest.mark.asyncio
async def test_somfy_multisite_relogin_rescopes_selected_gateway():
    """Relogin on a multi-site account must re-apply site scoping.

    A relogin mints a fresh, unscoped Ginaite token that is NOT expired
    (expires_in=900), so without re-selecting the previously-selected
    gateway, refresh_if_needed() would return False and auth_headers() would
    serve the unscoped global token against the still-selected region
    endpoint. The fix must re-select the gateway so the context is marked
    expired again, forcing the next request to mint a site-scoped token.
    """
    strategy, session = _build_somfy_multisite_strategy()
    strategy.context.access_token = "ginaite-1"
    session.get = MagicMock(return_value=_json_ctx(_BOB_SITES))
    await strategy.discover_gateways()
    strategy.select_gateway("2025-0000-0001")
    emea_endpoint = strategy.endpoint

    patch_password, patch_exchange = _patch_somfy_login_tokens(strategy)
    with patch_password, patch_exchange:
        await strategy.login()

    assert strategy.selected_gateway == "2025-0000-0001"
    assert strategy.endpoint == emea_endpoint
    # The fresh token must be treated as stale so the next request re-scopes it.
    assert strategy.context.is_expired()


@pytest.mark.asyncio
async def test_somfy_multisite_relogin_drops_removed_gateway():
    """If the previously-selected gateway disappears on relogin, drop it.

    Rather than silently keep pointing at a gateway/endpoint that's gone
    (e.g. access revoked), the stale selection state must be cleared.
    """
    strategy, session = _build_somfy_multisite_strategy()
    strategy.context.access_token = "ginaite-1"
    session.get = MagicMock(return_value=_json_ctx(_BOB_SITES))
    await strategy.discover_gateways()
    strategy.select_gateway("2025-0000-0001")

    reduced_sites = {
        "totalCount": 1,
        "results": [_BOB_SITES["results"][1]],  # only site-b / 1225-0000-0002
    }
    session.get = MagicMock(return_value=_json_ctx(reduced_sites))

    patch_password, patch_exchange = _patch_somfy_login_tokens(strategy)
    with patch_password, patch_exchange:
        await strategy.login()

    assert strategy.selected_gateway is None
    assert strategy._selected_site_oid is None
    assert strategy.endpoint == strategy.server.endpoint
