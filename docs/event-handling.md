# Event handling

## Register and unregister a listener

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
        await client.register_event_listener()
        await client.unregister_event_listener()


asyncio.run(main())
```

## Fetch events with backoff

```python
import asyncio

from pyoverkiz.auth.credentials import UsernamePasswordCredentials
from pyoverkiz.client import OverkizClient
from pyoverkiz.enums import Server
from pyoverkiz.exceptions import (
    InvalidEventListenerIdError,
    NoRegisteredEventListenerError,
)


async def main() -> None:
    async with OverkizClient(
        server=Server.SOMFY_EUROPE,
        credentials=UsernamePasswordCredentials("you@example.com", "password"),
    ) as client:
        await client.login()
        await client.register_event_listener()

        while True:
            try:
                events = await client.fetch_events()
            except (InvalidEventListenerIdError, NoRegisteredEventListenerError):
                await asyncio.sleep(1)
                await client.register_event_listener()
                continue

            for event in events:
                print(event)

            await asyncio.sleep(2)


asyncio.run(main())
```

## Reconnect tips

- Re-register the listener when you see `InvalidEventListenerIdError`.
- Poll occasionally if your network has unstable connectivity.
- Keep the fetch loop alive to avoid listener timeout.
