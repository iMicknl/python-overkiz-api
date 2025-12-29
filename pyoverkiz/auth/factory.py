"""Factory to build authentication strategies based on server and credentials."""

from __future__ import annotations

import ssl

from aiohttp import ClientSession

from pyoverkiz.auth.credentials import (
    Credentials,
    LocalTokenCredentials,
    RexelOAuthCodeCredentials,
    TokenCredentials,
    UsernamePasswordCredentials,
)
from pyoverkiz.auth.strategies import (
    AuthStrategy,
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


def build_auth_strategy(
    *,
    server_config: ServerConfig,
    credentials: Credentials,
    session: ClientSession,
    ssl_context: ssl.SSLContext | bool,
) -> AuthStrategy:
    """Build the correct auth strategy for the given server and credentials."""
    server: Server | None = server_config.server

    if server == Server.SOMFY_EUROPE:
        return SomfyAuthStrategy(
            _ensure_username_password(credentials),
            session,
            server_config,
            ssl_context,
            server_config.type,
        )

    if server in {
        Server.ATLANTIC_COZYTOUCH,
        Server.THERMOR_COZYTOUCH,
        Server.SAUTER_COZYTOUCH,
    }:
        return CozytouchAuthStrategy(
            _ensure_username_password(credentials),
            session,
            server_config,
            ssl_context,
            server_config.type,
        )

    if server == Server.NEXITY:
        return NexityAuthStrategy(
            _ensure_username_password(credentials),
            session,
            server_config,
            ssl_context,
            server_config.type,
        )

    if server == Server.REXEL:
        return RexelAuthStrategy(
            _ensure_rexel(credentials),
            session,
            server_config,
            ssl_context,
            server_config.type,
        )

    if server_config.type == APIType.LOCAL:
        if isinstance(credentials, LocalTokenCredentials):
            return LocalTokenAuthStrategy(
                credentials, session, server_config, ssl_context, server_config.type
            )
        return BearerTokenAuthStrategy(
            _ensure_token(credentials),
            session,
            server_config,
            ssl_context,
            server_config.type,
        )

    if isinstance(credentials, TokenCredentials) and not isinstance(
        credentials, LocalTokenCredentials
    ):
        return BearerTokenAuthStrategy(
            credentials, session, server_config, ssl_context, server_config.type
        )

    return SessionLoginStrategy(
        _ensure_username_password(credentials),
        session,
        server_config,
        ssl_context,
        server_config.type,
    )


def _ensure_username_password(credentials: Credentials) -> UsernamePasswordCredentials:
    """Validate that credentials are username/password based."""
    if not isinstance(credentials, UsernamePasswordCredentials):
        raise TypeError("UsernamePasswordCredentials are required for this server.")
    return credentials


def _ensure_token(credentials: Credentials) -> TokenCredentials:
    """Validate that credentials carry a bearer token."""
    if not isinstance(credentials, TokenCredentials):
        raise TypeError("TokenCredentials are required for this server.")
    return credentials


def _ensure_rexel(credentials: Credentials) -> RexelOAuthCodeCredentials:
    """Validate that credentials are of Rexel OAuth code type."""
    if not isinstance(credentials, RexelOAuthCodeCredentials):
        raise TypeError("RexelOAuthCodeCredentials are required for this server.")
    return credentials
