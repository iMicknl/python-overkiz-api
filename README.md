# Python client for OverKiz API

A fully asynchronous and user-friendly API client for the OverKiz platform. This client enables interaction with smart devices connected to OverKiz, supporting multiple vendors such as Somfy TaHoma and Atlantic Cozytouch.

This package is primarily used by Home Assistant Core to provide the Overkiz integration. If you wish to use this package in your own project, refer to the [examples below](#getting-started) or explore the [Home Assistant source code](https://github.com/home-assistant/core/tree/dev/homeassistant/components/overkiz) for additional usage examples.

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
    async with OverkizClient(
        USERNAME, PASSWORD, server=SUPPORTED_SERVERS[Server.SOMFY_EUROPE]
    ) as client:
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
LOCAL_GATEWAY = "gateway-xxxx-xxxx-xxxx.local"  # or use the IP address of your gateway
VERIFY_SSL = True  # set verify_ssl to False if you don't use the .local hostname


async def main() -> None:
    token = ""  # generate your token via the Somfy app and include it here

    # Local Connection
    session = aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(verify_ssl=VERIFY_SSL)
    )

    async with OverkizClient(
        username="",
        password="",
        token=token,
        session=session,
        verify_ssl=VERIFY_SSL,
        server=OverkizServer(
            name="Somfy TaHoma (local)",
            endpoint=f"https://{LOCAL_GATEWAY}:8443/enduser-mobile-web/1/enduserAPI/",
            manufacturer="Somfy",
            configuration_url=None,
        ),
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

## Projects using pyOverkiz

This package powers the Overkiz integration in [Home Assistant Core](https://www.home-assistant.io/integrations/overkiz/). Other open-source projects and custom automations also leverage pyOverkiz to interact with Overkiz-compatible hubs and devices, including:

- [overkiz2mqtt](https://github.com/RichieB2B/overkiz2mqtt): Bridges Overkiz devices to MQTT for integration with various platforms.
- [mcp-overkiz](https://github.com/phimage/mcp-overkiz): Implements an MCP server to enable communication between Overkiz devices and language models.
- [tahoma](https://github.com/pzim-devdata/tahoma): Command Line Interface (CLI) to control Overkiz devices.


## Contribute

We welcome contributions! To get started with setting up this project for development, follow the steps below.


### Project setup
#### Dev Container (recommended)

If you use Visual Studio Code with Docker or GitHub Codespaces, you can take advantage of the included [Dev Container](https://code.visualstudio.com/docs/devcontainers/containers). This environment comes pre-configured with all necessary dependencies and tools, including the correct Python version, making setup simple and straightforward.

#### Manual setup

- Install [uv](https://docs.astral.sh/uv/getting-started/installation).
- Clone this repository and navigate to it: `cd python-overkiz-api`
- Initialize the project with `uv sync`, then run `uv run pre-commit install`

#### Tests

```bash
uv run pytest
```
