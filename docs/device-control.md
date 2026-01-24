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
```

## Polling vs event-driven

Polling with `get_devices()` is straightforward but may introduce latency and increase server load. For more immediate updates, consider using event listeners. Refer to the [event handling](event-handling.md) guide for implementation details.
