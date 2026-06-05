"""Models representing Overkiz API payloads and convenient accessors."""

from __future__ import annotations

import json
import re
from collections.abc import Iterator, Mapping
from typing import Any, cast

from attr import define, field

from pyoverkiz.enums import (
    DataType,
    EventName,
    ExecutionState,
    ExecutionSubType,
    ExecutionType,
    GatewaySubType,
    GatewayType,
    ProductType,
    StateDefinitionType,
    UIClass,
    UIClassifier,
    UIProfile,
    UIWidget,
    UpdateBoxStatus,
    UpdateCriticityLevel,
)
from pyoverkiz.enums.command import OverkizCommand
from pyoverkiz.enums.protocol import Protocol
from pyoverkiz.enums.server import APIType, Server
from pyoverkiz.enums.state import OverkizAttribute, OverkizState
from pyoverkiz.exceptions import OverkizError
from pyoverkiz.obfuscate import obfuscate_email, obfuscate_id, obfuscate_string
from pyoverkiz.types import DATA_TYPE_TO_PYTHON, CommandParameterValue, StateType

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


# States are keyed by core state names (OverkizState) for device.states and by
# attribute names (OverkizAttribute) for device.attributes; both are StrEnum, so
# plain str keys work too.
StateName = str | OverkizState | OverkizAttribute


@define(init=False)
class States(Mapping[str, State]):
    """Container of State objects implementing Mapping[str, State]."""

    _states: list[State]
    _index: dict[str, State]
    _pos: dict[str, int]

    def __init__(self, states: list[State] | None = None) -> None:
        """Create a States container from a list of State objects or empty."""
        self._states = list(states) if states else []
        self._index = {state.name: state for state in self._states}
        self._pos = {state.name: i for i, state in enumerate(self._states)}

    def __iter__(self) -> Iterator[str]:
        """Return an iterator over state names."""
        return iter(self._index)

    def __contains__(self, name: object) -> bool:
        """Return True if a state with the given name exists in the container."""
        return isinstance(name, str) and name in self._index

    def __getitem__(self, name: str) -> State:
        """Return the State with the given name or raise KeyError if missing."""
        try:
            return self._index[name]
        except KeyError as err:
            raise KeyError(f"State {name!r} not found") from err

    def __setitem__(self, name: str, state: State) -> None:
        """Set or append a State identified by name."""
        if state.name != name:
            raise ValueError(f"State name {state.name!r} does not match key {name!r}")
        if name in self._pos:
            self._states[self._pos[name]] = state
        else:
            self._pos[name] = len(self._states)
            self._states.append(state)
        self._index[name] = state

    def __len__(self) -> int:
        """Return number of states in the container."""
        return len(self._states)

    def get_value(self, name: StateName) -> StateType:
        """Return the value of a state by name, or None if missing."""
        state = self._index.get(name)
        if state is not None:
            return state.value
        return None

    def first(self, names: list[StateName]) -> State | None:
        """Return the first State that exists and has a non-None value, or None."""
        for name in names:
            state = self._index.get(name)
            if state is not None and state.value is not None:
                return state
        return None

    def first_value(self, names: list[StateName]) -> StateType:
        """Return the value of the first State with a non-None value, or None."""
        if state := self.first(names):
            return state.value
        return None

    def has_value(self, name: StateName) -> bool:
        """Return True if the state exists and has a non-None value.

        For a pure existence check (ignoring the value), use ``name in states``.
        """
        state = self._index.get(name)
        return state is not None and state.value is not None

    def has_any_value(self, names: list[StateName]) -> bool:
        """Return True if any of the given states exist with a non-None value."""
        return self.first(names) is not None


@define(kw_only=True)
class CommandDefinition:
    """Metadata for a single command definition (name and parameter count)."""

    command_name: str
    nparams: int


@define(init=False)
class CommandDefinitions(Mapping[str, CommandDefinition]):
    """Container for command definitions implementing Mapping[str, CommandDefinition]."""

    _commands: list[CommandDefinition]
    _index: dict[str, CommandDefinition]

    def __init__(self, commands: list[CommandDefinition] | None = None) -> None:
        """Build the inner list and index from CommandDefinition objects."""
        self._commands = list(commands) if commands else []
        self._index = {cd.command_name: cd for cd in self._commands}

    def __iter__(self) -> Iterator[str]:
        """Iterate over command names."""
        return iter(self._index)

    def __contains__(self, name: object) -> bool:
        """Return True if a command with `name` exists."""
        return (
            str(name) in self._index
            if isinstance(name, (str, OverkizCommand))
            else False
        )

    def __getitem__(self, command: str) -> CommandDefinition:
        """Return the command definition or raise KeyError if missing."""
        try:
            return self._index[command]
        except KeyError as err:
            raise KeyError(f"Command {command!r} not found") from err

    def __len__(self) -> int:
        """Return number of command definitions."""
        return len(self._commands)

    def first(self, commands: list[str | OverkizCommand]) -> str | None:
        """Return the first command name that exists in this definition, or None."""
        return next(
            (str(command) for command in commands if str(command) in self._index), None
        )

    def has_any(self, commands: list[str | OverkizCommand]) -> bool:
        """Return True if any of the given commands exist in this definition."""
        return self.first(commands) is not None


