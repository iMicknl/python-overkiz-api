"""Factory to build authentication strategies based on server and credentials."""

from __future__ import annotations

import ssl
from typing import Any

from aiohttp import ClientSession

from pyoverkiz.auth.credentials import (
    Credentials,
    LocalTokenCredentials,
    RexelOAuthCodeCredentials,
    TokenCredentials,
    UsernamePasswordCredentials,
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
from pyoverkiz.const import SUPPORTED_SERVERS
from pyoverkiz.enums import APIType, Server
from pyoverkiz.models import ServerConfig


def build_auth_strategy(
    server_key: str | Server | None,
    server_config: ServerConfig,
    credentials: Credentials,
    session: ClientSession,
    ssl_context: ssl.SSLContext | bool,
) -> Any:
    """Build the correct auth strategy for the given server and credentials."""
    # Normalize server key
    try:
        key = Server(server_key) if server_key else _match_server_key(server_config)
    except ValueError:
        key = None

    if key == Server.SOMFY_EUROPE:
        return SomfyAuthStrategy(
            _ensure_username_password(credentials),
            session,
            server_config,
            ssl_context,
            server_config.type,
        )

    if key in {
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

    if key == Server.NEXITY:
        return NexityAuthStrategy(
            _ensure_username_password(credentials),
            session,
            server_config,
            ssl_context,
            server_config.type,
        )

    if key == Server.REXEL:
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


def _match_server_key(server: ServerConfig) -> Server:
    """Find the `Server` enum corresponding to a `ServerConfig` entry."""
    for key, value in SUPPORTED_SERVERS.items():
        if server is value or server.endpoint == value.endpoint:
            return Server(key)

    raise ValueError("Unable to match server to a known Server enum.")


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
