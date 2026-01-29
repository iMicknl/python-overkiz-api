"""Test script for Rexel OAuth2 PKCE authentication flow."""

from __future__ import annotations

import asyncio
import os
import secrets
from typing import Any

import aiohttp

from pyoverkiz.auth.credentials import RexelOAuthCodeCredentials
from pyoverkiz.auth.factory import build_auth_strategy
from pyoverkiz.const import (
    REXEL_BACKEND_API,
    REXEL_OAUTH_REDIRECT_URI,
    REXEL_OAUTH_TOKEN_URL,
    SUPPORTED_SERVERS,
)
from pyoverkiz.enums import Server
from pyoverkiz.pkce import generate_pkce_pair
from pyoverkiz.utils import build_rexel_authorization_url

# Test Credentials (from documentation)
TEST_USERNAME = ""
TEST_PASSWORD = ""


async def exchange_code_for_token(
    code: str, code_verifier: str, redirect_uri: str
) -> dict[str, Any]:
    """Exchange authorization code for access token using PKCE (for testing).

    This is a standalone test function. In production, use RexelAuthStrategy.

    Returns the token response containing access_token, refresh_token, etc.
    """
    import urllib.parse

    from pyoverkiz.const import (
        REXEL_OAUTH_CLIENT_ID,
        REXEL_OAUTH_SCOPE,
    )

    payload = {
        "grant_type": "authorization_code",
        "client_id": REXEL_OAUTH_CLIENT_ID,
        "scope": REXEL_OAUTH_SCOPE,
        "code": code,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
    }

    # Add client_secret if configured (some Azure AD B2C apps require it even with PKCE)
    client_secret = os.environ.get("REXEL_CLIENT_SECRET")
    if client_secret:
        payload["client_secret"] = client_secret
        print("Debug - Using client_secret from REXEL_CLIENT_SECRET env var")

    # Debug: print the payload
    print(f"\nDebug - Payload keys: {list(payload.keys())}")
    print(f"Debug - Code length: {len(code)}")
    print(f"Debug - Code verifier length: {len(code_verifier)}")
    print(f"Debug - Code first 100 chars: {code[:100]}")
    print(f"Debug - Code last 100 chars: {code[-100:]}")

    # Manually encode as form data to ensure proper encoding
    encoded_payload = urllib.parse.urlencode(payload)
    print(f"Debug - Encoded payload length: {len(encoded_payload)}")

    # Check if encoding changed the code
    encoded_code_part = encoded_payload.split("code=")[1].split("&")[0]
    decoded_code = urllib.parse.unquote(encoded_code_part)
    print(f"Debug - Code matches after encode/decode: {decoded_code == code}")

    async with aiohttp.ClientSession() as session:
        async with session.post(
            REXEL_OAUTH_TOKEN_URL,
            data=encoded_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ) as response:
            print(f"Token Response Status: {response.status}")
            print(f"Request URL: {response.url}")
            token_data = await response.json()

            if response.status != 200:
                print(f"Error Response: {token_data}")
                raise Exception(
                    f"Token exchange failed: {token_data.get('error_description', token_data)}"
                )

            return token_data


async def test_api_with_token(access_token: str) -> None:
    """Test making API calls with the access token."""
    headers = {"Authorization": f"Bearer {access_token}"}

    async with aiohttp.ClientSession() as session:
        # Test getting setup/gateways
        test_url = f"{REXEL_BACKEND_API}setup/gateways"
        print(f"\nTesting API call to: {test_url}")

        async with session.get(test_url, headers=headers) as response:
            print(f"API Response Status: {response.status}")
            if response.status == 200:
                data = await response.json()
                print(f"API Response: {data}")
            else:
                error_text = await response.text()
                print(f"API Error: {error_text}")


