"""Utilities for generating helper objects and simple checks."""

from __future__ import annotations

import re

from pyoverkiz.const import LOCAL_API_PATH
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
        server=server,
        name=name,
        endpoint=endpoint,
        manufacturer=manufacturer,
        configuration_url=configuration_url,
        type=type,
    )


def is_overkiz_gateway(gateway_id: str) -> bool:
    """Return if gateway is Overkiz gateway. Can be used to distinguish between the main gateway and an additional gateway."""
    return bool(re.match(r"\d{4}-\d{4}-\d{4}", gateway_id))
