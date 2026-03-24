"""Models representing Overkiz API payloads and convenient accessors."""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Any, cast

from attr import Factory, define, field

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

# <protocol>://<gatewayId>/<deviceAddress>[#<subsystemId>]
DEVICE_URL_RE = r"(?P<protocol>.+)://(?P<gatewayId>[^/]+)/(?P<deviceAddress>[^#]+)(#(?P<subsystemId>\d+))?"


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
class OptionParameter:
    """Key/value pair representing option parameter."""

    name: str
    value: str


@define(kw_only=True)
class DataProperty:
    """Data property with qualified name and value."""

    qualified_name: str
    value: str


@define(kw_only=True)
class ProtocolType:
    """Protocol type definition from the reference API."""

    id: int
    prefix: str
    name: str
    label: str


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
    value_prototypes: list[ValuePrototype] = Factory(list)


@define(kw_only=True)
class CommandPrototype:
    """Command prototype defining parameters."""

    parameters: list[CommandParameter] = Factory(list)


@define(kw_only=True)
class StatePrototype:
    """State prototype defining value constraints."""

    value_prototypes: list[ValuePrototype] = Factory(list)


@define(kw_only=True)
class UIProfileCommand:
    """UI profile command definition."""

    name: str
    prototype: CommandPrototype | None = None
    description: str | None = None


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
    commands: list[UIProfileCommand] = Factory(list)
    states: list[UIProfileState] = Factory(list)
    form_factor: bool = False


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


@define(kw_only=True)
class Option:
    """A subscribed option for a setup including parameters."""

    creation_time: int
    last_update_time: int
    option_id: str
    start_date: int
    parameters: list[OptionParameter] = Factory(list)


@define(kw_only=True)
class Zone:
    """A Zone groups related devices inside a place."""

    creation_time: int
    last_update_time: int
    label: str
    type: int
    items: list[ZoneItem] = Factory(list)
    external_oid: str | None = None
    metadata: str | None = None
    oid: str = ""


@define(kw_only=True)
class Gateway:
    """Representation of a gateway, including connectivity and partner info."""

    partners: list[Partner] = Factory(list)
    functions: str | None = None
    sub_type: GatewaySubType | None = None
    id: str = field(repr=obfuscate_id, default="")
    gateway_id: str = field(repr=obfuscate_id, default="")
    alive: bool | None = None
    mode: str | None = None
    place_oid: str | None = None
    time_reliable: bool | None = None
    connectivity: Connectivity = Factory(
        lambda: Connectivity(status="", protocol_version="")  # type: ignore[call-arg]
    )
    up_to_date: bool | None = None
    update_status: UpdateBoxStatus | None = None
    sync_in_progress: bool | None = None
    type: GatewayType | None = None

    def __attrs_post_init__(self) -> None:
        """Mirror gateway_id into id for convenience."""
        if self.gateway_id and not self.id:
            self.id = self.gateway_id
        elif self.id and not self.gateway_id:
            self.gateway_id = self.id


@define(kw_only=True)
class Place:
    """Representation of a place (house/room) in a setup."""

    creation_time: int = 0
    last_update_time: int | None = None
    label: str = ""
    type: int = 0
    id: str = ""
    oid: str = ""
    sub_places: list[Place] = Factory(list)

    def __attrs_post_init__(self) -> None:
        """Mirror oid into id for convenience."""
        if self.oid and not self.id:
            self.id = self.oid


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
    duration: int = 0
    label: str | None = None
    type: str = ""
    state: ExecutionState = ExecutionState.UNKNOWN
    failure_type: str = ""
    commands: list[HistoryExecutionCommand] = Factory(list)
    execution_type: ExecutionType = ExecutionType.UNKNOWN
    execution_sub_type: ExecutionSubType = ExecutionSubType.UNKNOWN


@define(kw_only=True)
class Setup:
    """Representation of a complete setup returned by the Overkiz API."""

    creation_time: int | None = None
    last_update_time: int | None = None
    id: str = field(repr=obfuscate_id, default=None)
    location: Location | None = None
    gateways: list[Gateway] = Factory(list)
    devices: list[Device] = Factory(list)
    zones: list[Zone] | None = None
    reseller_delegation_type: str | None = None
    oid: str | None = None
    root_place: Place | None = None
    features: list[Feature] | None = None


