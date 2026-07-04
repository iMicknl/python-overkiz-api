#!/usr/bin/env python
"""Live smoke test for Somfy multi-site sign-in.

Logs in with a Somfy account, lists every site/gateway the account can reach,
selects each one in turn, and prints the resolved region endpoint plus a device
count. Nothing is mutated.

Run (credentials via env, never hard-coded):

    PYOVERKIZ_USERNAME='you@example.com' \\
    PYOVERKIZ_PASSWORD='...' \\
    uv run python tools/somfy_multisite_smoke.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

from pyoverkiz.auth.credentials import UsernamePasswordCredentials
from pyoverkiz.client import OverkizClient
from pyoverkiz.enums import Server


async def main() -> int:
    username = os.environ.get("PYOVERKIZ_USERNAME")
    password = os.environ.get("PYOVERKIZ_PASSWORD")
    if not username or not password:
        print(
            "Set PYOVERKIZ_USERNAME and PYOVERKIZ_PASSWORD in the environment.",
            file=sys.stderr,
        )
        return 2

    credentials = UsernamePasswordCredentials(username=username, password=password)

    async with OverkizClient(server=Server.SOMFY, credentials=credentials) as client:
        # Placeholder endpoint until a gateway is selected, so skip the
        # event-listener registration that login() would otherwise attempt.
        await client.login(register_event_listener=False)

        gateways = await client.discover_gateways()
        print(f"Discovered {len(gateways)} gateway(s):\n")

        for gateway in gateways:
            client.select_gateway(gateway.gateway_id)
            setup = await client.get_setup(refresh=True)
            devices = setup.devices

            print(f"  {gateway.label or '(unnamed)'}")
            print(f"    gateway_id : {gateway.gateway_id}")
            print(f"    site (oid) : {gateway.home_id}")
            print(f"    external   : {gateway.external_id}")
            # The strategy overrides the placeholder endpoint per selected site;
            # the client requests against this resolved endpoint, not server_config.
            print(f"    endpoint   : {client._auth.endpoint}")  # noqa: SLF001
            print(f"    devices    : {len(devices)}")
            for device in devices[:5]:
                print(f"      - {device.label} ({device.controllable_name})")
            if len(devices) > 5:
                print(f"      ... and {len(devices) - 5} more")
            print()

    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    raise SystemExit(asyncio.run(main()))
