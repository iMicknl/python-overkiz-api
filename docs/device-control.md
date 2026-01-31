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

# Traditional approach
availability_state = next(
    (state for state in device.states if state.name == OverkizState.CORE_AVAILABILITY),
    None,
)

print(availability_state.value if availability_state else None)
```

### Helper methods for device state queries

The `Device` class provides convenient helper methods for querying device states, commands, and their definitions:

#### Get state value

```python
from pyoverkiz.enums import OverkizState

devices = await client.get_devices()
device = devices[0]

# Get the value of the first matching state
slats_orientation = device.get_state_value([OverkizState.CORE_SLATS_ORIENTATION, OverkizState.CORE_SLATE_ORIENTATION])
print(f"Orientation: {slats_orientation}")

# Check if a state has a non-None value
if device.has_state_value([OverkizState.CORE_SLATS_ORIENTATION, OverkizState.CORE_SLATE_ORIENTATION]):
    print("Device has a slats orientation")
```

#### Get state definition

```python
devices = await client.get_devices()
device = devices[0]

# Get the state definition for querying type, valid values, etc.
state_def = device.get_state_definition([OverkizState.CORE_OPEN_CLOSED, OverkizState.CORE_SLATS_OPEN_CLOSED])
if state_def:
    print(f"Type: {state_def.type}")
    print(f"Valid values: {state_def.values}")
```

#### Check supported commands

```python
from pyoverkiz.enums import OverkizCommand

devices = await client.get_devices()
device = devices[0]

# Check if device supports any of the given commands
if device.has_supported_command([OverkizCommand.OPEN, OverkizCommand.CLOSE]):
    print("Device supports open/close commands")

# Get the first supported command from a list
supported_cmd = device.get_supported_command_name(
    [OverkizCommand.SET_CLOSURE, OverkizCommand.OPEN, OverkizCommand.CLOSE]
)
if supported_cmd:
    print(f"Supported command: {supported_cmd}")
```

#### Get attribute value

```python
devices = await client.get_devices()
device = devices[0]

# Get the value of device attributes (like firmware)
firmware = device.get_attribute_value([
    OverkizAttribute.CORE_FIRMWARE_REVISION,
])
print(f"Firmware: {firmware}")
```

#### Access device identifier

Device URLs are automatically parsed into structured identifier components for easier access:

```python
devices = await client.get_devices()
device = devices[0]

# Access parsed device URL components
print(f"Protocol: {device.identifier.protocol}")
print(f"Gateway ID: {device.identifier.gateway_id}")
print(f"Device address: {device.identifier.device_address}")
print(f"Base device URL: {device.identifier.base_device_url}")

# Check if this is a sub-device
if device.identifier.is_sub_device:
    print(f"Sub-device ID: {device.identifier.subsystem_id}")
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