async def test_with_auth_strategy(
    code: str, code_verifier: str, redirect_uri: str
) -> None:
    """Test using the RexelAuthStrategy from the library."""
    print("\n" + "=" * 70)
    print("Testing with RexelAuthStrategy")
    print("=" * 70)

    # Create credentials
    credentials = RexelOAuthCodeCredentials(
        code=code,
        redirect_uri=redirect_uri,
        code_verifier=code_verifier,
    )

    # Get server config
    server_config = SUPPORTED_SERVERS[Server.REXEL]

    async with aiohttp.ClientSession() as session:
        # Build auth strategy
        strategy = build_auth_strategy(
            server_config=server_config,
            credentials=credentials,
            session=session,
            ssl_context=True,
        )

        # Login
        print("\nPerforming login...")
        await strategy.login()
        print("✓ Login successful!")

        # Get auth headers
        headers = strategy.auth_headers()
        print(f"\nAuth Headers: {headers}")

        # Test API call
        test_url = f"{REXEL_BACKEND_API}setup/gateways"
        print(f"\nTesting API call to: {test_url}")

        async with session.get(test_url, headers=headers) as response:
            print(f"API Response Status: {response.status}")
            if response.status == 200:
                data = await response.json()
                print(f"API Response Data: {data}")
            else:
                error_text = await response.text()
                print(f"API Error: {error_text}")


async def main() -> None:
    """Main test flow for Rexel OAuth2 PKCE authentication."""
    print("=" * 70)
    print("Rexel OAuth2 PKCE Authentication Test")
    print("=" * 70)

    # Step 1: Generate PKCE parameters
    code_verifier, code_challenge = generate_pkce_pair()
    print("\n1. Generated PKCE parameters:")
    print(f"   Code Verifier: {code_verifier}")
    print(f"   Code Challenge: {code_challenge}")

    # Step 2: Build authorization URL
    state = secrets.token_urlsafe(16)
    auth_url = build_rexel_authorization_url(code_challenge, state)
    print("\n2. Authorization URL (open this in a browser):")
    print(f"   {auth_url}")
    print("\n   Note: You need to log in with:")
    print(f"   Username: {TEST_USERNAME}")
    print(f"   Password: {TEST_PASSWORD}")

    # Step 3: Get authorization code from user
    print("\n3. After authorizing, you'll be redirected to:")
    print(f"   {REXEL_OAUTH_REDIRECT_URI}?code=XXXXX&state={state}")
    print(
        "\n   Copy the 'code' parameter from the redirect URL (or paste the full URL)."
    )
    auth_code_input = input("\n   Enter the authorization code: ").strip()

    if not auth_code_input:
        print("No authorization code provided. Exiting.")
        return

    # Extract code from URL if full URL was pasted
    if "code=" in auth_code_input:
        import urllib.parse as urlparse

        # Handle full URL or just query params
        if auth_code_input.startswith("http"):
            parsed = urlparse.urlparse(auth_code_input)
            params = urlparse.parse_qs(parsed.query)
        else:
            # Just query string like "code=xxx&state=yyy"
            params = urlparse.parse_qs(auth_code_input)

        auth_code = params.get("code", [auth_code_input])[0]
        print(f"   Extracted code from URL (length: {len(auth_code)})")
    else:
        # Check if &state= was accidentally included
        if "&state=" in auth_code_input:
            auth_code = auth_code_input.split("&state=")[0]
            print(f"   Removed &state= suffix (length: {len(auth_code)})")
        else:
            auth_code = auth_code_input

    # Step 4: Choose test method
    print("\n4. Choose how to test (authorization codes can only be used once):")
    print("   1. Manual token exchange (shows raw token response)")
    print("   2. Use RexelAuthStrategy (library integration test)")
    choice = input("\n   Enter choice (1 or 2, default 2): ").strip() or "2"

    try:
        if choice == "1":
            # Manual token exchange
            print("\n   Exchanging authorization code for access token...")
            token_data = await exchange_code_for_token(
                auth_code, code_verifier, REXEL_OAUTH_REDIRECT_URI
            )
            print("\n   ✓ Token exchange successful!")
            print(f"\n   Access Token: {token_data.get('access_token', '')[:50]}...")
            print(f"   Token Type: {token_data.get('token_type')}")
            print(f"   Expires In: {token_data.get('expires_in')} seconds")

            if token_data.get("refresh_token"):
                print(
                    f"   Refresh Token: {token_data.get('refresh_token', '')[:50]}..."
                )

            # Test API call with the token
            access_token = token_data.get("access_token")
            if access_token:
                print("\n5. Testing API call with access token...")
                await test_api_with_token(access_token)
            else:
                print("\n   ✗ No access token received")

        else:
            # Test with RexelAuthStrategy (recommended)
            await test_with_auth_strategy(
                auth_code, code_verifier, REXEL_OAUTH_REDIRECT_URI
            )

    except Exception as e:
        print(f"\n   ✗ Error: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
