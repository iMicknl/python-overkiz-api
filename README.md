# Python client for OverKiz API

A fully asynchronous and user-friendly API client for the OverKiz platform. This client enables interaction with smart devices connected to OverKiz, supporting multiple vendors such as Somfy TaHoma and Atlantic Cozytouch.

This package is primarily used by Home Assistant Core to provide the Overkiz integration. If you wish to use this package in your own project, refer to the [full documentation](https://imicknl.github.io/python-overkiz-api/), the [example below](#getting-started), or explore the [Home Assistant source code](https://github.com/home-assistant/core/tree/dev/homeassistant/components/overkiz) for additional usage examples.

## Documentation

Full documentation is available at **[imicknl.github.io/python-overkiz-api](https://imicknl.github.io/python-overkiz-api/)**:

- [Getting started](https://imicknl.github.io/python-overkiz-api/getting-started/) — cloud and local API setup
- [Core concepts](https://imicknl.github.io/python-overkiz-api/core-concepts/) — clients, servers, credentials, and models
- [Device control](https://imicknl.github.io/python-overkiz-api/device-control/) and [event handling](https://imicknl.github.io/python-overkiz-api/event-handling/)
- [Migrating from v1](https://imicknl.github.io/python-overkiz-api/migration-v2/)
- [SDK reference](https://imicknl.github.io/python-overkiz-api/sdk-reference/)

## Supported hubs

- Atlantic Cozytouch
- Bouygues Flexom
- Brandt Smart Control **\***
- Hitachi Hi Kumo
- Nexity Eugénie
- Rexel Energeasy Connect **\*\***
- Sauter Cozytouch
- Simu (LiveIn2)
- Somfy Connexoon IO
- Somfy Connexoon RTS
- Somfy TaHoma
- Somfy TaHoma Switch
- Thermor Cozytouch

**\*** _This server's authentication method isn't supported yet. To use it, obtain an access token (by sniffing the original app) and create a local user on the Overkiz API platform._

**\*\*** _Requires OAuth credentials provided by Rexel._

## Installation

```bash
pip install pyoverkiz
```

## Getting started

Connect to the cloud API, authenticate, and list your devices:

```python
import asyncio

from pyoverkiz.auth.credentials import UsernamePasswordCredentials
from pyoverkiz.client import OverkizClient
from pyoverkiz.enums import Server


async def main() -> None:
    async with OverkizClient(
        server=Server.SOMFY_EUROPE,
        credentials=UsernamePasswordCredentials("username", "password"),
    ) as client:
        await client.login()

        devices = await client.get_devices()
        for device in devices:
            print(f"{device.label} ({device.device_url}) - {device.controllable_name}")


asyncio.run(main())
```

For executing commands, listening to events, and connecting to the **local API**, see the [Getting started guide](https://imicknl.github.io/python-overkiz-api/getting-started/) in the documentation.

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
- Initialize the project with `uv sync`, then run `uv run prek install`

#### Tests

```bash
uv run pytest
```
