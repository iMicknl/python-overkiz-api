"""Models representing Overkiz API payloads and convenient accessors."""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from typing import Any, cast

from attr import define, field

from pyoverkiz.enums import (
    DataType,
    EventName,
    ExecutionState,
    ExecutionSubType,
    ExecutionType,
    FailureType,
    GatewaySubType,
    GatewayType,
    ProductType,
    UIClass,
    UIWidget,
    UpdateBoxStatus,
)
from pyoverkiz.enums.command import OverkizCommand, OverkizCommandParam
from pyoverkiz.enums.protocol import Protocol
from pyoverkiz.enums.server import APIType, Server
from pyoverkiz.obfuscate import obfuscate_email, obfuscate_id, obfuscate_string
from pyoverkiz.types import DATA_TYPE_TO_PYTHON, StateType

# ---------------------------------------------------------------------------
# State & command primitives
# ---------------------------------------------------------------------------


@define(kw_only=True)
class State:
    """A single device state with typed accessors for its value."""

    name: str
    type: DataType
    value: StateType = None

    @property
    def value_as_int(self) -> int | None:
        """Return the integer value or None if not set; raise on type mismatch."""
        if self.type == DataType.NONE:
            return None
        if self.type == DataType.INTEGER:
            return cast(int, self.value)
        raise TypeError(f"{self.name} is not an integer")

    @property
    def value_as_float(self) -> float | None:
        """Return the float value, allow int->float conversion; raise on type mismatch."""
        if self.type == DataType.NONE:
            return None
        if self.type == DataType.FLOAT:
            return cast(float, self.value)
        if self.type == DataType.INTEGER:
            return float(cast(int, self.value))
        raise TypeError(f"{self.name} is not a float")

    @property
    def value_as_bool(self) -> bool | None:
        """Return the boolean value or raise on type mismatch."""
        if self.type == DataType.NONE:
            return None
        if self.type == DataType.BOOLEAN:
            return cast(bool, self.value)
        raise TypeError(f"{self.name} is not a boolean")

    @property
    def value_as_str(self) -> str | None:
        """Return the string value or raise on type mismatch."""
        if self.type == DataType.NONE:
            return None
        if self.type == DataType.STRING:
            return cast(str, self.value)
        raise TypeError(f"{self.name} is not a string")

    @property
    def value_as_dict(self) -> dict[str, Any] | None:
        """Return the dict value or raise if state is not a JSON object."""
        if self.type == DataType.NONE:
            return None
        if self.type == DataType.JSON_OBJECT:
            return cast(dict, self.value)
        raise TypeError(f"{self.name} is not a JSON object")

    @property
    def value_as_list(self) -> list[Any] | None:
        """Return the list value or raise if state is not a JSON array."""
        if self.type == DataType.NONE:
            return None
        if self.type == DataType.JSON_ARRAY:
            return cast(list, self.value)
        raise TypeError(f"{self.name} is not an array")


@define(kw_only=True)
class EventState(State):
    """State variant used when parsing event payloads (casts string values)."""

    def __attrs_post_init__(self) -> None:
        """Cast string values based on declared data type."""
        # Overkiz (cloud) returns all state values as a string
        # Overkiz (local) returns all state values in the right format
        if not isinstance(self.value, str) or self.type not in DATA_TYPE_TO_PYTHON:
            return

        if self.type in (DataType.JSON_ARRAY, DataType.JSON_OBJECT):
            self.value = self._cast_json_value(self.value)
            return

        caster = DATA_TYPE_TO_PYTHON[self.type]
        self.value = caster(self.value)

    def _cast_json_value(self, raw_value: str) -> StateType:
        """Cast JSON event state values; raise on decode errors."""
        try:
            return json.loads(raw_value)
        except json.JSONDecodeError as err:
            raise ValueError(
                f"Invalid JSON for event state `{self.name}` ({self.type.name}): {err}"
            ) from err


