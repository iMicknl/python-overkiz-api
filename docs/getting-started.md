# Getting started

## Prerequisites

- Python 3.10+
- An OverKiz-compatible hub and account

## Install pyOverkiz from PyPi


### With UV <small>recommended</small> { #with-uv data-toc-label="with uv" }

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

## First login (cloud)

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
        print(await client.get_setup())


asyncio.run(main())
```

## First login (local)

```python
import asyncio

from pyoverkiz.auth.credentials import LocalTokenCredentials
from pyoverkiz.client import OverkizClient
from pyoverkiz.utils import create_local_server_config


async def main() -> None:
    async with OverkizClient(
        server=create_local_server_config(host="gateway-xxxx.local"),
        credentials=LocalTokenCredentials("local-token"),
        verify_ssl=False,
    ) as client:
        await client.login()
        print(await client.get_setup())


asyncio.run(main())
```

## Sanity check: list devices

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
        devices = await client.get_devices()
        for device in devices:
            print(f"{device.label} ({device.id}) -> {device.widget}")


asyncio.run(main())

## Next steps

- Learn about authentication flows in [docs/authentication.md](docs/authentication.md).
- Control devices and run actions in [docs/device-control.md](docs/device-control.md).
- Handle events in [docs/event-handling.md](docs/event-handling.md).
- Understand errors in [docs/error-handling.md](docs/error-handling.md).
```
