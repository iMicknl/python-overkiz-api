# Migrating from v1 to v2

This guide covers every breaking change in pyOverkiz 2.0 and shows how to update your code.

## Python version

pyOverkiz 2.0 requires **Python 3.12 or later**. If you are on an older version, upgrade Python first.

## Client constructor

The `OverkizClient` constructor is now keyword-only and uses dedicated credential classes instead of positional `username`/`password` arguments.

=== "v1"

    ```python
    from pyoverkiz.client import OverkizClient
    from pyoverkiz.const import SUPPORTED_SERVERS
    from pyoverkiz.enums import Server

    client = OverkizClient("user@example.com", "password", SUPPORTED_SERVERS[Server.SOMFY_EUROPE])
    ```

=== "v2"

    ```python
    from pyoverkiz.auth.credentials import UsernamePasswordCredentials
    from pyoverkiz.client import OverkizClient
    from pyoverkiz.enums import Server

    client = OverkizClient(
        server=Server.SOMFY_EUROPE,
        credentials=UsernamePasswordCredentials("user@example.com", "password"),
    )
    ```

Key differences:

- `server` accepts a `Server` enum, a server key string, or a `ServerConfig` instance directly — no need to look up `SUPPORTED_SERVERS` yourself.
- Authentication details are wrapped in a `Credentials` subclass: `UsernamePasswordCredentials`, `TokenCredentials`, `LocalTokenCredentials`, or `RexelOAuthCodeCredentials`.
- The `token` parameter is removed. Use `TokenCredentials` or `LocalTokenCredentials` instead.

### Local API

=== "v1"

    ```python
    from pyoverkiz.client import OverkizClient
    from pyoverkiz.utils import generate_local_server

    server = generate_local_server(host="gateway-xxxx-xxxx-xxxx.local:8443")
    client = OverkizClient("", "", server, token="your-token")
    ```

=== "v2"

    ```python
    from pyoverkiz.auth.credentials import LocalTokenCredentials
    from pyoverkiz.client import OverkizClient
    from pyoverkiz.utils import create_local_server_config

    client = OverkizClient(
        server=create_local_server_config(host="gateway-xxxx-xxxx-xxxx.local:8443"),
        credentials=LocalTokenCredentials("your-token"),
    )
    ```

## Server configuration

| v1 | v2 |
|----|-----|
| `OverkizServer` | `ServerConfig` |
| `generate_local_server()` | `create_local_server_config()` |
| `client.api_type` | `client.server_config.api_type` |

`ServerConfig` adds a `server` field (the `Server` enum key) and an explicit `api_type` field (`APIType.CLOUD` or `APIType.LOCAL`).

## Executing commands

The command execution API has been consolidated into a single method.

| v1 | v2 |
|----|-----|
| `client.execute_command(device_url, command)` | `client.execute_action_group(actions=[...])` |
| `client.execute_commands(device_url, commands)` | `client.execute_action_group(actions=[...])` |
| `Command` | `Action` wrapping one or more `Command` objects |

=== "v1"

    ```python
    from pyoverkiz.models import Command

    await client.execute_command(
        "io://1234-5678-1234/12345678",
        Command("open", []),
    )
    ```

=== "v2"

    ```python
    from pyoverkiz.models import Action, Command

    await client.execute_action_group(
        actions=[
            Action(
                device_url="io://1234-5678-1234/12345678",
                commands=[Command(name="open")],
            )
        ],
    )
    ```

v2 also supports sending actions to **multiple devices** in a single call and choosing an `ExecutionMode` (`HIGH_PRIORITY`, `GEOLOCATED`, `INTERNAL`).

## Diagnostics

`get_diagnostic_data()` now returns a structured dict with named sections instead of a flat setup dump.

| v1 | v2 |
|----|-----|
| `data["gateways"]` | `data["setup"]["gateways"]` |
| (not available) | `data["action_groups"]` |

=== "v1"

    ```python
    diagnostics = await client.get_diagnostic_data()
    gateways = diagnostics["gateways"]
    ```

=== "v2"

    ```python
    diagnostics = await client.get_diagnostic_data()
    gateways = diagnostics["setup"]["gateways"]
    action_groups = diagnostics["action_groups"]
    ```

