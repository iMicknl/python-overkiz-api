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
from pyoverkiz.const import LOCAL_API_PATH, SUPPORTED_SERVERS
from pyoverkiz.enums import APIType, Server
from pyoverkiz.models import OverkizServer


def build_auth_strategy(
    server_key: str | Server | None,
    server: OverkizServer,
    credentials: Credentials,
    session: ClientSession,
    ssl_context: ssl.SSLContext | bool,
) -> Any:
    api_type = APIType.LOCAL if LOCAL_API_PATH in server.endpoint else APIType.CLOUD

    # Normalize server key
    try:
        key = Server(server_key) if server_key else _match_server_key(server)
    except ValueError:
        key = None

    if key == Server.SOMFY_EUROPE:
        return SomfyAuthStrategy(
            _ensure_username_password(credentials),
            session,
            server,
            ssl_context,
            api_type,
        )

    if key in {
        Server.ATLANTIC_COZYTOUCH,
        Server.THERMOR_COZYTOUCH,
        Server.SAUTER_COZYTOUCH,
    }:
        return CozytouchAuthStrategy(
            _ensure_username_password(credentials),
            session,
            server,
            ssl_context,
            api_type,
        )

    if key == Server.NEXITY:
        return NexityAuthStrategy(
            _ensure_username_password(credentials),
            session,
            server,
            ssl_context,
            api_type,
        )

    if key == Server.REXEL:
        return RexelAuthStrategy(
            _ensure_rexel(credentials), session, server, ssl_context, api_type
        )

    if api_type == APIType.LOCAL:
        if isinstance(credentials, LocalTokenCredentials):
            return LocalTokenAuthStrategy(
                credentials, session, server, ssl_context, api_type
            )
        return BearerTokenAuthStrategy(
            _ensure_token(credentials), session, server, ssl_context, api_type
        )

    if isinstance(credentials, TokenCredentials) and not isinstance(
        credentials, LocalTokenCredentials
    ):
        return BearerTokenAuthStrategy(
            credentials, session, server, ssl_context, api_type
        )

    return SessionLoginStrategy(
        _ensure_username_password(credentials), session, server, ssl_context, api_type
    )


def _match_server_key(server: OverkizServer) -> Server:
    for key, value in SUPPORTED_SERVERS.items():
        if server is value or server.endpoint == value.endpoint:
            return Server(key)

    raise ValueError("Unable to match server to a known Server enum.")


def _ensure_username_password(credentials: Credentials) -> UsernamePasswordCredentials:
    if not isinstance(credentials, UsernamePasswordCredentials):
        raise TypeError("UsernamePasswordCredentials are required for this server.")
    return credentials


def _ensure_token(credentials: Credentials) -> TokenCredentials:
    if not isinstance(credentials, TokenCredentials):
        raise TypeError("TokenCredentials are required for this server.")
    return credentials


def _ensure_rexel(credentials: Credentials) -> RexelOAuthCodeCredentials:
    if not isinstance(credentials, RexelOAuthCodeCredentials):
        raise TypeError("RexelOAuthCodeCredentials are required for this server.")
    return credentials
