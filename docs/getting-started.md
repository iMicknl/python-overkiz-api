# Getting started

This guide will help you install the library, connect to your hub, and perform your first actions.

> Need the official Overkiz cloud API reference? Visit the [Overkiz API Documentation](https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/doc) ([mirror](/api)). Most endpoints are accessible via the pyOverkiz package.

## Prerequisites

- Python 3.10+
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
            server=create_local_server_config(host="gateway-xxxx-xxxx-xxxx.local"),
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
            server=Server.SOMFY_EUROPE,
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

    Authentication to the Rexel cloud requires your mobile app username and password.

    Use `Server.REXEL` with `UsernamePasswordCredentials` to authenticate.

    ```python
    import asyncio

    from pyoverkiz.auth.credentials import UsernamePasswordCredentials
    from pyoverkiz.client import OverkizClient
    from pyoverkiz.enums import Server

    async def main() -> None:
        async with OverkizClient(
            server=Server.REXEL,
            credentials=UsernamePasswordCredentials("you@example.com", "password"),
        ) as client:
            await client.login()

    asyncio.run(main())
    ```
