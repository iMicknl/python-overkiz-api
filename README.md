[![CI status](https://github.com/iMicknl/python-overkiz-api/workflows/CI/badge.svg)](https://github.com/iMicknl/python-overkiz-api/actions)
[![GitHub release](https://img.shields.io/github/release/iMicknl/python-overkiz-api.svg)](https://GitHub.com/iMicknl/python-overkiz-api/releases/)
[![Open in Visual Studio Code](https://open.vscode.dev/badges/open-in-vscode.svg)](https://open.vscode.dev/iMicknl/python-overkiz-api/)
[![Discord](https://img.shields.io/discord/718361810985549945?label=chat&logo=discord)](https://discord.gg/RRXuSVDAzG)

# Overkiz API wrapper for Python (pyoverkiz)

An async package to interact with various Overkiz API's, for example Somfy (Connexoon / TaHoma), Hitachi (Hi Kumo), Rexel (Energeasy Connect) and Atlantic (Cozytouch).

This package is mainly written for usage in a Home Assistant ([ha-tahoma](https://github.com/iMicknl/ha-tahoma)) integration, but could be used by any Python project interacting with Overkiz servers.

## Supported Overkiz servers

- Atlantic Cozytouch
- Hitachi Hi Kumo (Asia, Europe, Oceania)
- Nexity Eugénie
- Rexel Energeasy
- Somfy (Europe, North America, Oceania)

>Somfy has an official API, which can be consumed via the [Somfy-open-api](https://github.com/tetienne/somfy-open-api). However, this API has many limitations and stability issues, thus the need for this package.


## Installation

```bash
pip install pyoverkiz
```

## Getting started

```python
import asyncio
import time

from pyoverkiz.const import SUPPORTED_SERVERS
from pyoverkiz.client import OverkizClient

USERNAME = ""
PASSWORD = ""

async def main() -> None:
    async with OverkizClient(USERNAME, PASSWORD, api_url=SUPPORTED_SERVERS["somfy_europe"]) as client:
        try:
            await client.login()
        except Exception as exception:  # pylint: disable=broad-except
            print(exception)
            return

        devices = await client.get_devices()

        for device in devices:
            print(device)

        while True:
            events = await client.fetch_events()
            print(events)

            time.sleep(2)

asyncio.run(main())
```
