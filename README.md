# Python client for OverKiz API

A fully asynchronous and user-friendly API client for the OverKiz platform. This client enables interaction with smart devices connected to OverKiz, supporting multiple vendors such as Somfy TaHoma and Atlantic Cozytouch.

This package is mainly used by Home Assistant Core, to offer the Overkiz integration. If you want to use this package in your own project, you can use the [following examples](#getting-started) to get started, or look at the [Home Assistant Code](https://github.com/home-assistant/core/tree/dev/homeassistant/components/overkiz) for more examples.

## Supported hubs

- Atlantic Cozytouch
- Bouygues Flexom
- Brandt Smart Control **\***
- Hitachi Hi Kumo
- Nexity Eugénie
- Rexel Energeasy Connect **\***
- Sauter Cozytouch
- Simu (LiveIn2)
- Somfy Connexoon IO
- Somfy Connexoon RTS
- Somfy TaHoma
- Somfy TaHoma Switch
- Thermor Cozytouch

\[*] _These servers utilize an authentication method that is currently not supported by this library. To use this library with these servers, you will need to obtain an access token (by sniffing the original app) and create a local user on the Overkiz API platform._

## Installation

```bash
pip install pyoverkiz
```

## Getting started


### Cloud API

```python
import asyncio
import time

from pyoverkiz.const import SUPPORTED_SERVERS
from pyoverkiz.client import OverkizClient
from pyoverkiz.enums import Server

USERNAME = ""
PASSWORD = ""

async def main() -> None:
    async with OverkizClient(USERNAME, PASSWORD, server=SUPPORTED_SERVERS[Server.SOMFY_EUROPE]) as client:
        try:
            await client.login()
        except Exception as exception:  # pylint: disable=broad-except
            print(exception)
            return

        devices = await client.get_devices()

        for device in devices:
            print(f"{device.label} ({device.id}) - {device.controllable_name}")
            print(f"{device.widget} - {device.ui_class}")

        while True:
            events = await client.fetch_events()
            print(events)

            time.sleep(2)

asyncio.run(main())
```

### Local API

```python
import asyncio
import time
import aiohttp

from pyoverkiz.client import OverkizClient
from pyoverkiz.const import SUPPORTED_SERVERS, OverkizServer
from pyoverkiz.enums import Server

USERNAME = ""
PASSWORD = ""
LOCAL_GATEWAY = "gateway-xxxx-xxxx-xxxx.local" # or use the IP address of your gateway
VERIFY_SSL = True # set verify_ssl to False if you don't use the .local hostname

async def main() -> None:
    token = "" # you can set the token here for testing purposes, to re-use an earlier generated token

    if not token:
        # Generate new token via Cloud API
        async with OverkizClient(
            username=USERNAME, password=PASSWORD, server=SUPPORTED_SERVERS[Server.SOMFY_EUROPE]
        ) as client:

            await client.login()
            gateways = await client.get_gateways()

            for gateway in gateways:
                token = await client.generate_local_token(gateway.id)
                await client.activate_local_token(gateway_id=gateway.id, token=token, label="Home Assistant/local-dev")
                print(f"Token for {gateway.label} ({gateway.id}):")
                print(token)  # save this token for future use

    # Local Connection
    session = aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(verify_ssl=VERIFY_SSL))

    async with OverkizClient(
        username="", password="", token=token, session=session, verify_ssl=VERIFY_SSL, server=OverkizServer(
            name="Somfy TaHoma (local)",
            endpoint=f"https://{LOCAL_GATEWAY}:8443/enduser-mobile-web/1/enduserAPI/",
            manufacturer="Somfy",
            configuration_url=None,
        )
    ) as client:
        await client.login()

        print("Local API connection succesfull!")

        print(await client.get_api_version())

        setup = await client.get_setup()
        print(setup)

        devices = await client.get_devices()
        print(devices)

        for device in devices:
            print(f"{device.label} ({device.id}) - {device.controllable_name}")
            print(f"{device.widget} - {device.ui_class}")

        while True:
            events = await client.fetch_events()
            print(events)

            time.sleep(2)

asyncio.run(main())
```

## Contribute

We welcome contributions! To get started with setting up this project for development, follow the steps below.

### Dev Container (recommended)

If you use Visual Studio Code with Docker or GitHub Codespaces, you can take advantage of the included [Dev Container](https://code.visualstudio.com/docs/devcontainers/containers). This environment comes pre-configured with all necessary dependencies and tools, including the correct Python version, making setup simple and straightforward.

### Manual

- Ensure Python 3.12 is installed on your system.
- Install [uv](https://docs.astral.sh/uv/getting-started/installation).
- Clone this repository and navigate to it: `cd python-overkiz-api`
- Initialize the project with `uv sync`, then run `uv run pre-commit install`
