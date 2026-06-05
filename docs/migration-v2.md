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

`execute_action_group()` is keyword-only — pass `actions=[...]` (and optional `mode=`/`label=`) by name, not positionally.

v2 also supports sending actions to **multiple devices** in a single call and choosing an `ExecutionMode` (`HIGH_PRIORITY`, `GEOLOCATED`, `INTERNAL`). Execution modes are only supported by the Cloud API; the local API rejects them (see [Somfy-TaHoma-Developer-Mode#227](https://github.com/Somfy-Developer/Somfy-TaHoma-Developer-Mode/issues/227)).

### `Command` is no longer a `dict`

In v1, `Command` subclassed `dict`, so you could access its fields by subscript (`command["name"]`) or unpack it. In v2 it is a plain attrs class — use attribute access instead, and call `to_payload()` if you need the serializable dict form.

=== "v1"

    ```python
    command = Command("open", [])
    name = command["name"]          # dict access worked
    ```

=== "v2"

    ```python
    command = Command(name="open")
    name = command.name             # attribute access only
    payload = command.to_payload()  # dict form, if needed
    ```

`Command` also gains an optional `type` field, and `parameters` now accepts `OverkizCommandParam` values in addition to primitives.

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

`get_action_groups()` now returns `list[PersistedActionGroup]` instead of `list[ActionGroup]`. `PersistedActionGroup` extends `ActionGroup` with `oid`, `creation_time`, `last_update_time`, and a read-only `id` property (alias for `oid`). The base `ActionGroup` no longer has these fields.

## Execution methods

| v1 | v2 |
|----|-----|
| `CommandMode` | `ExecutionMode` |
| `client.cancel_command(exec_id)` | `client.cancel_execution(exec_id)` |
| `client.get_current_execution(exec_id)` returns `Execution` | Returns `Execution | None` |
| `Execution.state` is `str` | `Execution.state` is `ExecutionState` |
| `Execution.action_group` is `list[Action]` | `Execution.action_group` is `ActionGroup | None` |

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

### State and attribute access

v2 provides a consistent API on `device.states` and `device.attributes` (both are `States` containers):

| Method | Returns | Purpose |
|--------|---------|---------|
| `.get(name)` | `State \| None` | Single-key lookup |
| `.get_value(name)` | `StateType` | Single-key value (None if missing) |
| `.first(names)` | `State \| None` | First non-None match from fallback list |
| `.first_value(names)` | `StateType` | First non-None value from fallback list |
| `.has_value(name)` | `bool` | Check single state exists with a non-None value |
| `.has_any_value(names)` | `bool` | Check any state exists with a non-None value |
| `name in states` | `bool` | Pure existence check (ignores the value) |

```python
# Get a single state value
temp = device.states.get_value("core:TemperatureState")

# Fallback chain — try multiple state names, return first hit
temp = device.states.first_value(["core:TemperatureState", "core:TemperatureInCelsiusState"])

# Value check — state exists and has a non-None value
if device.states.has_value("core:ClosureState"):
    ...

# Pure existence check (ignores the value)
if "core:ClosureState" in device.states:
    ...

# Same API works for attributes
firmware = device.attributes.get_value("core:FirmwareRevision")
```

### Command helpers

| Method | Purpose |
|--------|---------|
| `device.supports_command(cmd)` | Check single command support |
| `device.supports_any_command(cmds)` | Check any command supported |
| `device.first_command(cmds)` | First supported command from list |
| `device.get_command_definition(cmd)` | Get `CommandDefinition` metadata |

### Definition helpers

`device.definition` is `Definition | None` — always check before accessing. State definitions are available via the `StateDefinitions` container at `device.definition.states`:

```python
if device.definition:
    state_def = device.definition.states.get("core:ClosureState")
    first_def = device.definition.states.first(["core:ClosureState", "core:TargetClosureState"])
    if "core:ClosureState" in device.definition.states:
        ...
```

| Container | Method | Purpose |
|-----------|--------|---------|
| `device.definition.states` | `.get(name)` | Single state definition lookup |
| | `.first(names)` | First matching from list |
| | `.has_any(names)` | Check if any exist |
| | `name in ...` | Membership test |

## Collection lookups (States, CommandDefinitions)

`States.__getitem__` and `CommandDefinitions.__getitem__` now raise `KeyError` when the requested key is not found. In v1 they returned `None`.

=== "v1"

    ```python
    state = device.states["core:ClosureState"]  # returned None if missing
    if state:
        ...
    ```

=== "v2"

    ```python
    # Option 1: use .get() for the old behavior
    state = device.states.get("core:ClosureState")

    # Option 2: use [] and handle KeyError
    try:
        state = device.states["core:ClosureState"]
    except KeyError:
        ...
    ```

## Iterating state and command containers

!!! danger "Silent behavior change"
    `States`, `CommandDefinitions`, and `StateDefinitions` now implement
    `collections.abc.Mapping`. **Iterating them yields keys (`str`), not the
    contained objects.** This change is silent — no exception is raised, your
    loop variable is just a different type than before.

This affects `device.states`, `device.attributes`, `device.definition.states`,
and `device.definition.commands`.

=== "v1"

    ```python
    # Iterating yielded the objects directly
    for state in device.states:
        print(state.name, state.value)

    for definition in device.definition.states:
        print(definition.qualified_name)
    ```

=== "v2"

    ```python
    # Iterating now yields keys (str), like any Mapping
    for name in device.states:
        state = device.states[name]
        print(name, state.value)

    # Use .values() to iterate the objects
    for state in device.states.values():
        print(state.name, state.value)

    for definition in device.definition.states.values():
        print(definition.qualified_name)

    # .keys() / .items() are also available
    for name, state in device.states.items():
        ...
    ```

## Gateway model

- `Gateway.connectivity` is now `Connectivity | None` (was always set in v1).
- `Gateway.id` and `Place.id` are now read-only properties.

## Events

In v1, `Event` was a single flat class that carried every field any event could
possibly have, so every field was optional and present on every event regardless
of its `name`. In v2, `Event` is the base of a **typed hierarchy**: structuring an
event payload returns a concrete subtype chosen by its `name` (e.g.
`DeviceStateChangedEvent`, `ExecutionStateChangedEvent`, `GatewayEvent`,
`FailureEvent`). The base `Event` keeps only the fields common to every event
(`name`, `timestamp`, `setup_oid`, `owning_partners`); everything else lives on
the relevant subtype.

Narrow with `isinstance` before accessing subtype-specific fields:

=== "v1"

    ```python
    for event in events:
        # Every field existed on every Event (None when not applicable)
        if event.device_states:
            ...
    ```

=== "v2"

    ```python
    from pyoverkiz.models import DeviceStateChangedEvent

    for event in events:
        # device_states only exists on DeviceStateChangedEvent
        if isinstance(event, DeviceStateChangedEvent):
            for state in event.device_states:
                ...
    ```

Event names without a dedicated subtype (including any new name the API adds
later) structure into the base `Event`, so unknown events never raise.

### Strict subtypes, resilient batches

Subtypes mark the fields the API is documented to always send for that event as
**required** (no `None` default): `device_url` on device events, `gateway_id` on
gateway events, `zone_oid` on zone events, and `exec_id` / `new_state` /
`old_state` on execution-state events. This means once you have narrowed to a
subtype, those fields are guaranteed non-`None` — no defensive checks needed.

To keep that strictness from making event fetching fragile, structuring degrades
**per event**: if a single payload is missing a required field (an undocumented
API quirk or partial data), that one event falls back to the base `Event` and a
warning is logged — the rest of the batch is unaffected. A flood of such warnings
is a signal that a field marked required should be loosened.

### Removed fields

These v1 `Event` fields are not carried by any v2 event subtype and are no longer
available:

| Field | v1 events that carried it |
|-------|---------------------------|
| `camera_id` | `CameraDiscoveredEvent`, `CameraUploadPhotoEvent` |
| `condition_groupoid` | `ConditionGroup*Event` |
| `deleted_raw_devices_count` | `PurgePartialRawDevicesEvent` |

`failure_type_code` is no longer on failure events either: the API only ever
sends it on `ExecutionStateChangedEvent`, where it remains. The `*FailedEvent`
payloads carry `failure_type` (plus `gateway_id` / `device_url` / `protocol_type`
where applicable), all surfaced on `FailureEvent`.

## Authentication methods

The per-server login helpers on `OverkizClient` have been removed. Authentication is now handled internally by the credential/strategy system — call the single `login()` method, which dispatches to the correct strategy based on the `Credentials` you passed to the constructor.

| v1 | v2 |
|----|-----|
| `client.cozytouch_login()` | `await client.login()` (with the appropriate credentials) |
| `client.nexity_login()` | `await client.login()` |
| `client.somfy_tahoma_get_access_token()` | `await client.login()` |
| `client.refresh_token()` | Handled internally; call `await client.login()` again to re-authenticate |

## Client internals

These changes affect you if you subclass `OverkizClient` or use internal APIs:

| v1 | v2 |
|----|-----|
| `client.check_response(response)` | `from pyoverkiz.response_handler import check_response`; `await check_response(response)` (module-level async function) |
| `client.event_listener_id = ...` | Read-only property; managed internally |
| `SUPPORTED_SERVERS[key] = ...` | `SUPPORTED_SERVERS` is now immutable (`MappingProxyType`) |
| `get_device_definition()` returns `dict` | Returns `Definition | None` |

## Parameter renames

| v1 | v2 |
|----|-----|
| `deviceurl` | `device_url` |
| `Event.setupoid` | `Event.setup_oid` |

Update any keyword arguments and attribute accesses using the old spelling. The `actions`, `owner`, and `source` fields now live on `ExecutionRegisteredEvent` (see [Events](#events)).

## Model defaults

- `Location` address/string fields now default to `None` instead of empty strings.
- `OverkizClient` raises `OverkizError` instead of `ValueError` when server configuration cannot be resolved.
- `obfuscate_sensitive_data()` returns a new dict instead of mutating the input.

## Boolean parsing fix

The Cloud API boolean parser previously mapped the string `"false"` to `True` (because `bool("false")` is truthy in Python). This is now fixed — `"false"` correctly maps to `False`. If your code relied on this incorrect behavior, update it accordingly.

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

??? note "Changed values"

    | Member | v1 value | v2 value |
    |--------|----------|----------|
    | `UNKNOWN` | `unknown` | `Unknown` |

### UIWidget

??? note "Renamed members"

    | v1 | v2 | Note |
    |----|-----|------|
    | `DIMMER_RGBCOLOURED_LIGHT` | `DIMMER_RGB_COLOURED_LIGHT` | |
    | `EWATTCH_TICCOUNTER` | `EWATTCH_TIC_COUNTER` | |
    | `GENERIC_16_CHANNELS_COUNTER` | `GENERIC16_CHANNELS_COUNTER` | |
    | `GENERIC_1_CHANNEL_COUNTER` | `GENERIC1_CHANNEL_COUNTER` | |
    | `IOGENERIC` | `IO_GENERIC` | |
    | `IOSIREN` | `IO_SIREN` | |
    | `IOSTACK` | `IO_STACK` | |
    | `IRBLASTER` | `IR_BLASTER` | |
    | `JSWCAMERA` | `JSW_CAMERA` | |
    | `OVPGENERIC` | `OVP_GENERIC` | |
    | `ROCKER_SWITCHX_1_CONTROLLER` | `ROCKER_SWITCHX1_CONTROLLER` | |
    | `ROCKER_SWITCHX_2_CONTROLLER` | `ROCKER_SWITCHX2_CONTROLLER` | |
    | `ROCKER_SWITCHX_4_CONTROLLER` | `ROCKER_SWITCHX4_CONTROLLER` | |
    | `TSKALARM_CONTROLLER` | `TSK_ALARM_CONTROLLER` | |
    | `VOCSENSOR` | `VOC_SENSOR` | |
    | `ZWAVE_DANFOSS_RSLINK` | `ZWAVE_DANFOSS_RS_LINK` | |
    | `ZWAVE_SEDEVICE_CONFIGURATION` | `ZWAVE_SE_DEVICE_CONFIGURATION` | |

??? note "Changed values"

    | Member | v1 value | v2 value |
    |--------|----------|----------|
    | `UNKNOWN` | `unknown` | `Unknown` |

### OverkizState

??? note "Renamed members"

    | v1 | v2 | Note |
    |----|-----|------|
    | `CORE_HOLIDAYS_MODE_STATE` | `CORE_HOLIDAYS_MODE` | `_STATE` suffix dropped |
    | `CORE_PROGRAMING_AVAILABLE_STATE` | `CORE_PROGRAMMING_AVAILABLE` | Typo fix + `_STATE` suffix dropped |
    | `SOMFY_THERMOSTAT_AT_HOME_TARGET_TEMPERATURE` | `SOMFYTHERMOSTAT_AT_HOME_TARGET_TEMPERATURE` | Prefix `SOMFY_THERMOSTAT_` → `SOMFYTHERMOSTAT_` |
    | `SOMFY_THERMOSTAT_AWAY_MODE_TARGET_TEMPERATURE` | `SOMFYTHERMOSTAT_AWAY_MODE_TARGET_TEMPERATURE` | |
    | `SOMFY_THERMOSTAT_DEROGATION_HEATING_MODE` | `SOMFYTHERMOSTAT_DEROGATION_HEATING_MODE` | |
    | `SOMFY_THERMOSTAT_FREEZE_MODE_TARGET_TEMPERATURE` | `SOMFYTHERMOSTAT_FREEZE_MODE_TARGET_TEMPERATURE` | |
    | `SOMFY_THERMOSTAT_HEATING_MODE` | `SOMFYTHERMOSTAT_HEATING_MODE` | |
    | `SOMFY_THERMOSTAT_SLEEPING_MODE_TARGET_TEMPERATURE` | `SOMFYTHERMOSTAT_SLEEPING_MODE_TARGET_TEMPERATURE` | |

    The underlying state values (e.g. `somfythermostat:HeatingModeState`) are unchanged — only the Python member names changed.

### EventName

??? note "Renamed members"

    | v1 | v2 | Note |
    |----|-----|------|
    | `DELAYED_TRIGGER_SET_EVENT` | `DELAYED_TRIGGER_SET` | `_EVENT` suffix dropped |

### OverkizCommandParam

??? note "Changed values"

    These members kept their names but their string **values** were corrected to match the API. Code comparing against the enum member is unaffected; code comparing against the old hard-coded string must update.

    | Member | v1 value | v2 value |
    |--------|----------|----------|
    | `FURTHER_NOTICE` | `further_notice` | `furtherNotice` |
    | `STANDARD` | `standard` | `Standard` |

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

- `UIProfile` — describes device capabilities (commands + states) at a higher level than raw command names. Auto-generated from the server's `/reference/ui/profiles` endpoint. Accessible via `device.definition.ui_profiles` (a `list[UIProfile]`). See [UI profiles and classifiers](core-concepts.md#ui-profiles-and-classifiers).
- `UIClassifier` — categorizes device types (e.g. `SENSOR`, `EMITTER`, `GENERATOR`). Accessible via `device.definition.ui_classifiers` (a `list[UIClassifier]`).
- `ExecutionState` — typed states for `Execution.state`.
- `UpdateCriticityLevel` — criticity level of gateway updates.

## Dependencies

- `pyhumps` has been removed and replaced with an internal `_case` module. No action needed unless you imported from `pyhumps` directly.
- `cattrs` is a new required dependency (handles model structuring).
- `boto3` and `warrant-lite` are now optional. Install with `pip install "pyoverkiz[nexity]"` if you use the Nexity server.

## Other changes

| v1 | v2 |
|----|-----|
| `Setup.id` always set | `Setup.id` is `None` for Local API |
| `get_diagnostic_data()` | `get_diagnostic_data(mask_sensitive_data=True)` — opt out of PII masking |

## New features in v2

These are not breaking, but worth knowing about when migrating:

- **Client settings** — behavioral configuration is now grouped in `OverkizClientSettings`, passed via the `settings` parameter. This replaces standalone constructor parameters like `action_queue`.
- **Action queue** — batch device executions automatically. See the [action queue guide](action-queue.md).
- **RTS command duration** — override the default execution duration for RTS commands (15–30s) to prevent blocking consecutive commands. See [RTS command duration](device-control.md#rts-command-duration).
- **Device helpers** — `Device.get_command_definition()` for looking up command metadata.
- **Reference endpoints** — query server metadata: `get_reference_ui_classes()`, `get_reference_ui_widgets()`, `get_reference_ui_profile()`, `get_reference_controllable_types()`, etc.
- **Firmware management** — `get_devices_not_up_to_date()`, `get_device_firmware_status()`, `update_device_firmware()`.
- **Optional Nexity dependencies** — `boto3` and `warrant-lite` are no longer installed by default. Install them with `pip install "pyoverkiz[nexity]"` if you use the Nexity server. A clear `ImportError` is raised at login time if the extra is missing.

## `auth_headers` is now async

`AuthStrategy.auth_headers()` and every concrete strategy's implementation are
now coroutines. This only affects code that calls `auth_headers()` directly or
implements a custom `AuthStrategy` — normal `OverkizClient` use is unaffected.

=== "Before"

    ```python
    headers = strategy.auth_headers(path)
    ```

=== "After"

    ```python
    headers = await strategy.auth_headers(path)
    ```

Custom strategies must change the method signature to `async def auth_headers`.
This change lets token-supplied strategies (such as Rexel's
`RexelTokenAuthStrategy`) await an externally-supplied access-token callback per
request instead of caching token state.
