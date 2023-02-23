# Python client for OverKiz API

<p align=center>
    <a href="https://github.com/iMicknl/python-overkiz-api/actions"><img src="https://github.com/iMicknl/python-overkiz-api/workflows/CI/badge.svg"/></a>
    <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" /></a>
</p>

A fully async and easy to use API client for the (internal) OverKiz API. You can use this client to interact with smart devices connected to the OverKiz platform, used by various vendors like Somfy TaHoma and Atlantic Cozytouch.

This package is written for the Home Assistant [Overkiz](https://www.home-assistant.io/integrations/overkiz/) integration, but could be used by any Python project interacting with OverKiz hubs.

## Supported hubs

See [pyoverkiz/const.py](./pyoverkiz/const.py)

## Installation

```bash
pip install pyoverkiz
```

## Getting started

### API Documentation

A subset of the API is [documented and maintened](https://somfy-developer.github.io/Somfy-TaHoma-Developer-Mode) by Somfy.

### Local API or Developer mode

See https://github.com/Somfy-Developer/Somfy-TaHoma-Developer-Mode#getting-started

For the moment, only Somfy TaHoma Switch, TaHoma V2 and Connexoon hubs from Somfy Europe can enabled this mode. Not all the devices are returned. You can have more details [here](https://github.com/Somfy-Developer/Somfy-TaHoma-Developer-Mode/issues/20).

```python
import asyncio
import time

from aiohttp import ClientSession

from pyoverkiz.clients.overkiz import OverkizClient
from pyoverkiz.const import Server
from pyoverkiz.overkiz import Overkiz

USERNAME = ""
PASSWORD = ""


async def main() -> None:

    async with ClientSession() as session:
        client = Overkiz.get_client_for(
            server=Server.SOMFY_EUROPE,
            username=USERNAME,
            password=PASSWORD,
            session=session
        )
        try:
            await client.login()
        except Exception as exception:  # pylint: disable=broad-except
            print(exception)
            return

        devices = await client.get_devices()

        for device in devices:
            print(f"{device.label} ({device.id}) - {device.controllable_name}")
            print(f"{device.widget} - {device.ui_class}")

        await client.register_event_listener()

        while True:
            events = await client.fetch_events()
            print(events)

            time.sleep(2)


asyncio.run(main())
```

### Cloud API

```python
import asyncio
import time

from aiohttp import ClientSession

from pyoverkiz.clients.overkiz import OverkizClient
from pyoverkiz.const import Server
from pyoverkiz.overkiz import Overkiz

USERNAME = ""
PASSWORD = ""


async def main() -> None:

    async with ClientSession() as session:
        client = Overkiz.get_client_for(
            Server.SOMFY_EUROPE, USERNAME, PASSWORD, session
        )
        try:
            await client.login()
        except Exception as exception:  # pylint: disable=broad-except
            print(exception)
            return

        gateways = await client.get_gateways()
        token = await client.generate_local_token(gateways[0].id)
        await client.activate_local_token(gateways[0].id, token, "pyoverkiz")

        domain = f"gateway-{gateways[0].id}.local"
        local_client: OverkizClient = Overkiz.get_client_for(
            Server.SOMFY_DEV_MODE, domain, token, session
        )

        devices = await local_client.get_devices()

        for device in devices:
            print(f"{device.label} ({device.id}) - {device.controllable_name}")
            print(f"{device.widget} - {device.ui_class}")

        await local_client.register_event_listener()

        while True:
            events = await local_client.fetch_events()
            print(events)

            time.sleep(2)


asyncio.run(main())

```

## Development

### Installation

- For Linux, install [pyenv](https://github.com/pyenv/pyenv) using [pyenv-installer](https://github.com/pyenv/pyenv-installer)
- For MacOS, run `brew install pyenv`
- Don't forget to update your `.bashrc` file (or similar):
  ```
  export PATH="~/.pyenv/bin:$PATH"
  eval "$(pyenv init -)"
  ```
- Install the required [dependencies](https://github.com/pyenv/pyenv/wiki#suggested-build-environment)
- Install [poetry](https://python-poetry.org): `curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python`

- Clone this repository
- `cd python-overkiz-api`
- Install the required Python version: `pyenv install`
- Init the project: `poetry install`
- Run `poetry run pre-commit install`

## PyCharm

As IDE you can use [PyCharm](https://www.jetbrains.com/pycharm/).

Using snap, run `snap install pycharm --classic` to install it.

For MacOS, run `brew cask install pycharm-ce`

Once launched, don't create a new project, but open an existing one and select the **python-overkiz-api** folder.

Go to _File | Settings | Project: nre-tag | Project Interpreter_. Your interpreter must look like `<whatever>/python-overkiz-api/.venv/bin/python`
