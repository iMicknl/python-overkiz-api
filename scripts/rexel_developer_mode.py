"""Authenticate with Rexel (OAuth2 + PKCE) and inspect developer mode / tokens.

This is an interactive helper: it prints a Rexel sign-in URL, you log in in a
browser, then paste back the resulting redirect URL (or just the ``code``). It
then calls ``get_developer_mode`` and ``get_local_tokens`` for the gateway.

Usage:
    python scripts/rexel_developer_mode.py
"""

from __future__ import annotations

import asyncio
import urllib.parse

from pyoverkiz.auth.credentials import RexelOAuthCodeCredentials
from pyoverkiz.client import OverkizClient
from pyoverkiz.const import REXEL_OAUTH_REDIRECT_URI
from pyoverkiz.enums import Server
from pyoverkiz.pkce import generate_pkce_pair
from pyoverkiz.utils import build_rexel_authorization_url


def _extract_code(answer: str) -> str:
    """Return the OAuth2 ``code`` from a pasted redirect URL, or the code itself."""
    answer = answer.strip()
    if "code=" in answer:
        query = urllib.parse.urlparse(answer).query
        code = urllib.parse.parse_qs(query).get("code", [""])[0]
        if code:
            return code
    return answer


async def main() -> None:
    code_verifier, code_challenge = generate_pkce_pair()

    authorization_url = build_rexel_authorization_url(code_challenge=code_challenge)
    print("1. Open this URL in your browser and sign in to Rexel:\n")
    print(f"   {authorization_url}\n")
    print(
        "2. After signing in you are redirected to "
        f"{REXEL_OAUTH_REDIRECT_URI}?code=...\n"
    )
    answer = await asyncio.to_thread(
        input, "3. Paste the full redirect URL (or just the code) here: "
    )
    code = _extract_code(answer)

    credentials = RexelOAuthCodeCredentials(
        code=code,
        redirect_uri=REXEL_OAUTH_REDIRECT_URI,
        code_verifier=code_verifier,
    )

    async with OverkizClient(server=Server.REXEL, credentials=credentials) as client:
        # login() exchanges the code and auto-selects the gateway if there is
        # only one; otherwise pick one from the discovered candidates.
        await client.login()

        gateways = await client.discover_gateways()
        if not gateways:
            print("No gateways found.")
            return

        for index, candidate in enumerate(gateways):
            print(f"  [{index}] {candidate.gateway_id} (home={candidate.label})")

        gateway_id = gateways[0].gateway_id
        if len(gateways) > 1:
            choice = await asyncio.to_thread(
                input, f"Select gateway [0-{len(gateways) - 1}] (default 0): "
            )
            if choice.strip():
                gateway_id = gateways[int(choice)].gateway_id
        client.select_gateway(gateway_id)
        print(f"\nUsing gateway: {gateway_id}\n")

        developer_mode = await client.get_developer_mode(gateway_id)
        print(f"Developer mode: {developer_mode}")

        tokens = await client.get_local_tokens(gateway_id)
        print(f"\nActive tokens ({len(tokens)}):")
        for token in tokens:
            print(f"  - {token.label} (uuid={token.uuid}, scope={token.scope})")


if __name__ == "__main__":
    asyncio.run(main())
