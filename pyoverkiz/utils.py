from __future__ import annotations

from pyoverkiz.enums import Server
from pyoverkiz.models import OverkizServer


def generate_local_server(
    host: str,
    name: str = Server.SOMFY_DEVELOPER_MODE,
    manufacturer: str = "Somfy",
    configuration_url: str | None = None,
) -> OverkizServer:
    """Generate OverkizServer class for connection with a local API (Somfy Developer mode)."""
    return OverkizServer(
        name=name,
        endpoint=f"https://{host}/enduser-mobile-web/1/enduserAPI/",
        manufacturer=manufacturer,
        configuration_url=configuration_url,
    )