@define(init=False)
class States:
    """Container of State objects providing lookup and mapping helpers."""

    _states: list[State]
    _index: dict[str, State]

    def __init__(self, states: list[State] | None = None) -> None:
        """Create a States container from a list of State objects or empty."""
        self._states = list(states) if states else []
        self._index = {state.name: state for state in self._states}

    def __iter__(self) -> Iterator[State]:
        """Return an iterator over contained State objects."""
        return self._states.__iter__()

    def __contains__(self, name: object) -> bool:
        """Return True if a state with the given name exists in the container."""
        return name in self._index

    def __getitem__(self, name: str) -> State:
        """Return the State with the given name or raise KeyError if missing."""
        return self._index[name]

    def __setitem__(self, name: str, state: State) -> None:
        """Set or append a State identified by name."""
        if name in self._index:
            idx = self._states.index(self._index[name])
            self._states[idx] = state
        else:
            self._states.append(state)
        self._index[name] = state

    def __len__(self) -> int:
        """Return number of states in the container."""
        return len(self._states)

    def get(self, name: str) -> State | None:
        """Return the State with the given name or None if missing."""
        return self._index.get(name)

    def select(self, names: list[str]) -> State | None:
        """Return the first State that exists and has a non-None value, or None."""
        for name in names:
            state = self._index.get(name)
            if state is not None and state.value is not None:
                return state
        return None

    def select_value(self, names: list[str]) -> StateType:
        """Return the value of the first State that exists with a non-None value."""
        if state := self.select(names):
            return state.value
        return None

    def has_any(self, names: list[str]) -> bool:
        """Return True if any of the given state names exist with a non-None value."""
        return self.select(names) is not None


@define(kw_only=True)
class CommandDefinition:
    """Metadata for a single command definition (name and parameter count)."""

    command_name: str
    nparams: int


@define(init=False)
class CommandDefinitions:
    """Container for command definitions providing convenient lookup by name."""

    _commands: list[CommandDefinition]
    _index: dict[str, CommandDefinition]

    def __init__(self, commands: list[CommandDefinition] | None = None) -> None:
        """Build the inner list and index from CommandDefinition objects."""
        self._commands = list(commands) if commands else []
        self._index = {cd.command_name: cd for cd in self._commands}

    def __iter__(self) -> Iterator[CommandDefinition]:
        """Iterate over defined commands."""
        return self._commands.__iter__()

    def __contains__(self, name: object) -> bool:
        """Return True if a command with `name` exists."""
        return name in self._index

    def __getitem__(self, command: str) -> CommandDefinition:
        """Return the command definition or raise KeyError if missing."""
        return self._index[command]

    def __len__(self) -> int:
        """Return number of command definitions."""
        return len(self._commands)

    def get(self, command: str) -> CommandDefinition | None:
        """Return the command definition or None if missing."""
        return self._index.get(command)

    def select(self, commands: list[str | OverkizCommand]) -> str | None:
        """Return the first command name that exists in this definition, or None."""
        return next(
            (str(command) for command in commands if str(command) in self._index), None
        )

    def has_any(self, commands: list[str | OverkizCommand]) -> bool:
        """Return True if any of the given commands exist in this definition."""
        return self.select(commands) is not None


@define(kw_only=True)
class StateDefinition:
    """Definition metadata for a state (qualified name, type and possible values)."""

    qualified_name: str | None = None
    name: str | None = field(default=None, init=True, repr=False, eq=False)
    type: str | None = None
    values: list[str] | None = None
    event_based: bool | None = None

    def __attrs_post_init__(self) -> None:
        """Resolve qualified_name from either `name` or `qualified_name`."""
        if self.qualified_name is None:
            if self.name is not None:
                self.qualified_name = self.name
            else:
                raise ValueError(
                    "StateDefinition requires either `name` or `qualified_name`."
                )


@define(kw_only=True)
class DataProperty:
    """Data property with qualified name and value."""

    qualified_name: str
    value: str


