# Device control

## List devices

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
            print(device.label, device.controllable_name)


asyncio.run(main())
```

## Read a state value

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
        device = devices[0]
        closure_state = next(
            (state for state in device.states if state.name == "core:ClosureState"),
            None,
        )
        print(closure_state.value if closure_state else None)


asyncio.run(main())
```

## Send a command

```python
import asyncio

from pyoverkiz.auth.credentials import UsernamePasswordCredentials
from pyoverkiz.client import OverkizClient
from pyoverkiz.enums import OverkizCommand, Server
from pyoverkiz.models import Action, Command


async def main() -> None:
    async with OverkizClient(
        server=Server.SOMFY_EUROPE,
        credentials=UsernamePasswordCredentials("you@example.com", "password"),
    ) as client:
        await client.login()
        await client.execute_action_group(
            actions=[
                Action(
                    device_url="io://1234-5678-1234/12345678",
                    commands=[
                        Command(
                            name=OverkizCommand.SET_CLOSURE,
                            parameters=[50],
                        )
                    ],
                )
            ],
            label="Set closure",
        )


asyncio.run(main())
```

## Action groups and common patterns

- Use a single action group to batch multiple device commands.
- Parameters vary by device. Many closure-style devices use 0–100.
- Thermostat-style devices commonly accept target temperatures.

```python
import asyncio

from pyoverkiz.auth.credentials import UsernamePasswordCredentials
from pyoverkiz.client import OverkizClient
from pyoverkiz.enums import OverkizCommand, Server
from pyoverkiz.models import Action, Command


async def main() -> None:
    async with OverkizClient(
        server=Server.SOMFY_EUROPE,
        credentials=UsernamePasswordCredentials("you@example.com", "password"),
    ) as client:
        await client.login()
        await client.execute_action_group(
            actions=[
                Action(
                    device_url="io://1234-5678-1234/12345678",
                    commands=[
                        Command(
                            name=OverkizCommand.SET_TARGET_TEMPERATURE,
                            parameters=[21.5],
                        )
                    ],
                )
            ],
            label="Set temperature",
        )


asyncio.run(main())
```

## Polling vs event-driven

Polling `get_devices()` is simple but can be slower. Event listeners provide faster updates; see the event handling guide for details.