@define(init=False, kw_only=True)
class DeviceIdentifier:
    """Parsed components from a device URL."""

    protocol: Protocol
    gateway_id: str = field(repr=obfuscate_id)
    device_address: str = field(repr=obfuscate_id)
    subsystem_id: int | None = None
    base_device_url: str = field(repr=obfuscate_id, init=False)

    def __init__(
        self,
        *,
        protocol: Protocol,
        gateway_id: str,
        device_address: str,
        subsystem_id: int | None = None,
    ) -> None:
        """Initialize DeviceIdentifier with required URL components."""
        self.protocol = protocol
        self.gateway_id = gateway_id
        self.device_address = device_address
        self.subsystem_id = subsystem_id
        self.base_device_url = f"{protocol}://{gateway_id}/{device_address}"

    @property
    def is_sub_device(self) -> bool:
        """Return True if this identifier represents a sub-device (subsystem_id > 1)."""
        return self.subsystem_id is not None and self.subsystem_id > 1

    @classmethod
    def from_device_url(cls, device_url: str) -> DeviceIdentifier:
        """Parse a device URL into its structured identifier components."""
        match = re.search(DEVICE_URL_RE, device_url)
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


@define(init=False, kw_only=True)
class Device:
    """Representation of a device in the setup including parsed fields and states."""

    attributes: States
    available: bool
    enabled: bool
    label: str = field(repr=obfuscate_string)
    device_url: str = field(repr=obfuscate_id)
    controllable_name: str
    definition: Definition
    states: States
    type: ProductType
    oid: str | None = field(repr=obfuscate_id, default=None)
    place_oid: str | None = None
    creation_time: int | None = None
    last_update_time: int | None = None
    shortcut: bool | None = None
    metadata: str | None = None
    synced: bool | None = None  # Local API only
    subsystem_id: int | None = None  # Local API only
    identifier: DeviceIdentifier = field(init=False, repr=False)
    _ui_class: UIClass | None = field(init=False, repr=False)
    _widget: UIWidget | None = field(init=False, repr=False)

    def __init__(
        self,
        *,
        attributes: list[dict[str, Any]] | None = None,
        available: bool,
        enabled: bool,
        label: str,
        device_url: str,
        controllable_name: str,
        definition: dict[str, Any],
        widget: str | None = None,
        ui_class: str | None = None,
        states: list[dict[str, Any]] | None = None,
        type: int,
        oid: str | None = None,
        place_oid: str | None = None,
        creation_time: int | None = None,
        last_update_time: int | None = None,
        shortcut: bool | None = None,
        metadata: str | None = None,
        synced: bool | None = None,
        subsystem_id: int | None = None,
        **_: Any,
    ) -> None:
        """Initialize Device and parse URL, protocol and nested definitions."""
        self.attributes = States(attributes)
        self.available = available
        self.definition = Definition(**definition)
        self.device_url = device_url
        self.enabled = enabled
        self.label = label
        self.controllable_name = controllable_name
        self.states = States(states)
        self.type = ProductType(type)
        self.oid = oid
        self.place_oid = place_oid
        self.creation_time = creation_time
        self.last_update_time = last_update_time
        self.shortcut = shortcut
        self.metadata = metadata
        self.synced = synced
        self.subsystem_id = subsystem_id

        self.identifier = DeviceIdentifier.from_device_url(device_url)

        self._ui_class = UIClass(ui_class) if ui_class else None
        self._widget = UIWidget(widget) if widget else None

    @property
    def ui_class(self) -> UIClass:
        """Return the UI class, falling back to the definition if available."""
        if self._ui_class is not None:
            return self._ui_class
        if self.definition.ui_class:
            return UIClass(self.definition.ui_class)
        raise ValueError(f"Device {self.device_url} has no UI class defined")

    @property
    def widget(self) -> UIWidget:
        """Return the widget, falling back to the definition if available."""
        if self._widget is not None:
            return self._widget
        if self.definition.widget_name:
            return UIWidget(self.definition.widget_name)
        raise ValueError(f"Device {self.device_url} has no widget defined")

    def supports_command(self, command: str | OverkizCommand) -> bool:
        """Check if device supports a command."""
        return str(command) in self.definition.commands

    def supports_any_command(self, commands: list[str | OverkizCommand]) -> bool:
        """Check if device supports any of the commands."""
        return self.definition.commands.has_any(commands)

    def select_first_command(self, commands: list[str | OverkizCommand]) -> str | None:
        """Return first supported command name from list, or None."""
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
        return self.definition.get_state_definition([state])

    def select_first_state_definition(
        self, states: list[str]
    ) -> StateDefinition | None:
        """Return first matching StateDefinition from list, or None."""
        return self.definition.get_state_definition(states)

    def get_attribute_value(self, attribute: str) -> StateType | None:
        """Get value of a single attribute, or None if not found or None."""
        return self.attributes.select_value([attribute])

    def select_first_attribute_value(self, attributes: list[str]) -> StateType | None:
        """Return value of first attribute with non-None value from list, or None."""
        return self.attributes.select_value(attributes)


