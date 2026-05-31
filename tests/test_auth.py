"""Tests for authentication module."""

# ruff: noqa: S105, S106
# S105/S106: Test credentials use dummy values.

from __future__ import annotations

import base64
import datetime
import importlib.util
import json
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
