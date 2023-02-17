# Python client for OverKiz API

<p align=center>
    <a href="https://github.com/iMicknl/python-overkiz-api/actions"><img src="https://github.com/iMicknl/python-overkiz-api/workflows/CI/badge.svg"/></a>
    <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" /></a>
</p>

A fully async and easy to use API client for the (internal) OverKiz API. You can use this client to interact with smart devices connected to the OverKiz platform, used by various vendors like Somfy TaHoma and Atlantic Cozytouch.

This package is written for the Home Assistant [ha-tahoma](https://github.com/iMicknl/ha-tahoma) integration, but could be used by any Python project interacting with OverKiz hubs.

> Somfy TaHoma has an official API, which can be consumed via the [somfy-open-api](https://github.com/tetienne/somfy-open-api). Unfortunately only a few device classes are supported via the official API, thus the need for this API client.

## Supported hubs

- Atlantic Cozytouch
- Bouygues Flexom
- Hitachi Hi Kumo
- Nexity Eugénie
- Rexel Energeasy Connect
- Simu (LiveIn2)
- Somfy Connexoon IO
- Somfy Connexoon RTS
- Somfy TaHoma
- Somfy TaHoma Switch
- Thermor Cozytouch

## Installation

```bash
pip install pyoverkiz
```

## Getting started

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
        print(token)
        await client.activate_local_token(gateways[0].id, token, "pyoverkiz")

        local_client: OverkizClient = Overkiz.get_client_for(
            Server.SOMFY_DEV_MODE, gateways[0].id, token, session
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
