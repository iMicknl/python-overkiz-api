"""Tests for authentication module."""

from __future__ import annotations

import datetime
import ssl
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from aiohttp import ClientSession

from pyoverkiz.auth.base import AuthContext
from pyoverkiz.auth.credentials import (
    LocalTokenCredentials,
    RexelOAuthCodeCredentials,
    TokenCredentials,
    UsernamePasswordCredentials,
)
from pyoverkiz.auth.factory import (
    _ensure_rexel,
    _ensure_token,
    _ensure_username_password,
    build_auth_strategy,
)
from pyoverkiz.auth.strategies import (
    BearerTokenAuthStrategy,
    CozytouchAuthStrategy,
    LocalTokenAuthStrategy,
    NexityAuthStrategy,
    RexelAuthStrategy,
    SessionLoginStrategy,
    SomfyAuthStrategy,
)
from pyoverkiz.enums import APIType, Server
from pyoverkiz.models import ServerConfig


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
        creds = RexelOAuthCodeCredentials("auth_code_xyz", "http://redirect.uri")
        assert creds.code == "auth_code_xyz"
        assert creds.redirect_uri == "http://redirect.uri"


class TestAuthFactory:
    """Test authentication factory functions."""

    def test_ensure_username_password_valid(self):
        """Test that valid username/password credentials pass validation."""
        creds = UsernamePasswordCredentials("user", "pass")
        result = _ensure_username_password(creds)
        assert result is creds

    def test_ensure_username_password_invalid(self):
        """Test that invalid credentials raise TypeError."""
        creds = TokenCredentials("token")
        with pytest.raises(
            TypeError, match="UsernamePasswordCredentials are required"
        ):
            _ensure_username_password(creds)

    def test_ensure_token_valid(self):
        """Test that valid token credentials pass validation."""
        creds = TokenCredentials("token")
        result = _ensure_token(creds)
        assert result is creds

    def test_ensure_token_local_valid(self):
        """Test that LocalTokenCredentials also pass token validation."""
        creds = LocalTokenCredentials("local_token")
        result = _ensure_token(creds)
        assert result is creds

    def test_ensure_token_invalid(self):
        """Test that invalid credentials raise TypeError."""
        creds = UsernamePasswordCredentials("user", "pass")
        with pytest.raises(TypeError, match="TokenCredentials are required"):
            _ensure_token(creds)

    def test_ensure_rexel_valid(self):
        """Test that valid Rexel credentials pass validation."""
        creds = RexelOAuthCodeCredentials("code", "uri")
        result = _ensure_rexel(creds)
        assert result is creds

    def test_ensure_rexel_invalid(self):
        """Test that invalid credentials raise TypeError."""
        creds = UsernamePasswordCredentials("user", "pass")
        with pytest.raises(TypeError, match="RexelOAuthCodeCredentials are required"):
            _ensure_rexel(creds)

    @pytest.mark.asyncio
    async def test_build_auth_strategy_somfy(self):
        """Test building Somfy auth strategy."""
        server_config = ServerConfig(
            server=Server.SOMFY_EUROPE,
            name="Somfy",
            endpoint="https://api.somfy.com",
            manufacturer="Somfy",
            type=APIType.CLOUD,
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
            type=APIType.CLOUD,
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
            type=APIType.CLOUD,
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
            type=APIType.CLOUD,
        )
        credentials = RexelOAuthCodeCredentials("code", "http://redirect.uri")
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
            type=APIType.LOCAL,
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
            type=APIType.LOCAL,
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
            type=APIType.CLOUD,
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
            type=APIType.CLOUD,
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
            type=APIType.CLOUD,
        )
        credentials = TokenCredentials("token")  # Wrong type for Somfy
        session = AsyncMock(spec=ClientSession)

        with pytest.raises(
            TypeError, match="UsernamePasswordCredentials are required"
        ):
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
            type=APIType.CLOUD,
        )
        credentials = UsernamePasswordCredentials("user", "pass")
        session = AsyncMock(spec=ClientSession)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"success": True})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        session.post = MagicMock(return_value=mock_response)

        strategy = SessionLoginStrategy(
            credentials, session, server_config, True, APIType.CLOUD
        )
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
            type=APIType.CLOUD,
        )
        credentials = UsernamePasswordCredentials("user", "pass")
        session = AsyncMock(spec=ClientSession)

        mock_response = MagicMock()
        mock_response.status = 204
        mock_response.json = AsyncMock()
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        session.post = MagicMock(return_value=mock_response)

        strategy = SessionLoginStrategy(
            credentials, session, server_config, True, APIType.CLOUD
        )
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
            type=APIType.CLOUD,
        )
        credentials = UsernamePasswordCredentials("user", "pass")
        session = AsyncMock(spec=ClientSession)

        strategy = SessionLoginStrategy(
            credentials, session, server_config, True, APIType.CLOUD
        )
        result = await strategy.refresh_if_needed()

        assert not result

    def test_auth_headers_no_token(self):
        """Test that auth headers return empty dict when no token."""
        server_config = ServerConfig(
            server=Server.SOMFY_OCEANIA,
            name="Test",
            endpoint="https://api.test.com/",
            manufacturer="Test",
            type=APIType.CLOUD,
        )
        credentials = UsernamePasswordCredentials("user", "pass")
        session = AsyncMock(spec=ClientSession)

        strategy = SessionLoginStrategy(
            credentials, session, server_config, True, APIType.CLOUD
        )
        headers = strategy.auth_headers()

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
            type=APIType.CLOUD,
        )
        credentials = TokenCredentials("my_bearer_token")
        session = AsyncMock(spec=ClientSession)

        strategy = BearerTokenAuthStrategy(
            credentials, session, server_config, True, APIType.CLOUD
        )
        result = await strategy.login()

        # Login should be a no-op
        assert result is None

    def test_auth_headers_with_token(self):
        """Test that auth headers include Bearer token."""
        server_config = ServerConfig(
            server=None,
            name="Test",
            endpoint="https://api.test.com/",
            manufacturer="Test",
            type=APIType.CLOUD,
        )
        credentials = TokenCredentials("my_bearer_token")
        session = AsyncMock(spec=ClientSession)

        strategy = BearerTokenAuthStrategy(
            credentials, session, server_config, True, APIType.CLOUD
        )
        headers = strategy.auth_headers()

        assert headers == {"Authorization": "Bearer my_bearer_token"}
