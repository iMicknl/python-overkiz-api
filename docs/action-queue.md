# Action queue

The action queue automatically groups rapid, consecutive calls to `execute_action_group()` into a single ActionGroup execution. This minimizes the number of API calls and helps prevent rate limiting issues, such as `TooManyRequestsException`, `TooManyConcurrentRequestsException`, or `TooManyExecutionsException`, which can occur if actions are sent individually in quick succession.

## Enable with defaults

Set `action_queue=True` to enable batching with default settings:

```python
from pyoverkiz.auth import UsernamePasswordCredentials
from pyoverkiz.client import OverkizClient
from pyoverkiz.enums import OverkizCommand, Server
from pyoverkiz.models import Action, Command

client = OverkizClient(
    server=Server.SOMFY_EUROPE,
    credentials=UsernamePasswordCredentials("user@example.com", "password"),
    action_queue=True,  # uses defaults
)

action1 = Action(
    device_url="io://1234-5678-1234/12345678",
    commands=[Command(name=OverkizCommand.CLOSE)],
)
action2 = Action(
    device_url="io://1234-5678-1234/87654321",
    commands=[Command(name=OverkizCommand.OPEN)],
)

task1 = asyncio.create_task(client.execute_action_group([action1]))
task2 = asyncio.create_task(client.execute_action_group([action2]))
exec_id1, exec_id2 = await asyncio.gather(task1, task2)

print(exec_id1 == exec_id2)
```

Defaults:
- `delay=0.5`
- `max_actions=20`

## Advanced settings

If you need to tune batching behavior, pass `ActionQueueSettings`:

```python
import asyncio

from pyoverkiz.action_queue import ActionQueueSettings
from pyoverkiz.client import OverkizClient
from pyoverkiz.auth import UsernamePasswordCredentials
from pyoverkiz.enums import OverkizCommand, Server
from pyoverkiz.models import Action, Command

client = OverkizClient(
    server=Server.SOMFY_EUROPE,
    credentials=UsernamePasswordCredentials("user@example.com", "password"),
    action_queue=ActionQueueSettings(
        delay=0.5,  # seconds to wait before auto-flush
        max_actions=20,  # auto-flush when this count is reached
    ),
)
```

## `flush_action_queue()` (force immediate execution)

Normally, queued actions are sent after the delay window or when `max_actions` is reached. Call `flush_action_queue()` to force the queue to execute immediately, which is useful when you want to send any pending actions without waiting for the delay timer to expire.

```python
from pyoverkiz.action_queue import ActionQueueSettings
import asyncio

from pyoverkiz.client import OverkizClient
from pyoverkiz.auth import UsernamePasswordCredentials
from pyoverkiz.enums import OverkizCommand, Server
from pyoverkiz.models import Action, Command

client = OverkizClient(
    server=Server.SOMFY_EUROPE,
    credentials=UsernamePasswordCredentials("user@example.com", "password"),
    action_queue=ActionQueueSettings(delay=10.0),  # long delay
)

action = Action(
    device_url="io://1234-5678-1234/12345678",
    commands=[Command(name=OverkizCommand.CLOSE)],
)

exec_task = asyncio.create_task(client.execute_action_group([action]))

# Give it time to enter the queue
await asyncio.sleep(0.05)

# Force immediate execution instead of waiting 10 seconds
await client.flush_action_queue()

exec_id = await exec_task
print(exec_id)
```

Why this matters:
- It lets you keep a long delay for batching, but still force a quick execution when a user interaction demands it.
- Useful before shutdown to avoid leaving actions waiting in the queue.

## `get_pending_actions_count()` (best-effort count)

`get_pending_actions_count()` returns a snapshot of how many actions are currently queued. Because the queue can change concurrently (and the method does not acquire the queue lock), the value is approximate. Use it for logging, diagnostics, or UI hints—not for critical control flow.

```python
from pyoverkiz.client import OverkizClient
from pyoverkiz.auth import UsernamePasswordCredentials
from pyoverkiz.enums import OverkizCommand, Server
from pyoverkiz.models import Action, Command

client = OverkizClient(
    server=Server.SOMFY_EUROPE,
    credentials=UsernamePasswordCredentials("user@example.com", "password"),
    action_queue=True,
)

action = Action(
    device_url="io://1234-5678-1234/12345678",
    commands=[Command(name=OverkizCommand.CLOSE)],
)

exec_task = asyncio.create_task(client.execute_action_group([action]))
await asyncio.sleep(0.01)

pending = client.get_pending_actions_count()
print(f"Pending actions (approx): {pending}")

exec_id = await exec_task
print(exec_id)
```

Why it’s best-effort:
- Actions may flush automatically while you read the count.
- New actions may be added concurrently by other tasks.
- The count can be briefly stale, so avoid using it to decide whether you must flush or not.
