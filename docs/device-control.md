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

# Get the value of a single state
slats_orientation = device.get_state_value(OverkizState.CORE_SLATS_ORIENTATION)
print(f"Orientation: {slats_orientation}")

# Get the value of the first matching state from a list (fallback pattern)
slats_orientation = device.select_first_state_value([OverkizState.CORE_SLATS_ORIENTATION, OverkizState.CORE_SLATE_ORIENTATION])
print(f"Orientation: {slats_orientation}")

# Check if a single state has a non-None value
if device.has_state_value(OverkizState.CORE_SLATS_ORIENTATION):
    print("Device has a slats orientation")

# Check if any of the states have non-None values
if device.has_any_state_value([OverkizState.CORE_SLATS_ORIENTATION, OverkizState.CORE_SLATE_ORIENTATION]):
    print("Device has a slats orientation")
```

#### Get state definition

```python
devices = await client.get_devices()
device = devices[0]

# Get the state definition for a single state
state_def = device.get_state_definition(OverkizState.CORE_OPEN_CLOSED)
if state_def:
    print(f"Type: {state_def.type}")
    print(f"Valid values: {state_def.values}")

# Get the first matching state definition from a list
state_def = device.select_first_state_definition([OverkizState.CORE_OPEN_CLOSED, OverkizState.CORE_SLATS_OPEN_CLOSED])
if state_def:
    print(f"Type: {state_def.type}")
    print(f"Valid values: {state_def.values}")
```

#### Check supported commands

```python
from pyoverkiz.enums import OverkizCommand

devices = await client.get_devices()
device = devices[0]

# Check if device supports a single command
if device.supports_command(OverkizCommand.OPEN):
    print("Device supports open command")

# Check if device supports any of the given commands
if device.supports_any_command([OverkizCommand.OPEN, OverkizCommand.CLOSE]):
    print("Device supports open/close commands")

# Get the first supported command from a list
supported_cmd = device.select_first_command(
    [OverkizCommand.SET_CLOSURE, OverkizCommand.OPEN, OverkizCommand.CLOSE]
)
if supported_cmd:
    print(f"Supported command: {supported_cmd}")
```

#### Get attribute value

```python
devices = await client.get_devices()
device = devices[0]

# Get the value of a single attribute
firmware = device.get_attribute_value(OverkizAttribute.CORE_FIRMWARE_REVISION)
print(f"Firmware: {firmware}")

# Get the value of the first matching attribute from a list
firmware = device.select_first_attribute_value([
    OverkizAttribute.CORE_FIRMWARE_REVISION,
    OverkizAttribute.CORE_MANUFACTURER,
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

## Send a single command to a device

Create an `Action` with the target device URL and one or more `Command` objects, then wrap it in an action group. The method returns an `exec_id` you can use to track or cancel the execution.

```python
from pyoverkiz.enums import OverkizCommand
from pyoverkiz.models import Action, Command

exec_id = await client.execute_action_group(
    actions=[
        Action(
            device_url="io://1234-5678-1234/12345678",
            commands=[
                Command(name=OverkizCommand.SET_CLOSURE, parameters=[50])
            ],
        )
    ],
    label="Set closure to 50%",
)
```

## Send multiple commands to one device

A single action can hold multiple commands. They are executed in order on the device.

```python
from pyoverkiz.enums import OverkizCommand, OverkizCommandParam
from pyoverkiz.models import Action, Command

exec_id = await client.execute_action_group(
    actions=[
        Action(
            device_url="io://1234-5678-1234/12345678",
            commands=[
                Command(
                    name=OverkizCommand.SET_DEROGATION,
                    parameters=[21.5, OverkizCommandParam.FURTHER_NOTICE],
                ),
                Command(
                    name=OverkizCommand.SET_MODE_TEMPERATURE,
                    parameters=[OverkizCommandParam.MANUAL_MODE, 21.5],
                ),
            ],
        )
    ],
    label="Set temperature derogation",
)
```

## Control multiple devices at once

An action group can contain one action per device. All actions in the group are submitted as a single execution.

```python
from pyoverkiz.enums import OverkizCommand
from pyoverkiz.models import Action, Command

exec_id = await client.execute_action_group(
    actions=[
        Action(
            device_url="io://1234-5678-1234/11111111",
            commands=[Command(name=OverkizCommand.CLOSE)],
        ),
        Action(
            device_url="io://1234-5678-1234/22222222",
            commands=[Command(name=OverkizCommand.OPEN)],
        ),
    ],
    label="Close blinds, open garage",
)
```

!!! note
    The gateway allows at most **one action per device** in each action group.
    If you need to send commands to the same device in separate executions, use
    separate `execute_action_group()` calls.

## Execution modes

Pass an `ExecutionMode` to change how the gateway processes the action group:

```python
from pyoverkiz.enums import ExecutionMode, OverkizCommand
from pyoverkiz.models import Action, Command

exec_id = await client.execute_action_group(
    actions=[
        Action(
            device_url="io://1234-5678-1234/12345678",
            commands=[Command(name=OverkizCommand.OPEN)],
        )
    ],
    mode=ExecutionMode.HIGH_PRIORITY,
)
```

Available modes: `HIGH_PRIORITY`, `GEOLOCATED`, `INTERNAL`. When omitted, the default execution mode is used.

## Track and cancel executions

```python
# List all running executions
executions = await client.get_current_executions()

# Get a specific execution
execution = await client.get_current_execution(exec_id)

# Cancel a running execution
await client.cancel_execution(exec_id)

# Review past executions
history = await client.get_execution_history()
```

## Persisted action groups

Action groups can be stored on the server (like saved scenes). Use these methods to list and execute them:

```python
# List all persisted action groups
action_groups = await client.get_action_groups()

for ag in action_groups:
    print(f"{ag.label} (OID: {ag.oid})")

# Execute a persisted action group by OID
exec_id = await client.execute_persisted_action_group(ag.oid)

# Schedule for future execution (Unix timestamp)
trigger_id = await client.schedule_persisted_action_group(ag.oid, timestamp=1735689600)
```

## Limitations and rate limits

Gateways impose limits on how many executions can run or be queued simultaneously. If the execution queue is full, the API will raise an `ExecutionQueueFullError`. Most gateways allow up to 10 concurrent executions.

### Action queue (batching across calls)

If you trigger many action groups in rapid succession, you can enable the action
queue to batch calls within a short window. This reduces API calls and helps
avoid rate limits. See the [Action queue](action-queue.md) guide for setup,
advanced settings, and usage patterns.

### Polling vs event-driven

Polling with `get_devices()` is straightforward but may introduce latency and increase server load. For more immediate updates, consider using event listeners. Refer to the [event handling](event-handling.md) guide for implementation details.
