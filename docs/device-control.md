# Device control

All examples assume you are authenticated and have an active session. For details on setting up authentication, see the [Getting Started](getting-started.md) guide.

## List devices

```python
devices = await client.get_devices()

for device in devices:
    print(device.label, device.controllable_name)

    # Access device metadata, including available commands, states, and identifiers:
    print(device.definition)
```

## Read a state value

```python
from pyoverkiz.enums import OverkizState

devices = await client.get_devices()

# For demo purposes we take the first available device
device = devices[0]

availability_state = next(
    (state for state in device.states if state.name == OverkizState.CORE_AVAILABILITY),
    None,
)

print(availability_state.value if availability_state else None)
```

## Send a command

```python
from pyoverkiz.enums import OverkizCommand
from pyoverkiz.models import Action, Command

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
    label="Execution: set closure",
)
```

## Action groups and common patterns

- Use a single action group to batch multiple device commands.

```python
from pyoverkiz.enums import OverkizCommand
from pyoverkiz.models import Action, Command

await client.execute_action_group(
    actions=[
        Action(
            device_url="io://1234-5678-1234/12345678",
            commands=[
                Command(
                    name=OverkizCommand.SET_DEROGATION,
                    parameters=[21.5, OverkizCommandParam.FURTHER_NOTICE],
                )
            ],
        ),
        Action(
            device_url="io://1234-5678-1234/12345678",
            commands=[
                Command(
                    name=OverkizCommand.SET_MODE_TEMPERATURE,
                    parameters=[OverkizCommandParam.MANUAL_MODE, 21.5],
                )
            ],
        )
    ],
    label="Execution: multiple commands",
)

## Limitations and rate limits

Gateways impose limits on how many executions can run or be queued simultaneously. If the execution queue is full, the API will raise an `ExecutionQueueFullException`. Most gateways allow up to 10 concurrent executions.

### Action queue (batching across calls)

If you trigger many action groups in rapid succession, you can enable the action
queue to batch calls within a short window. This reduces API calls and helps
avoid rate limits. See the [Action queue](action-queue.md) guide for setup,
advanced settings, and usage patterns.

### Polling vs event-driven

Polling with `get_devices()` is straightforward but may introduce latency and increase server load. For more immediate updates, consider using event listeners. Refer to the [event handling](event-handling.md) guide for implementation details.
