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
            _ensure_credentials(credentials, UsernamePasswordCredentials),
            session,
            server_config,
            ssl_context,
        )

    if server in {
        Server.ATLANTIC_COZYTOUCH,
        Server.THERMOR_COZYTOUCH,
        Server.SAUTER_COZYTOUCH,
    }:
        return CozytouchAuthStrategy(
            _ensure_credentials(credentials, UsernamePasswordCredentials),
            session,
            server_config,
            ssl_context,
        )

    if server == Server.NEXITY:
        return NexityAuthStrategy(
            _ensure_credentials(credentials, UsernamePasswordCredentials),
            session,
            server_config,
            ssl_context,
        )

    if server == Server.REXEL:
        return RexelAuthStrategy(
            _ensure_credentials(credentials, RexelOAuthCodeCredentials),
            session,
            server_config,
            ssl_context,
        )

    if server_config.api_type == APIType.LOCAL:
        if isinstance(credentials, LocalTokenCredentials):
            return LocalTokenAuthStrategy(
                credentials, session, server_config, ssl_context
            )
        return BearerTokenAuthStrategy(
            _ensure_credentials(credentials, TokenCredentials),
            session,
            server_config,
            ssl_context,
        )

    if isinstance(credentials, TokenCredentials) and not isinstance(
        credentials, LocalTokenCredentials
    ):
        return BearerTokenAuthStrategy(credentials, session, server_config, ssl_context)

    return SessionLoginStrategy(
        _ensure_credentials(credentials, UsernamePasswordCredentials),
        session,
        server_config,
        ssl_context,
    )


def _ensure_credentials[C: Credentials](
    credentials: Credentials, expected: type[C]
) -> C:
    """Validate that credentials match the expected type."""
    if not isinstance(credentials, expected):
        raise TypeError(f"{expected.__name__} are required for this server.")
    return credentials
