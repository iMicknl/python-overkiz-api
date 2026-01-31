# Error handling

## Common exceptions

- `NotAuthenticatedException`
- `TooManyRequestsException`
- `TooManyConcurrentRequestsException`
- `TooManyExecutionsException`
- `MaintenanceException`
- `AccessDeniedToGatewayException`
- `BadCredentialsException`

## Retry and backoff guidance

Use short, jittered delays for transient errors and re-authenticate on auth failures.

```python
import asyncio

from pyoverkiz.auth.credentials import UsernamePasswordCredentials
from pyoverkiz.client import OverkizClient
from pyoverkiz.enums import Server
from pyoverkiz.exceptions import (
    NotAuthenticatedException,
    TooManyConcurrentRequestsException,
    TooManyRequestsException,
)


async def fetch_devices_with_retry() -> None:
    async with OverkizClient(
        server=Server.SOMFY_EUROPE,
        credentials=UsernamePasswordCredentials("you@example.com", "password"),
    ) as client:
        await client.login()
        for attempt in range(5):
            try:
                devices = await client.get_devices()
                print(devices)
                return
            except (TooManyRequestsException, TooManyConcurrentRequestsException):
                await asyncio.sleep(0.5 * (attempt + 1))
            except NotAuthenticatedException:
                await client.login()


asyncio.run(fetch_devices_with_retry())
```

## SSL and local certificates

If you use local gateways with `.local` hostnames, you may need `verify_ssl=False` when a trusted certificate is not available.

## Timeouts

For long-running operations, prefer shorter request timeouts with retries rather than a single long timeout.