@define(kw_only=True)
class Command:
    """Represents an OverKiz Command."""

    name: str | OverkizCommand
    parameters: list[str | int | float | OverkizCommandParam] | None = None
    type: int | None = None

    def to_payload(self) -> dict[str, object]:
        """Return a JSON-serializable payload for this command.

        The payload uses snake_case keys; the client will convert to camelCase
        and apply small key fixes (like `deviceURL`) before sending.
        """
        payload: dict[str, object] = {"name": str(self.name)}

        if self.type is not None:
            payload["type"] = self.type

        if self.parameters is not None:
            payload["parameters"] = [
                p if isinstance(p, (str, int, float, bool)) else str(p)
                for p in self.parameters
            ]

        return payload


# ---------------------------------------------------------------------------
# Device & definition
# ---------------------------------------------------------------------------


@define(kw_only=True)
class Definition:
    """Definition of device capabilities: command definitions, state definitions and UI hints."""

    commands: CommandDefinitions = field(factory=CommandDefinitions)
    states: list[StateDefinition] = field(factory=list)
    data_properties: list[DataProperty] = field(factory=list)
    widget_name: str | None = None
    ui_class: str | None = None
    qualified_name: str | None = None
    ui_profiles: list[str] | None = None
    ui_classifiers: list[str] | None = None
    type: str | None = None
    attributes: list[dict[str, Any]] | None = None

    def get_state_definition(self, states: list[str]) -> StateDefinition | None:
        """Return the first StateDefinition whose `qualified_name` matches, or None."""
        states_set = set(states)
        for state_def in self.states:
            if state_def.qualified_name in states_set:
                return state_def
        return None

    def has_state_definition(self, states: list[str]) -> bool:
        """Return True if any of the given state definitions exist."""
        return self.get_state_definition(states) is not None


# <protocol>://<gatewayId>/<deviceAddress>[#<subsystemId>]
DEVICE_URL_RE = re.compile(
    r"(?P<protocol>[^:]+)://(?P<gatewayId>[^/]+)/(?P<deviceAddress>[^#]+)(#(?P<subsystemId>\d+))?"
)


@define(kw_only=True)
class DeviceIdentifier:
    """Parsed components from a device URL."""

    protocol: Protocol
    gateway_id: str = field(repr=obfuscate_id)
    device_address: str = field(repr=obfuscate_id)
    subsystem_id: int | None = None
    base_device_url: str = field(repr=obfuscate_id, init=False)

    def __attrs_post_init__(self) -> None:
        """Compute base_device_url from protocol, gateway_id and device_address."""
        self.base_device_url = (
            f"{self.protocol}://{self.gateway_id}/{self.device_address}"
        )

    @property
    def is_sub_device(self) -> bool:
        """Return True if this identifier represents a sub-device (subsystem_id > 1)."""
        return self.subsystem_id is not None and self.subsystem_id > 1

    @classmethod
    def from_device_url(cls, device_url: str) -> DeviceIdentifier:
        """Parse a device URL into its structured identifier components."""
        match = DEVICE_URL_RE.fullmatch(device_url)
        if not match:
            raise ValueError(f"Invalid device URL: {device_url}")

        subsystem_id = (
            int(match.group("subsystemId")) if match.group("subsystemId") else None
        )

        return cls(
            protocol=Protocol(match.group("protocol")),
            gateway_id=match.group("gatewayId"),
            device_address=match.group("deviceAddress"),
            subsystem_id=subsystem_id,
        )


