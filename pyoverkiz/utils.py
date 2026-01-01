"""Utilities for generating helper objects and simple checks."""

from __future__ import annotations

import asyncio
import re
import socket

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
    """Return if gateway is Overkiz gateway. Can be used to distinguish between the main gateway and an additional gateway."""
    return bool(re.match(r"\d{4}-\d{4}-\d{4}", gateway_id))


async def resolve_mdns_hostname(hostname: str) -> str | bool:
    """Resolve a .local (mDNS) hostname to its IP address.

    This function attempts to resolve .local addresses to IP addresses to improve
    connection reliability when mDNS resolution is slow or unstable.

    Example:
        >>> ip = await resolve_mdns_hostname("gateway-1234-5678-1234.local")
        >>> # Returns "192.168.1.100" if successful, False if resolution fails

    Args:
        hostname: The hostname to resolve (can be .local or already an IP address)

    Returns:
        The resolved IP address if the hostname is a .local address and resolution
        succeeds. Returns False if the hostname is .local but resolution fails.
        For non-.local addresses (already IPs), returns the original hostname unchanged.

    Note:
        This function uses asyncio.getaddrinfo() which performs async DNS resolution.
        If the hostname doesn't end with .local, it's returned as-is without resolution
        attempt. If resolution times out or fails, False is returned.
    """
    # Extract hostname without port if present
    host_only = hostname.split(":")[0]

    # If not a .local address, return as-is (likely already an IP)
    if not host_only.lower().endswith(".local"):
        return hostname

    try:
        # Attempt async DNS resolution with a timeout
        try:
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.getaddrinfo(host_only, None),
                timeout=2.0,  # 2 second timeout for resolution
            )
            # Return the first IPv4 address found
            if result:
                for addr_info in result:
                    if addr_info[0] == socket.AF_INET:  # IPv4
                        ip = addr_info[4][0]
                        # Reconstruct with port if original had one
                        if ":" in hostname:
                            port = hostname.split(":")[1]
                            return f"{ip}:{port}"
                        return ip
        except TimeoutError:
            # Resolution timed out
            return False

    except Exception:  # pylint: disable=broad-except
        # Any other error (invalid hostname, etc.)
        return False

    return False