@define(init=False, kw_only=True)
class StateDefinition:
    """Definition metadata for a state (qualified name, type and possible values)."""

    qualified_name: str
    type: str | None = None
    values: list[str] | None = None
    event_based: bool | None = None

    def __init__(
        self,
        name: str | None = None,
        qualified_name: str | None = None,
        type: str | None = None,
        values: list[str] | None = None,
        event_based: bool | None = None,
        **_: Any,
    ) -> None:
        """Initialize StateDefinition and set qualified name from either `name` or `qualified_name`."""
        self.type = type
        self.values = values
        self.event_based = event_based

        if qualified_name:
            self.qualified_name = qualified_name
        elif name:
            self.qualified_name = name


@define(init=False, kw_only=True)
class Definition:
    """Definition of device capabilities: command definitions, state definitions and UI hints."""

    commands: CommandDefinitions
    states: list[StateDefinition]
    data_properties: list[DataProperty]
    widget_name: str | None = None
    ui_class: str | None = None
    qualified_name: str | None = None
    ui_profiles: list[str] | None = None
    ui_classifiers: list[str] | None = None
    type: str | None = None
    attributes: list[dict[str, Any]] | None = None  # Local API only

    def __init__(
        self,
        *,
        commands: list[dict[str, Any]],
        states: list[dict[str, Any]] | None = None,
        data_properties: list[dict[str, Any]] | None = None,
        widget_name: str | None = None,
        ui_class: str | None = None,
        qualified_name: str | None = None,
        ui_profiles: list[str] | None = None,
        ui_classifiers: list[str] | None = None,
        type: str | None = None,
        attributes: list[dict[str, Any]] | None = None,
        **_: Any,
    ) -> None:
        """Initialize Definition and construct nested command/state definitions."""
        self.commands = CommandDefinitions(commands)
        self.states = [StateDefinition(**sd) for sd in states] if states else []
        self.data_properties = (
            [DataProperty(**dp) for dp in data_properties] if data_properties else []
        )
        self.widget_name = widget_name
        self.ui_class = ui_class
        self.qualified_name = qualified_name
        self.ui_profiles = ui_profiles
        self.ui_classifiers = ui_classifiers
        self.type = type
        self.attributes = attributes

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


@define(init=False, kw_only=True)
class CommandDefinition:
    """Metadata for a single command definition (name and parameter count)."""

    command_name: str
    nparams: int

    def __init__(self, command_name: str, nparams: int, **_: Any) -> None:
        """Initialize CommandDefinition."""
        self.command_name = command_name
        self.nparams = nparams


@define(init=False)
class CommandDefinitions:
    """Container for command definitions providing convenient lookup by name."""

    _commands: list[CommandDefinition]

    def __init__(self, commands: list[dict[str, Any]]):
        """Build the inner list of CommandDefinition objects from raw data."""
        self._commands = [CommandDefinition(**command) for command in commands]

    def __iter__(self) -> Iterator[CommandDefinition]:
        """Iterate over defined commands."""
        return self._commands.__iter__()

    def __contains__(self, name: str) -> bool:
        """Return True if a command with `name` exists."""
        return self.__getitem__(name) is not None

    def __getitem__(self, command: str) -> CommandDefinition | None:
        """Return the command definition or None if missing."""
        return next((cd for cd in self._commands if cd.command_name == command), None)

    def __len__(self) -> int:
        """Return number of command definitions."""
        return len(self._commands)

    get = __getitem__

    def select(self, commands: list[str | OverkizCommand]) -> str | None:
        """Return the first command name that exists in this definition, or None."""
        return next(
            (str(command) for command in commands if str(command) in self), None
        )

    def has_any(self, commands: list[str | OverkizCommand]) -> bool:
        """Return True if any of the given commands exist in this definition."""
        return self.select(commands) is not None


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
    """State variant used when parsing event payloads.

    The cloud API returns all state values as strings. This subclass casts
    them to the appropriate Python type based on the declared DataType.
    The local API returns properly typed values, which pass through unchanged.
    """

    def __attrs_post_init__(self) -> None:
        """Cast string values to the declared data type."""
        if isinstance(self.value, str) and self.type in DATA_TYPE_TO_PYTHON:
            self.value = DATA_TYPE_TO_PYTHON[self.type](self.value)


