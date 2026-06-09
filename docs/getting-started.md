# Getting started

This guide will help you install the library, connect to your hub, and perform your first actions.

> Need the official Overkiz cloud API reference? Visit the [Overkiz API Documentation](https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/doc) ([mirror](api/index.html)). Most endpoints are accessible via the pyOverkiz package.

> Upgrading from pyOverkiz 1.x? See the [migration guide](migration-v2.md) for a full list of breaking changes.

## Prerequisites

- Python 3.12+
- An OverKiz-compatible hub and account

## Install pyOverkiz from PyPI

### With UV <small>recommended</small>

```bash
uv add pyoverkiz
```

### With pip

```bash
pip install pyoverkiz
```

### Optional extras

Some servers require additional dependencies that are not installed by default:

| Extra | Server | Packages |
|-------|--------|----------|
| `nexity` | Nexity | boto3, warrant-lite |

Install an extra with:

```bash
uv add "pyoverkiz[nexity]"
# or
pip install "pyoverkiz[nexity]"
```

## Choose your server

Use a cloud server when you want to connect through the vendor’s public API. Use a local server when you want LAN access to a gateway.

- Cloud servers use the `Server` enum.
- Local servers use `create_local_server_config` with a hostname or IP address.

## Authentication

=== "Somfy (cloud)"

    Authentication to the Somfy cloud requires your mobile app username and password and your region.

    Use `Server.SOMFY_EUROPE`, `Server.SOMFY_AMERICA`, or `Server.SOMFY_OCEANIA` with `UsernamePasswordCredentials` to select your region and authenticate.

    ```python
    import asyncio

    from pyoverkiz.auth.credentials import UsernamePasswordCredentials
    from pyoverkiz.client import OverkizClient
    from pyoverkiz.enums import Server


    async def main() -> None:
        async with OverkizClient(
            server=Server.SOMFY_EUROPE,
            credentials=UsernamePasswordCredentials("you@example.com", "password"),
        ) as client:
            await client.login()

    asyncio.run(main())
    ```