@define(kw_only=True)
class Device:
    """Representation of a device in the setup including parsed fields and states."""

    attributes: States = field(factory=States)
    available: bool
    enabled: bool
    label: str = field(repr=obfuscate_string)
    device_url: str = field(repr=obfuscate_id)
    controllable_name: str
    definition: Definition | None = None
    states: States = field(factory=States)
    type: ProductType
    ui_class: UIClass | None = None
    widget: UIWidget | None = None
    identifier: DeviceIdentifier = field(init=False, repr=False)
    oid: str | None = field(repr=obfuscate_id, default=None)
    place_oid: str | None = None
    creation_time: int | None = None
    last_update_time: int | None = None
    shortcut: bool | None = None
    metadata: str | None = None
    synced: bool | None = None
    subsystem_id: int | None = None

    def __attrs_post_init__(self) -> None:
        """Resolve computed fields from device URL and definition fallbacks."""
        self.identifier = DeviceIdentifier.from_device_url(self.device_url)

        if self.definition:
            if self.ui_class is None and self.definition.ui_class:
                self.ui_class = UIClass(self.definition.ui_class)

            if self.widget is None and self.definition.widget_name:
                self.widget = UIWidget(self.definition.widget_name)

    def supports_command(self, command: str | OverkizCommand) -> bool:
        """Check if device supports a command."""
        return self.definition is not None and str(command) in self.definition.commands

    def supports_any_command(self, commands: list[str | OverkizCommand]) -> bool:
        """Check if device supports any of the commands."""
        return self.definition is not None and self.definition.commands.has_any(
            commands
        )

    def select_first_command(self, commands: list[str | OverkizCommand]) -> str | None:
        """Return first supported command name from list, or None."""
        if self.definition is None:
            return None
        return self.definition.commands.select(commands)

    def get_state_value(self, state: str) -> StateType | None:
        """Get value of a single state, or None if not found or None."""
        return self.states.select_value([state])

    def select_first_state_value(self, states: list[str]) -> StateType | None:
        """Return value of first state with non-None value from list, or None."""
        return self.states.select_value(states)

    def has_state_value(self, state: str) -> bool:
        """Check if a state exists with a non-None value."""
        return self.states.has_any([state])

    def has_any_state_value(self, states: list[str]) -> bool:
        """Check if any of the states exist with non-None values."""
        return self.states.has_any(states)

    def get_state_definition(self, state: str) -> StateDefinition | None:
        """Get StateDefinition for a single state name, or None."""
        if self.definition is None:
            return None
        return self.definition.get_state_definition([state])

    def select_first_state_definition(
        self, states: list[str]
    ) -> StateDefinition | None:
        """Return first matching StateDefinition from list, or None."""
        if self.definition is None:
            return None
        return self.definition.get_state_definition(states)

    def get_attribute_value(self, attribute: str) -> StateType | None:
        """Get value of a single attribute, or None if not found or None."""
        return self.attributes.select_value([attribute])

    def select_first_attribute_value(self, attributes: list[str]) -> StateType | None:
        """Return value of first attribute with non-None value from list, or None."""
        return self.attributes.select_value(attributes)


# ---------------------------------------------------------------------------
# Execution & action groups
# ---------------------------------------------------------------------------


@define(kw_only=True)
class Action:
    """An action consists of multiple commands related to a single device, identified by its device URL."""

    device_url: str
    commands: list[Command] = field(factory=list)

    def to_payload(self) -> dict[str, object]:
        """Return a JSON-serializable payload for this action (snake_case).

        The final camelCase conversion is handled by the client.
        """
        return {
            "device_url": self.device_url,
            "commands": [c.to_payload() for c in self.commands],
        }


@define(kw_only=True)
class ActionGroup:
    """An action group is composed of one or more actions.

    Each action is related to a single setup device (designated by its device URL) and
    is composed of one or more commands to be executed on that device.
    """

    actions: list[Action] = field(factory=list)
    creation_time: int | None = None
    last_update_time: int | None = None
    label: str = field(repr=obfuscate_string, default="")
    metadata: str | None = None
    shortcut: bool | None = None
    notification_type_mask: int | None = None
    notification_condition: str | None = None
    notification_text: str | None = None
    notification_title: str | None = None
    oid: str | None = field(repr=obfuscate_id, default=None)
    id: str | None = field(repr=obfuscate_id, default=None)

    def __attrs_post_init__(self) -> None:
        """Resolve id/oid fallback."""
        if self.label is None:
            self.label = ""
        if self.oid is None and self.id is None:
            raise ValueError("Either 'oid' or 'id' must be provided")
        resolved = cast(str, self.oid or self.id)
        self.id = resolved
        self.oid = resolved