@define(init=False)
class States:
    """Container of State objects providing lookup and mapping helpers."""

    _states: list[State]

    def __init__(self, states: list[dict[str, Any]] | None = None) -> None:
        """Create a container of State objects from raw state dicts or an empty list."""
        if states:
            self._states = [State(**state) for state in states]
        else:
            self._states = []

    def __iter__(self) -> Iterator[State]:
        """Return an iterator over contained State objects."""
        return self._states.__iter__()

    def __contains__(self, name: str) -> bool:
        """Return True if a state with the given name exists in the container."""
        return self.__getitem__(name) is not None

    def __getitem__(self, name: str) -> State | None:
        """Return the State with the given name or None if missing."""
        return next((state for state in self._states if state.name == name), None)

    def __setitem__(self, name: str, state: State) -> None:
        """Set or append a State identified by name."""
        found = self.__getitem__(name)
        if found is None:
            self._states.append(state)
        else:
            self._states[self._states.index(found)] = state

    def __len__(self) -> int:
        """Return number of states in the container."""
        return len(self._states)

    get = __getitem__

    def select(self, names: list[str]) -> State | None:
        """Return the first State that exists and has a non-None value, or None."""
        for name in names:
            if (state := self[name]) and state.value is not None:
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


@define(init=False, kw_only=True)
class Command:
    """Represents an OverKiz Command."""

    type: int | None = None
    name: str | OverkizCommand
    parameters: list[str | int | float | OverkizCommandParam] | None

    def __init__(
        self,
        name: str | OverkizCommand,
        parameters: list[str | int | float | OverkizCommandParam] | None = None,
        type: int | None = None,
        **_: Any,
    ):
        """Initialize a command instance and mirror fields into dict base class."""
        self.name = name
        self.parameters = parameters
        self.type = type

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


@define(kw_only=True)
class Event:
    """Represents an Overkiz event containing metadata and device states."""

    name: EventName
    timestamp: int | None = None
    setupoid: str | None = field(repr=obfuscate_id, default=None)
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
    metadata: Any | None = None
    camera_id: str | None = None
    deleted_raw_devices_count: Any | None = None
    protocol_type: Any | None = None
    gateway_id: str | None = field(repr=obfuscate_id, default=None)
    exec_id: str | None = None
    device_url: str | None = field(repr=obfuscate_id, default=None)
    device_states: list[EventState] = Factory(list)
    old_state: ExecutionState | None = None
    new_state: ExecutionState | None = None


@define(kw_only=True)
class Execution:
    """Execution occurrence with owner, state and action group metadata."""

    id: str
    description: str
    owner: str = field(repr=obfuscate_email)
    state: str
    action_group: ActionGroup


@define(init=False, kw_only=True)
class Action:
    """An action consists of multiple commands related to a single device, identified by its device URL."""

    device_url: str
    commands: list[Command]

    def __init__(self, device_url: str, commands: list[dict[str, Any] | Command]):
        """Initialize Action from API data and convert nested commands."""
        self.device_url = device_url
        self.commands = [
            c if isinstance(c, Command) else Command(**c) for c in commands
        ]

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

    id: str = field(repr=obfuscate_id, default="")
    creation_time: int | None = None
    last_update_time: int | None = None
    label: str = field(repr=obfuscate_string, default="")
    metadata: str | None = None
    shortcut: bool | None = None
    notification_type_mask: int | None = None
    notification_condition: str | None = None
    notification_text: str | None = None
    notification_title: str | None = None
    actions: list[Action] = Factory(list)
    oid: str = field(repr=obfuscate_id, default="")

    def __attrs_post_init__(self) -> None:
        """Mirror oid/id for convenience and ensure at least one is set."""
        if self.oid and not self.id:
            self.id = self.oid
        elif self.id and not self.oid:
            self.oid = self.id


@define(kw_only=True)
class ServerConfig:
    """Connection target details for an Overkiz-compatible server."""

    server: Server | None
    name: str
    endpoint: str
    manufacturer: str
    type: APIType
    configuration_url: str | None = None

    def __init__(
        self,
        *,
        server: Server | str | None = None,
        name: str,
        endpoint: str,
        manufacturer: str,
        type: str | APIType,
        configuration_url: str | None = None,
        **_: Any,
    ) -> None:
        """Initialize ServerConfig and convert enum fields."""
        self.server = (
            server if isinstance(server, Server) or server is None else Server(server)
        )
        self.name = name
        self.endpoint = endpoint
        self.manufacturer = manufacturer
        self.type = type if isinstance(type, APIType) else APIType(type)
        self.configuration_url = configuration_url


def _register_custom_init_models() -> None:
    """Register models that have a custom ``__init__`` with the cattrs converter.

    Without this, cattrs would auto-structure these by introspecting
    their attrs fields, which fails because their ``__init__`` accepts
    different parameters than the field definitions.
    """
    from pyoverkiz.converters import converter

    for cls in [
        DeviceIdentifier,
        Device,
        StateDefinition,
        Definition,
        CommandDefinition,
        CommandDefinitions,
        States,
        Command,
        Action,
        ServerConfig,
    ]:
        converter.register_structure_hook(
            cls,
            lambda d, _, c=cls: c(**d) if isinstance(d, dict) else d,
        )


_register_custom_init_models()