## Scenarios → Action groups

| v1 | v2 |
|----|-----|
| `Scenario` | `ActionGroup` |
| `client.get_scenarios()` | `client.get_action_groups()` |
| `client.execute_scenario(oid)` | `client.execute_persisted_action_group(oid)` |
| `client.execute_scheduled_scenario(oid, ts)` | `client.schedule_persisted_action_group(oid, ts)` |

`ActionGroup.id` and `ActionGroup.oid` are now `str | None` instead of `str`. `ActionGroup.creation_time` and `ActionGroup.metadata` are now optional.

## Execution methods

| v1 | v2 |
|----|-----|
| `CommandMode` | `ExecutionMode` |
| `client.cancel_command(exec_id)` | `client.cancel_execution(exec_id)` |
| `client.get_current_execution(exec_id)` returns `Execution` | Returns `Execution | None` |
| `Execution.state` is `str` | `Execution.state` is `ExecutionState` |

## Device model

### Removed fields

- `Device.id` — was a duplicate of `device_url`.
- `Device.data_properties` — was never populated by the API.

### Moved fields

Device URL components are now grouped under `device.identifier`:

| v1 | v2 |
|----|-----|
| `device.protocol` | `device.identifier.protocol` |
| `device.gateway_id` | `device.identifier.gateway_id` |
| `device.device_address` | `device.identifier.device_address` |
| `device.subsystem_id` | `device.identifier.subsystem_id` |
| `device.is_sub_device` | `device.identifier.is_sub_device` |

The identifier also provides `device.identifier.base_device_url`.

### New helper methods

The `Device` class now provides convenience methods — see the [device control guide](device-control.md) for details:

- `device.get_state_value()`, `device.select_first_state_value()`, `device.has_state_value()`
- `device.supports_command()`, `device.supports_any_command()`, `device.select_first_command()`
- `device.get_attribute_value()`, `device.select_first_attribute_value()`
- `device.get_state_definition()`, `device.select_first_state_definition()`

## Exceptions