@define(kw_only=True)
class Event:
    """Represents an Overkiz event containing metadata and device states."""

    name: EventName
    timestamp: int | None = None
    setup_oid: str | None = field(repr=obfuscate_id, default=None)
    owner_key: str | None = field(repr=obfuscate_id, default=None)
    type: int | None = None
    sub_type: int | None = None
    time_to_next_state: int | None = None
    failed_commands: list[dict[str, Any]] | None = None
    failure_type_code: FailureType | None = None
    failure_type: str | None = None
    condition_groupoid: str | None = None
    place_oid: str | None = None
    label: str | None = None
    metadata: str | None = None
    camera_id: str | None = None
    deleted_raw_devices_count: int | None = None
    protocol_type: int | None = None
    gateway_id: str | None = field(repr=obfuscate_id, default=None)
    exec_id: str | None = None
    device_url: str | None = field(repr=obfuscate_id, default=None)
    device_states: list[EventState] = field(factory=list)
    old_state: ExecutionState | None = None
    new_state: ExecutionState | None = None
    actions: list[Action] | None = None
    owner: str | None = field(repr=obfuscate_email, default=None)
    source: str | None = None


@define(kw_only=True)
class Execution:
    """Execution occurrence with owner, state and action group metadata."""

    id: str
    description: str
    owner: str = field(repr=obfuscate_email)
    state: str
    action_group: ActionGroup | None = None
    start_time: int | None = None
    execution_type: ExecutionType | None = None
    execution_sub_type: ExecutionSubType | None = None


@define(kw_only=True)
class HistoryExecutionCommand:
    """A command within a recorded historical execution, including its status and parameters."""

    device_url: str = field(repr=obfuscate_id)
    command: str
    rank: int
    dynamic: bool
    state: ExecutionState
    failure_type: str
    parameters: list[Any] | None = None


@define(kw_only=True)
class HistoryExecution:
    """A recorded execution entry containing details and its list of commands."""

    id: str
    event_time: int
    owner: str = field(repr=obfuscate_email)
    source: str
    end_time: int | None = None
    effective_start_time: int | None = None
    duration: int
    label: str | None = None
    type: str
    state: ExecutionState
    failure_type: str
    commands: list[HistoryExecutionCommand] = field(factory=list)
    execution_type: ExecutionType
    execution_sub_type: ExecutionSubType


# ---------------------------------------------------------------------------
# Infrastructure: gateways, places, zones
# ---------------------------------------------------------------------------


@define(kw_only=True)
class Partner:
    """Partner details for a gateway or service provider."""

    activated: bool
    name: str
    id: str = field(repr=obfuscate_id)
    status: str


@define(kw_only=True)
class Connectivity:
    """Connectivity metadata for a gateway update box."""

    status: str
    protocol_version: str


@define(kw_only=True)
class Gateway:
    """Representation of a gateway, including connectivity and partner info."""

    gateway_id: str = field(repr=obfuscate_id)
    connectivity: Connectivity | None = None
    partners: list[Partner] = field(factory=list)
    functions: str | None = None
    sub_type: GatewaySubType | None = None
    alive: bool | None = None
    mode: str | None = None
    place_oid: str | None = None
    time_reliable: bool | None = None
    up_to_date: bool | None = None
    update_status: UpdateBoxStatus | None = None
    sync_in_progress: bool | None = None
    type: GatewayType | None = None
    auto_update_enabled: bool | None = None
    update_criticity_level: str | None = None
    automatic_update: bool | None = None

    @property
    def id(self) -> str:
        """Alias for gateway_id."""
        return self.gateway_id


@define(kw_only=True)
class Feature:
    """Feature flags exposed by a setup or gateway."""

    name: str
    source: str


@define(kw_only=True)
class ZoneItem:
    """An item inside a Zone (device reference)."""

    item_type: str
    device_oid: str
    device_url: str


@define(kw_only=True)
class Zone:
    """A Zone groups related devices inside a place."""

    creation_time: int
    last_update_time: int
    label: str
    type: int
    items: list[ZoneItem] = field(factory=list)
    external_oid: str | None = None
    metadata: str | None = None
    oid: str = ""


@define(kw_only=True)
class Place:
    """Hierarchical representation of a location (house, room, area) in a setup."""

    creation_time: int
    last_update_time: int | None = None
    label: str
    type: int
    oid: str
    sub_places: list[Place] = field(factory=list)

    @property
    def id(self) -> str:
        """Alias for oid."""
        return self.oid


