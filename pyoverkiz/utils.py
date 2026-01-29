"""Utilities for generating helper objects and simple checks."""

from __future__ import annotations

import re
import urllib.parse

from pyoverkiz.const import (
    LOCAL_API_PATH,
    REXEL_OAUTH_AUTHORIZE_URL,
    REXEL_OAUTH_CLIENT_ID,
    REXEL_OAUTH_POLICY,
    REXEL_OAUTH_REDIRECT_URI,
    REXEL_OAUTH_SCOPE,
)
from pyoverkiz.enums.server import APIType, Server
from pyoverkiz.models import ServerConfig


def create_local_server_config(
    *,
    host: str,
    name: str = "Somfy Developer Mode",
    manufacturer: str = "Somfy",
    configuration_url: str | None = None,
) -> ServerConfig:
    """Generate server configuration for a local API (Somfy Developer mode)."""
    return create_server_config(
        name=name,
        endpoint=f"https://{host}{LOCAL_API_PATH}",
        manufacturer=manufacturer,
        server=Server.SOMFY_DEVELOPER_MODE,
        configuration_url=configuration_url,
        type=APIType.LOCAL,
    )


def create_server_config(
    *,
    name: str,
    endpoint: str,
    manufacturer: str,
    server: Server | str | None = None,
    type: APIType | str = APIType.CLOUD,
    configuration_url: str | None = None,
) -> ServerConfig:
    """Generate server configuration with the provided endpoint and metadata."""
    return ServerConfig(
        server=server,  # type: ignore[arg-type]
        name=name,
        endpoint=endpoint,
        manufacturer=manufacturer,
        configuration_url=configuration_url,
        type=type,  # type: ignore[arg-type]
    )


def is_overkiz_gateway(gateway_id: str) -> bool:
    """Return if gateway is Overkiz gateway. Can be used to distinguish between the main gateway and an additional gateway."""
    return bool(re.match(r"\d{4}-\d{4}-\d{4}", gateway_id))


def build_rexel_authorization_url(
    code_challenge: str,
    state: str | None = None,
    redirect_uri: str | None = None,
) -> str:
    """Build the Rexel OAuth2 authorization URL with PKCE parameters.

    Args:
        code_challenge: The PKCE code challenge (SHA-256 hash of code_verifier)
        state: Optional state parameter for CSRF protection
        redirect_uri: Optional redirect URI (defaults to REXEL_OAUTH_REDIRECT_URI)

    Returns:
        Complete authorization URL
    """
    params = {
        "p": REXEL_OAUTH_POLICY,
        "client_id": REXEL_OAUTH_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": redirect_uri or REXEL_OAUTH_REDIRECT_URI,
        "response_mode": "query",
        "scope": REXEL_OAUTH_SCOPE,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    if state:
        params["state"] = state

    query_string = urllib.parse.urlencode(params)
    return f"{REXEL_OAUTH_AUTHORIZE_URL}?{query_string}"
