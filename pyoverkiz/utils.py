from __future__ import annotations

import re

from pyoverkiz.const import LOCAL_API_PATH
from pyoverkiz.models import OverkizServer


def generate_local_server(
    host: str,
    name: str = "Somfy Developer Mode",
    manufacturer: str = "Somfy",
    configuration_url: str | None = None,
) -> OverkizServer:
    """Generate OverkizServer class for connection with a local API (Somfy Developer mode)."""
    return OverkizServer(
        name=name,
        endpoint=f"https://{host}{LOCAL_API_PATH}",
        manufacturer=manufacturer,
        configuration_url=configuration_url,
    )


def is_overkiz_gateway(gateway_id: str) -> bool:
    "Return if gateway is Overkiz gateway. Can be used to distinguish between the main gateway and an additional gateway."
    return bool(re.match(r"\d{4}-\d{4}-\d{4}", gateway_id))