@define(kw_only=True)
class StateDefinition:
    """Definition metadata for a state (qualified name, type and possible values)."""

    qualified_name: str | None = None
    name: str | None = field(default=None, init=True, repr=False, eq=False)
    type: StateDefinitionType | None = None
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


@define(init=False)
class StateDefinitions(Mapping[str, StateDefinition]):
    """Container for state definitions implementing Mapping[str, StateDefinition]."""

    _definitions: list[StateDefinition]
    _index: dict[str, StateDefinition]

    def __init__(self, definitions: list[StateDefinition] | None = None) -> None:
        """Build the inner list and index from StateDefinition objects."""
        self._definitions = list(definitions) if definitions else []
        self._index = {
            sd.qualified_name: sd
            for sd in self._definitions
            if sd.qualified_name is not None
        }

    def __iter__(self) -> Iterator[str]:
        """Iterate over qualified names."""
        return iter(self._index)

    def __contains__(self, name: object) -> bool:
        """Return True if a state definition with `name` exists."""
        return isinstance(name, str) and name in self._index

    def __getitem__(self, name: str) -> StateDefinition:
        """Return the state definition or raise KeyError if missing."""
        try:
            return self._index[name]
        except KeyError as err:
            raise KeyError(f"StateDefinition {name!r} not found") from err

    def __len__(self) -> int:
        """Return number of state definitions."""
        return len(self._definitions)

    def first(self, names: list[str | OverkizState]) -> StateDefinition | None:
        """Return the first StateDefinition whose qualified_name matches, or None."""
        for name in names:
            if name in self._index:
                return self._index[name]
        return None

    def has_any(self, names: list[str | OverkizState]) -> bool:
        """Return True if any of the given state definitions exist."""
        return self.first(names) is not None


@define(kw_only=True)
class DataProperty:
    """Data property with qualified name and value."""

    qualified_name: str
    value: str


@define(kw_only=True)
class Command:
    """Represents an OverKiz Command."""

    name: str | OverkizCommand
    parameters: list[CommandParameterValue] | None = None
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
                p if isinstance(p, (str, int, float, bool, dict, list)) else str(p)
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
    states: StateDefinitions = field(factory=StateDefinitions)
    data_properties: list[DataProperty] = field(factory=list)
    widget_name: str | None = None
    ui_class: str | None = None
    qualified_name: str | None = None
    ui_profiles: list[UIProfile] = field(factory=list)
    ui_classifiers: list[UIClassifier] = field(factory=list)
    type: str | None = None
    attributes: list[dict[str, Any]] | None = None


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
            raise OverkizError(f"Invalid device URL: {device_url}")

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
    definition: Definition
    states: States = field(factory=States)
    type: ProductType
    ui_class: UIClass = field(default=None)  # type: ignore[assignment]
    widget: UIWidget = field(default=None)  # type: ignore[assignment]
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

        if self.ui_class is None and self.definition.ui_class:
            self.ui_class = UIClass(self.definition.ui_class)

        if self.widget is None and self.definition.widget_name:
            self.widget = UIWidget(self.definition.widget_name)

        if self.ui_class is None or self.widget is None:
            raise OverkizError(
                f"Device {self.device_url} is missing ui_class or widget"
            )

    def supports_command(self, command: str | OverkizCommand) -> bool:
        """Check if device supports a command."""
        return str(command) in self.definition.commands

    def supports_any_command(self, commands: list[str | OverkizCommand]) -> bool:
        """Check if device supports any of the commands."""
        return self.definition.commands.has_any(commands)

    def first_command(self, commands: list[str | OverkizCommand]) -> str | None:
        """Return first supported command name from list, or None."""
        return self.definition.commands.first(commands)

    def get_command_definition(
        self, command: str | OverkizCommand
    ) -> CommandDefinition | None:
        """Return the CommandDefinition for a command, or None if unavailable."""
        return self.definition.commands.get(str(command))


# ---------------------------------------------------------------------------
# Execution & action groups
# ---------------------------------------------------------------------------


@define(kw_only=True)
class Action:
    """An action consists of multiple commands related to a single device, identified by its device URL."""

    device_url: str = field(repr=obfuscate_id)
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
    label: str | None = field(repr=obfuscate_string, default=None)
    metadata: str | None = None
    shortcut: bool | None = None
    notification_type_mask: int | None = None
    notification_condition: str | None = None
    notification_text: str | None = None
    notification_title: str | None = None