All exception classes have been renamed from `*Exception` to `*Error` following [PEP 8](https://peps.python.org/pep-0008/#exception-names):

| v1 | v2 |
|----|-----|
| `BaseOverkizException` | `BaseOverkizError` |
| `OverkizException` | `OverkizError` |
| `BadCredentialsException` | `BadCredentialsError` |
| `NotAuthenticatedException` | `NotAuthenticatedError` |
| `TooManyRequestsException` | `TooManyRequestsError` |
| `MaintenanceException` | `MaintenanceError` |
| `NotSuchTokenException` | `NoSuchTokenError` (typo fixed) |
| ... | _(all other exceptions follow the same pattern)_ |

New exception types in v2: `NoSuchDeviceError`, `NoSuchActionGroupError`, `UnsupportedOperationError`.

A quick way to update all imports:

```bash
# Find and replace across your codebase
find . -name "*.py" -exec sed -i '' 's/Exception\b/Error/g' {} +
```

!!! warning
    The sed command above is intentionally broad. Review the result to avoid renaming unrelated exception classes in your own code.

## Enum renames

All enums with an `UNKNOWN` fallback now inherit from `UnknownEnumMixin`. Unrecognized values returned by the API produce an `UNKNOWN` member with a logged warning instead of raising a `ValueError`.

Several enum members have been renamed for consistent `UPPER_SNAKE_CASE` or to fix typos. The tables below list every rename.

### UIClass

??? note "Renamed members"

    | v1 | v2 | Note |
    |----|-----|------|
    | `VENTILATION_SYTEM` | `VENTILATION_SYSTEM` | Typo fix |

### UIWidget

??? note "Renamed members"

    | v1 | v2 | Note |
    |----|-----|------|
    | `CYCLIC_SWINGING_GATE_OPENER` | `CYCLIC_SWINGING_GATE_OPENER` | Trailing space removed from value |
    | `DIMMER_RGBCOLOURED_LIGHT` | `DIMMER_RGB_COLOURED_LIGHT` | |
    | `EWATTCH_TICCOUNTER` | `EWATTCH_TIC_COUNTER` | |
    | `GENERIC_16_CHANNELS_COUNTER` | `GENERIC16_CHANNELS_COUNTER` | |
    | `GENERIC_1_CHANNEL_COUNTER` | `GENERIC1_CHANNEL_COUNTER` | |
    | `IOGENERIC` | `IO_GENERIC` | |
    | `IOSIREN` | `IO_SIREN` | |
    | `IOSTACK` | `IO_STACK` | |
    | `IRBLASTER` | `IR_BLASTER` | |
    | `JSWCAMERA` | `JSW_CAMERA` | |
    | `OPEN_CLOSE_GATE_4T` | `OPEN_CLOSE_GATE4_T` | |
    | `OPEN_CLOSE_SLIDING_GARAGE_DOOR_4T` | `OPEN_CLOSE_SLIDING_GARAGE_DOOR4_T` | |
    | `OPEN_CLOSE_SLIDING_GATE_4T` | `OPEN_CLOSE_SLIDING_GATE4_T` | |
    | `OVPGENERIC` | `OVP_GENERIC` | |
    | `RTS_GENERIC_4T` | `RTS_GENERIC4_T` | |
    | `ROCKER_SWITCHX_1_CONTROLLER` | `ROCKER_SWITCHX1_CONTROLLER` | |
    | `ROCKER_SWITCHX_2_CONTROLLER` | `ROCKER_SWITCHX2_CONTROLLER` | |
    | `ROCKER_SWITCHX_4_CONTROLLER` | `ROCKER_SWITCHX4_CONTROLLER` | |
    | `TSKALARM_CONTROLLER` | `TSK_ALARM_CONTROLLER` | |
    | `UP_DOWN_GARAGE_DOOR_4T` | `UP_DOWN_GARAGE_DOOR4_T` | |
    | `VOCSENSOR` | `VOC_SENSOR` | |
    | `ZWAVE_DANFOSS_RSLINK` | `ZWAVE_DANFOSS_RS_LINK` | |
    | `ZWAVE_SEDEVICE_CONFIGURATION` | `ZWAVE_SE_DEVICE_CONFIGURATION` | |

### Protocol

??? note "New members"

    | Member | Value |
    |--------|-------|
    | `SONOS` | `sonos` |

### GatewaySubType

??? note "New members"

    | Member | Value |
    |--------|-------|
    | `TAHOMA_BOX_C_IO` | `17` |

### New enums in v2

- `UIProfile` — auto-generated from server definitions.
- `UIClassifier` — categorizes device types (e.g. `SENSOR`, `EMITTER`, `GENERATOR`).
- `ExecutionState` — typed states for `Execution.state`.
- `UpdateCriticityLevel` — criticity level of gateway updates.

## Other changes

| v1 | v2 |
|----|-----|
| `Setup.id` always set | `Setup.id` is `None` for Local API |
| `get_diagnostic_data()` | `get_diagnostic_data(mask_sensitive_data=True)` — opt out of PII masking |

## New features in v2

These are not breaking, but worth knowing about when migrating:

- **Client settings** — behavioral configuration is now grouped in `OverkizClientSettings`, passed via the `settings` parameter. This replaces standalone constructor parameters like `action_queue`.
- **Action queue** — batch device executions automatically. See the [action queue guide](action-queue.md).
- **RTS command duration** — automatically inject execution duration into RTS commands to prevent the default 30-second blocking behavior. See [RTS command duration](device-control.md#rts-command-duration).
- **Device helpers** — `Device.get_command_definition()` for looking up command metadata.
- **Reference endpoints** — query server metadata: `get_reference_ui_classes()`, `get_reference_ui_widgets()`, `get_reference_ui_profile()`, `get_reference_controllable_types()`, etc.
- **Firmware management** — `get_devices_not_up_to_date()`, `get_device_firmware_status()`, `update_device_firmware()`.
- **Optional Nexity dependencies** — `boto3` and `warrant-lite` are no longer installed by default. Install them with `pip install pyoverkiz[nexity]` if you use the Nexity server. A clear `ImportError` is raised at login time if the extra is missing.
