"""Generate and activate a local API token for Atlantic Cozytouch.

Usage:
    python scripts/generate_local_token.py --username EMAIL --password PASSWORD [--label LABEL]
"""

from __future__ import annotations

import argparse
import asyncio

from pyoverkiz.auth.credentials import UsernamePasswordCredentials
from pyoverkiz.client import OverkizClient
from pyoverkiz.enums import Server


async def main(username: str, password: str, label: str) -> None:
    credentials = UsernamePasswordCredentials(username=username, password=password)

    async with OverkizClient(
        server=Server.ATLANTIC_COZYTOUCH, credentials=credentials
    ) as client:
        await client.login()

        gateways = await client.get_gateways()
        if not gateways:
            print("No gateways found.")
            return

        gateway = gateways[0]
        print(f"Using gateway: {gateway.gateway_id}")

        token = await client.generate_local_token(gateway.gateway_id)
        print(f"Generated token: {token}")

        request_id = await client.activate_local_token(
            gateway_id=gateway.gateway_id,
            token=token,
            label=label,
        )
        print(f"Activated (request ID: {request_id})")

        tokens = await client.get_local_tokens(gateway.gateway_id)
        print(f"\nActive tokens ({len(tokens)}):")
        for t in tokens:
            print(f"  - {t.label} (uuid={t.uuid}, scope={t.scope})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--label", default="pyoverkiz-local")
    args = parser.parse_args()

    asyncio.run(main(args.username, args.password, args.label))