@define(kw_only=True)
class PersistedActionGroup(ActionGroup):
    """A server-persisted action group returned by the /actionGroups endpoint."""

    oid: str = field(repr=obfuscate_id)
    creation_time: int = 0
    last_update_time: int = 0

    @property
    def id(self) -> str:
        """Alias for oid."""
        return self.oid


@define(kw_only=True)
class Event:
    """Base Overkiz event. Carries fields common to every event.

    Concrete events are structured into a subtype based on ``name`` (see the
    discriminator in pyoverkiz.converter). Unknown / unmodeled event names
    structure into this base class.
    """

    name: EventName
    timestamp: int | None = None
    setup_oid: str | None = field(repr=obfuscate_id, default=None)
    owning_partners: list[str] | None = None


@define(kw_only=True)
class DeviceStateChangedEvent(Event):
    """One or more states of a device changed (high-level)."""

    device_url: str = field(repr=obfuscate_id, default="")
    device_states: list[EventState] = field(
        factory=list,
        converter=lambda states: [
            EventState(**s) if isinstance(s, dict) else s for s in states
        ],
    )


@define(kw_only=True)
class Execution:
    """Execution occurrence with owner, state and action group metadata."""

    id: str
    description: str
    owner: str = field(repr=obfuscate_email)
    state: ExecutionState
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
class LocalToken:
    """A local API token for direct gateway access."""

    label: str
    gateway_id: str = field(repr=obfuscate_id)
    uuid: str = field(repr=obfuscate_id)
    scope: str
    gateway_creation_time: int | None = None
    expiration_time: int | None = None


@define(kw_only=True)
class DeveloperMode:
    """Developer mode status for a gateway."""

    active: bool


@define(kw_only=True)
class Gateway:
    """Representation of a gateway, including connectivity and partner info."""

    gateway_id: str = field(repr=obfuscate_id)
    connectivity: Connectivity
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
    update_criticity_level: UpdateCriticityLevel | None = None
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
    timezone: str | None = None
    longitude: str | None = field(repr=obfuscate_string, default=None)
    latitude: str | None = field(repr=obfuscate_string, default=None)
    twilight_mode: int | None = None
    twilight_angle: str | None = None
    twilight_city: str | None = None
    summer_solstice_dusk_minutes: str | None = None
    winter_solstice_dusk_minutes: str | None = None
    twilight_offset_enabled: bool = False
    dawn_offset: int | None = None
    dusk_offset: int | None = None
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
# Device catalog (reference/devices/search API)
# ---------------------------------------------------------------------------


@define(kw_only=True)
class DeviceCommandDefinition:
    """Full command definition from the device catalog."""

    command_name: str
    nparams: int = 0
    description: str | None = None
    prototype: CommandPrototype | None = None
    protocol_specifics: list[dict[str, Any]] | None = None


@define(kw_only=True)
class DeviceStateDefinition:
    """Full state definition from the device catalog."""

    name: str
    type: str | None = None
    event_based: bool = False
    persistent: bool = True
    prototype: StatePrototype | None = None
    protocol_specifics: list[dict[str, Any]] | None = None


@define(kw_only=True)
class DeviceAttributeDefinition:
    """Attribute definition from the device catalog."""

    name: str
    type: int | None = None
    default_value: str | None = None
    protocol_specifics: list[dict[str, Any]] | None = None


@define(kw_only=True)
class ManufacturerReferenceTag:
    """Tag within a manufacturer reference."""

    tag: str
    type: str | None = None


@define(kw_only=True)
class ManufacturerReference:
    """Manufacturer reference from the device catalog."""

    provider: str
    tags: list[ManufacturerReferenceTag] = field(factory=list)


@define(kw_only=True)
class DeviceTypeDefinition:
    """Complete device type definition from the reference devices search."""

    type_id: int | None = None
    subsystem_id: int | None = None
    local_pairing: bool = False
    commands: list[DeviceCommandDefinition] = field(factory=list)
    states: list[DeviceStateDefinition] = field(factory=list)
    attributes: list[DeviceAttributeDefinition] = field(factory=list)
    manufacturer_references: list[ManufacturerReference] = field(factory=list)
    ui_classifiers: list[str] = field(factory=list)
    ui_profiles: list[str] = field(factory=list)
    ui_class: str | None = None
    ui_widget: str | None = None
    controllable_name: str | None = None
    controllable_type: str | None = None
    protocol_type: str | None = None


@define(kw_only=True)
class DeviceSearchResult:
    """Result from POST /reference/devices/search."""

    all_result: bool = True
    devices_types: list[DeviceTypeDefinition] = field(factory=list)


@define(kw_only=True)
class DeviceManufacturerReference:
    """Manufacturer reference for a specific device (setup endpoint)."""

    protocol_type: int | None = None
    provider: str | None = None
    tag: str | None = None
    type: str | None = None


@define(kw_only=True)
class FirmwareStatus:
    """Firmware status of a device."""

    up_to_date: bool
    notes: list[dict[str, str]]


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
