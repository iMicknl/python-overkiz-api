# Action queue

The action queue automatically groups rapid, consecutive calls to `execute_action_group()` into a single ActionGroup execution. This minimizes the number of API calls and helps prevent rate limiting issues, such as `TooManyRequestsError`, `TooManyConcurrentRequestsError`, `TooManyExecutionsError`, or `ExecutionQueueFullError` which can occur if actions are sent individually in quick succession.

## How batching and merging works

The Overkiz API uses three levels of nesting:

- **Command** — a single device instruction (e.g. `close`, `setClosure(50)`)
- **Action** — one device URL + one or more commands
- **ActionGroup** — a batch of actions submitted as a single API call

The gateway enforces **one action per device** in each action group. The queue handles this automatically: when multiple actions target the same `device_url`, their commands are merged into a single action while preserving order.

### Different devices — no merging needed

Three commands for three different devices produce three actions in one action group:

```python
# These three calls arrive within the delay window:
await client.execute_action_group([Action(device_url="io://1234-5678-1234/12345678", commands=[Command(name=OverkizCommand.CLOSE)])])
await client.execute_action_group([Action(device_url="io://1234-5678-1234/87654321", commands=[Command(name=OverkizCommand.OPEN)])])
await client.execute_action_group([Action(device_url="io://1234-5678-1234/11111111", commands=[Command(name=OverkizCommand.STOP)])])

# Sent as one API call:
# ActionGroup(actions=[
#     Action(device_url="io://…/12345678", commands=[close]),
#     Action(device_url="io://…/87654321", commands=[open]),
#     Action(device_url="io://…/11111111", commands=[stop]),
# ])
```

### Same device — commands are merged

When two calls target the same device, the queue merges their commands into a single action:

```python
await client.execute_action_group([Action(device_url="io://1234-5678-1234/12345678", commands=[Command(name=OverkizCommand.CLOSE)])])
await client.execute_action_group([Action(device_url="io://1234-5678-1234/12345678", commands=[Command(name=OverkizCommand.SET_CLOSURE, parameters=[50])])])

# Sent as one API call:
# ActionGroup(actions=[
#     Action(device_url="io://…/12345678", commands=[close, setClosure(50)]),
# ])
```

### Mixed — both behaviors combined

```python
await client.execute_action_group([Action(device_url="io://1234-5678-1234/12345678", commands=[Command(name=OverkizCommand.CLOSE)])])
await client.execute_action_group([
    Action(device_url="io://1234-5678-1234/87654321", commands=[Command(name=OverkizCommand.OPEN)]),
    Action(device_url="io://1234-5678-1234/12345678", commands=[Command(name=OverkizCommand.SET_CLOSURE, parameters=[50])]),
])

# Sent as one API call:
# ActionGroup(actions=[
#     Action(device_url="io://…/12345678", commands=[close, setClosure(50)]),  # merged
#     Action(device_url="io://…/87654321", commands=[open]),
# ])
```

The original action objects passed to `execute_action_group()` are never mutated — the queue works on internal copies.

## Enable with defaults

Pass `ActionQueueSettings()` via `OverkizClientSettings` to enable batching with default settings:

```python
import asyncio

from pyoverkiz.action_queue import ActionQueueSettings
from pyoverkiz.auth import UsernamePasswordCredentials
from pyoverkiz.client import OverkizClient
from pyoverkiz.client import OverkizClientSettings
from pyoverkiz.enums import OverkizCommand, Server
from pyoverkiz.models import Action, Command

client = OverkizClient(
    server=Server.SOMFY_EUROPE,
    credentials=UsernamePasswordCredentials("user@example.com", "password"),
    settings=OverkizClientSettings(action_queue=ActionQueueSettings()),
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

If you need to tune batching behavior, pass custom values to `ActionQueueSettings`:

```python
import asyncio

from pyoverkiz.action_queue import ActionQueueSettings
from pyoverkiz.client import OverkizClient
from pyoverkiz.client import OverkizClientSettings
from pyoverkiz.auth import UsernamePasswordCredentials
from pyoverkiz.enums import OverkizCommand, Server
from pyoverkiz.models import Action, Command

client = OverkizClient(
    server=Server.SOMFY_EUROPE,
    credentials=UsernamePasswordCredentials("user@example.com", "password"),
    settings=OverkizClientSettings(
        action_queue=ActionQueueSettings(
            delay=0.5,  # seconds to wait before auto-flush
            max_actions=20,  # auto-flush when this count is reached
        ),
    ),
)
```

## `flush_action_queue()` (force immediate execution)

Normally, queued actions are sent after the delay window or when `max_actions` is reached. Call `flush_action_queue()` to force the queue to execute immediately, which is useful when you want to send any pending actions without waiting for the delay timer to expire.

```python
import asyncio

from pyoverkiz.action_queue import ActionQueueSettings
from pyoverkiz.client import OverkizClient
from pyoverkiz.client import OverkizClientSettings
from pyoverkiz.auth import UsernamePasswordCredentials
from pyoverkiz.enums import OverkizCommand, Server
from pyoverkiz.models import Action, Command

client = OverkizClient(
    server=Server.SOMFY_EUROPE,
    credentials=UsernamePasswordCredentials("user@example.com", "password"),
    settings=OverkizClientSettings(
        action_queue=ActionQueueSettings(delay=10.0),  # long delay
    ),
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
from pyoverkiz.action_queue import ActionQueueSettings
from pyoverkiz.client import OverkizClient
from pyoverkiz.client import OverkizClientSettings
from pyoverkiz.auth import UsernamePasswordCredentials
from pyoverkiz.enums import OverkizCommand, Server
from pyoverkiz.models import Action, Command

client = OverkizClient(
    server=Server.SOMFY_EUROPE,
    credentials=UsernamePasswordCredentials("user@example.com", "password"),
    settings=OverkizClientSettings(action_queue=ActionQueueSettings()),
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
