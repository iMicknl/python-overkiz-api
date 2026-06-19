"""Factory to build authentication strategies based on server and credentials."""

from __future__ import annotations

import ssl

from aiohttp import ClientSession

from pyoverkiz.auth.credentials import (
    Credentials,
    LocalTokenCredentials,
    RexelOAuthCodeCredentials,
    RexelTokenCredentials,
    TokenCredentials,
    UsernamePasswordCredentials,
)
from pyoverkiz.auth.strategies import (
    AuthStrategy,
    BearerTokenAuthStrategy,
    BrandtAuthStrategy,
    CozytouchAuthStrategy,
    LocalTokenAuthStrategy,
    NexityAuthStrategy,
    RexelAuthStrategy,
    RexelTokenAuthStrategy,
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

    # Local API routing keys off api_type, not server, so a local config can
    # carry any server identity (e.g. Server.REXEL) purely for labelling.
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

    if server == Server.BRANDT:
        return BrandtAuthStrategy(
            _ensure_credentials(credentials, UsernamePasswordCredentials),
            session,
            server_config,
            ssl_context,
        )

    if server == Server.REXEL:
        if isinstance(credentials, RexelTokenCredentials):
            return RexelTokenAuthStrategy(
                credentials, session, server_config, ssl_context
            )
        return RexelAuthStrategy(
            _ensure_credentials(credentials, RexelOAuthCodeCredentials),
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