@define(kw_only=True)
class Location:
    """Geographical and address metadata for a Setup."""

    creation_time: int
    last_update_time: int | None = None
    city: str | None = field(repr=obfuscate_string, default=None)
    country: str | None = field(repr=obfuscate_string, default=None)
    postal_code: str | None = field(repr=obfuscate_string, default=None)
    address_line1: str | None = field(repr=obfuscate_string, default=None)
    address_line2: str | None = field(repr=obfuscate_string, default=None)
    timezone: str = ""
    longitude: str | None = field(repr=obfuscate_string, default=None)
    latitude: str | None = field(repr=obfuscate_string, default=None)
    twilight_mode: int = 0
    twilight_angle: str = ""
    twilight_city: str | None = None
    summer_solstice_dusk_minutes: str = ""
    winter_solstice_dusk_minutes: str = ""
    twilight_offset_enabled: bool = False
    dawn_offset: int = 0
    dusk_offset: int = 0
    country_code: str | None = field(repr=obfuscate_string, default=None)
    tariff_settings: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Configuration & options
# ---------------------------------------------------------------------------


@define(kw_only=True)
class OptionParameter:
    """Key/value pair representing option parameter."""

    name: str
    value: str


@define(kw_only=True)
class Option:
    """A subscribed option for a setup including parameters."""

    creation_time: int
    last_update_time: int
    option_id: str
    start_date: int
    parameters: list[OptionParameter] = field(factory=list)


@define(kw_only=True)
class ServerConfig:
    """Connection target details for an Overkiz-compatible server."""

    server: Server | None = None
    name: str
    endpoint: str
    manufacturer: str
    api_type: APIType
    configuration_url: str | None = None


@define(kw_only=True)
class ProtocolType:
    """Protocol type definition from the reference API."""

    id: int
    prefix: str
    name: str
    label: str


# ---------------------------------------------------------------------------
# UI profile definitions (reference API)
# ---------------------------------------------------------------------------


@define(kw_only=True)
class ValuePrototype:
    """Value prototype defining parameter/state value constraints."""

    type: str
    min_value: int | float | None = None
    max_value: int | float | None = None
    enum_values: list[str] | None = None
    description: str | None = None


@define(kw_only=True)
class CommandParameter:
    """Command parameter definition."""

    optional: bool
    sensitive: bool
    value_prototypes: list[ValuePrototype] = field(factory=list)


@define(kw_only=True)
class CommandPrototype:
    """Command prototype defining parameters."""

    parameters: list[CommandParameter] = field(factory=list)


@define(kw_only=True)
class UIProfileCommand:
    """UI profile command definition."""

    name: str
    prototype: CommandPrototype | None = None
    description: str | None = None


@define(kw_only=True)
class StatePrototype:
    """State prototype defining value constraints."""

    value_prototypes: list[ValuePrototype] = field(factory=list)


@define(kw_only=True)
class UIProfileState:
    """UI profile state definition."""

    name: str
    prototype: StatePrototype | None = None
    description: str | None = None


@define(kw_only=True)
class UIProfileDefinition:
    """UI profile definition from the reference API.

    Describes device capabilities through available commands and states.
    """

    name: str
    commands: list[UIProfileCommand] = field(factory=list)
    states: list[UIProfileState] = field(factory=list)
    form_factor: bool = False


# ---------------------------------------------------------------------------
# Setup (root model — references most other models)
# ---------------------------------------------------------------------------


@define(kw_only=True)
class Setup:
    """Representation of a complete setup returned by the Overkiz API."""

    creation_time: int | None = None
    last_update_time: int | None = None
    id: str | None = field(repr=obfuscate_id, default=None)
    location: Location | None = None
    gateways: list[Gateway] = field(factory=list)
    devices: list[Device] = field(factory=list)
    zones: list[Zone] | None = None
    reseller_delegation_type: str | None = None
    oid: str | None = None
    root_place: Place | None = None
    features: list[Feature] | None = None
    disconnection_configuration: dict[str, Any] | None = None
    metadata: str | None = None
