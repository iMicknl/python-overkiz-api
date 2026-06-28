# Resiliency

pyOverkiz retries transient failures automatically and raises typed exceptions for
everything else. This page explains what the library handles for you, so you can
decide what (if anything) to handle yourself.

## What the library retries

Every request is wrapped with [`backoff`](https://github.com/litl/backoff) decorators
using exponential delays with full jitter. Each retry policy is capped by both a
maximum number of attempts (`max_tries`) and a maximum wall-clock budget (`max_time`),
so retries always give up rather than looping indefinitely.

| Failure | Retried | Budget | On retry |
| --- | --- | --- | --- |
| Connection errors — `TimeoutError`, `ClientConnectorError`, `ServerDisconnectedError` | yes | 3 tries / ~30s | reopen the connection |
| `NotAuthenticatedError` (session expired) | yes | 2 tries / ~60s | call `login()` |
| `TooManyConcurrentRequestsError` | yes | 5 tries / ~120s | — |
| `TooManyExecutionsError` | yes | 5 tries / ~300s | — |
| `ExecutionQueueFullError` | yes | 5 tries / ~120s | — |
| Event-listener errors — `InvalidEventListenerIdError`, `NoRegisteredEventListenerError` | yes (on `fetch_events`) | 2 tries / ~30s | re-register the listener |

Everything else — `BadCredentialsError`, `TooManyRequestsError`, `MaintenanceError`,
`UnsupportedOperationError`, and so on — is **not** retried and is raised directly.

### Connection errors fail fast

Transient transport failures are retried quickly and then given up on (3 attempts
within roughly 30 seconds). This is deliberate: it is better to surface a failure to
the caller than to keep a request hanging for minutes. For a polling loop such as
`fetch_events()`, letting a call fail and retrying on the next poll tick is usually the
right behaviour.

A dropped keep-alive socket (`ServerDisconnectedError`) is treated as a connection
blip and simply retried — it does **not** trigger a re-login. A genuine session expiry
is reported by the server as a `Not authenticated` response, which raises
`NotAuthenticatedError` and escalates to a re-login through the separate auth policy.

!!! note "`max_time` does not interrupt a hung request"
    The `max_time` budget only bounds the scheduling of retries *between* attempts; it
    cannot cancel a single in-flight request. A request that hangs is bounded by the
    session timeout (see below), which surfaces as a `TimeoutError` and is then retried.

## Request timeout

When pyOverkiz creates its own session, it applies a default per-request timeout
(`total=15s`, `sock_connect=10s`). This is kept below the connection-retry budget so a
hung socket fails fast and is retried, instead of blocking on aiohttp's 300-second
default.

If you pass your own `ClientSession`, **you own its timeout** — pyOverkiz does not
override it. Configure one explicitly:

```python
from aiohttp import ClientSession, ClientTimeout

from pyoverkiz.auth.credentials import UsernamePasswordCredentials
from pyoverkiz.client import OverkizClient
from pyoverkiz.enums import Server

session = ClientSession(timeout=ClientTimeout(total=15, sock_connect=10))

client = OverkizClient(
    server=Server.SOMFY_EUROPE,
    credentials=UsernamePasswordCredentials("you@example.com", "password"),
    session=session,
)
```

## What you should handle

Because the library already retries transient failures, most consumers only need to
handle the terminal cases:

- **`BadCredentialsError`** — the credentials are wrong; retrying will not help. Prompt
  for new credentials.
- **`TooManyRequestsError`** — you are being rate limited. Reduce your polling
  frequency. This is intentionally not retried so you do not make the situation worse.
- **`MaintenanceError` / `ServiceUnavailableError`** — the backend is temporarily
  unavailable. Back off and try again later.
- **`NotAuthenticatedError`** — only reaches you if the automatic re-login also failed.
  Call `login()` and retry.

```python
import asyncio

from pyoverkiz.auth.credentials import UsernamePasswordCredentials
from pyoverkiz.client import OverkizClient
from pyoverkiz.enums import Server
from pyoverkiz.exceptions import (
    MaintenanceError,
    NotAuthenticatedError,
    TooManyRequestsError,
)


async def fetch_devices() -> None:
    async with OverkizClient(
        server=Server.SOMFY_EUROPE,
        credentials=UsernamePasswordCredentials("you@example.com", "password"),
    ) as client:
        await client.login()
        try:
            print(await client.get_devices())
        except NotAuthenticatedError:
            await client.login()
            print(await client.get_devices())
        except TooManyRequestsError:
            # Rate limited — slow down your polling.
            await asyncio.sleep(60)
        except MaintenanceError:
            # Backend under maintenance — try again later.
            pass


asyncio.run(fetch_devices())
```

All exceptions derive from `BaseOverkizError`, so you can catch that as a catch-all for
anything the library raises.