=== "Somfy (local)"

    Local authentication requires a token generated via the official mobile app. For details on obtaining a token, refer to [Somfy TaHoma Developer Mode](https://github.com/Somfy-Developer/Somfy-TaHoma-Developer-Mode).

    Use the helper function `create_local_server_config` to create a `Server` with `LocalTokenCredentials` to provide your token.

    ```python
    import asyncio

    from pyoverkiz.auth.credentials import LocalTokenCredentials
    from pyoverkiz.client import OverkizClient
    from pyoverkiz.utils import create_local_server_config


    async def main() -> None:
        async with OverkizClient(
            server=create_local_server_config(host="gateway-xxxx-xxxx-xxxx.local:8443"),
            credentials=LocalTokenCredentials("token-from-your-mobile-app"),
            verify_ssl=True, # disable if you connect via IP
        ) as client:
            await client.login()

    asyncio.run(main())
    ```

=== "Cozytouch (cloud)"

    Authentication to the Cozytouch cloud requires your mobile app username and password and your vendor.

    Use `Server.ATLANTIC_COZYTOUCH`, `Server.SAUTER_COZYTOUCH`, or `Server.THERMOR_COZYTOUCH` with `UsernamePasswordCredentials` to select your vendor and authenticate.

    ```python
    import asyncio

    from pyoverkiz.auth.credentials import UsernamePasswordCredentials
    from pyoverkiz.client import OverkizClient
    from pyoverkiz.enums import Server


    async def main() -> None:
        async with OverkizClient(
            server=Server.ATLANTIC_COZYTOUCH,
            credentials=UsernamePasswordCredentials("you@example.com", "password"),
        ) as client:
            await client.login()

    asyncio.run(main())
    ```

=== "Hitachi Hi Kumo (cloud)"

    Authentication to the Hitachi Hi Kumo cloud requires your mobile app username and password and your region.

    Use `Server.HI_KUMO_ASIA`, `Server.HI_KUMO_EUROPE`, or `Server.HI_KUMO_OCEANIA` with `UsernamePasswordCredentials` to select your region and authenticate.

    ```python
    import asyncio

    from pyoverkiz.auth.credentials import UsernamePasswordCredentials
    from pyoverkiz.client import OverkizClient
    from pyoverkiz.enums import Server


    async def main() -> None:
        async with OverkizClient(
            server=Server.HI_KUMO_EUROPE,
            credentials=UsernamePasswordCredentials("you@example.com", "password"),
        ) as client:
            await client.login()

    asyncio.run(main())
    ```

=== "Rexel (cloud)"

    Authentication to the Rexel cloud uses OAuth2 with PKCE (Proof Key for Code Exchange).

    **Step 1: Generate PKCE parameters and authorization URL**

    ```python
    import secrets
    from pyoverkiz.pkce import generate_pkce_pair
    from pyoverkiz.utils import build_rexel_authorization_url

    # Generate PKCE code verifier and challenge
    code_verifier, code_challenge = generate_pkce_pair()

    # Generate authorization URL (user must visit this in browser)
    state = secrets.token_urlsafe(16)  # For CSRF protection
    auth_url = build_rexel_authorization_url(code_challenge, state)

    print(f"Visit this URL to authorize: {auth_url}")
    ```

    **Step 2: Redirect user to authorization URL**

    Direct the user to the `auth_url`. After successful login, they will be redirected to:
    ```
    https://my.home-assistant.io/redirect/oauth?code=AUTHORIZATION_CODE&state=STATE_VALUE
    ```

    Compare the returned `state` against the value from step 1 before
    continuing, and reject the response if they differ — this is what guards
    against CSRF.

    **Step 3: Exchange authorization code for access token**

    ```python
    import asyncio
    from pyoverkiz.auth.credentials import RexelOAuthCodeCredentials
    from pyoverkiz.client import OverkizClient
    from pyoverkiz.enums import Server
    from pyoverkiz.const import REXEL_OAUTH_REDIRECT_URI

    async def main(returned_state: str) -> None:
        # Verify the state echoed back by the redirect matches step 1.
        if returned_state != state:
            raise ValueError("State mismatch — possible CSRF, aborting.")

        # Use the authorization code from the redirect
        async with OverkizClient(
            server=Server.REXEL,
            credentials=RexelOAuthCodeCredentials(
                code="AUTHORIZATION_CODE_FROM_REDIRECT",
                redirect_uri=REXEL_OAUTH_REDIRECT_URI,
                code_verifier=code_verifier,  # From step 1
            ),
        ) as client:
            await client.login()  # auto-selects a sole gateway

            # Accounts with more than one gateway must select one explicitly.
            gateways = await client.discover_gateways()
            if len(gateways) > 1:
                client.select_gateway(gateways[0].gateway_id)

            # Client is now authenticated and ready to use

    asyncio.run(main(returned_state="STATE_VALUE_FROM_REDIRECT"))
    ```

=== "Rexel (externally-managed token)"

    Use this when an external system already owns the OAuth2 lifecycle — for
    example the Home Assistant `application_credentials` platform, which
    authorizes, exchanges, refreshes, and persists tokens for you. pyoverkiz
    then only needs the *current* access token and the Rexel gateway selection.

    Supply a token in one of two ways:

    **Async callback (recommended for long-running apps).** pyoverkiz calls it
    before each request, so the owner can refresh and persist transparently.

    ```python
    import asyncio
    from pyoverkiz.auth.credentials import RexelTokenCredentials
    from pyoverkiz.client import OverkizClient
    from pyoverkiz.enums import Server


    async def get_access_token() -> str:
        # Return a currently-valid access token (refresh upstream as needed).
        ...


    async def main() -> None:
        async with OverkizClient(
            server=Server.REXEL,
            credentials=RexelTokenCredentials(
                access_token_callback=get_access_token,
            ),
        ) as client:
            await client.login()  # discovers + auto-selects a sole gateway

            gateways = await client.discover_gateways()
            if len(gateways) > 1:
                client.select_gateway(gateways[0].gateway_id)

            setup = await client.get_setup()
            print(f"{len(setup.devices)} device(s)")

    asyncio.run(main())
    ```

    **Static token (simplest, for quick standalone or test use).** No refresh —
    when the token expires you construct a new client.

    ```python
    credentials = RexelTokenCredentials(access_token="YOUR_ACCESS_TOKEN")
    ```

    **Reload without re-discovering.** Persist the chosen `gateway_id` and pass
    it back on the next run; `login()` applies it directly and skips discovery:

    ```python
    credentials = RexelTokenCredentials(
        access_token_callback=get_access_token,
        gateway_id="STORED_GATEWAY_ID",
    )
    ```

=== "Rexel (local)"

    Rexel Energeasy Connect gateways expose a local API that third-party
    software (such as Home Assistant) can connect to over your local network.
    Supported by the following gateways:

    - Energeasy Connect Rail Din (`48`)
    - Energeasy Connect V2 (`57`)
    - Energeasy Connect V3 (`120`)
    - Energeasy Connect V3 Rail Din (`125`)

    To obtain a token, enable the local API of your Energeasy Connect Box from
    the EConnect mobile app:

    1. Open the EConnect app.
    2. Go to **Settings** » **My home** » **Maintenance**.
    3. Select your gateway » **Local API**.
    4. Generate a token to authenticate your API requests.
    5. Use the generated token below, and set the host to your gateway PIN code
       (e.g. `gateway-xxxx-xxxx-xxxx.local:8443`) or its IP address.

    Use the helper function `create_local_server_config` to create a `Server`
    with `LocalTokenCredentials` to provide your token.

    ```python
    import asyncio

    from pyoverkiz.auth.credentials import LocalTokenCredentials
    from pyoverkiz.client import OverkizClient
    from pyoverkiz.utils import create_local_server_config


    async def main() -> None:
        async with OverkizClient(
            server=create_local_server_config(host="gateway-xxxx-xxxx-xxxx.local:8443"),
            credentials=LocalTokenCredentials("token-from-the-econnect-app"),
            verify_ssl=True, # disable if you connect via IP
        ) as client:
            await client.login()

    asyncio.run(main())
    ```
