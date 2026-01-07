"""Models representing Overkiz API payloads and convenient accessors."""

from __future__ import annotations

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
from pyoverkiz.enums.protocol import Protocol
from pyoverkiz.obfuscate import obfuscate_email, obfuscate_id, obfuscate_string
from pyoverkiz.types import DATA_TYPE_TO_PYTHON, StateType

# pylint: disable=unused-argument, too-many-instance-attributes, too-many-locals

# <protocol>://<gatewayId>/<deviceAddress>[#<subsystemId>]
DEVICE_URL_RE = r"(?P<protocol>.+)://(?P<gatewayId>[^/]+)/(?P<deviceAddress>[^#]+)(#(?P<subsystemId>\d+))?"


@define(init=False, kw_only=True)
class Setup:
    """Representation of a complete setup returned by the Overkiz API."""

    creation_time: str | None = None
    last_update_time: str | None = None
    id: str = field(repr=obfuscate_id, default=None)
    location: Location | None = None
    gateways: list[Gateway]
    devices: list[Device]
    zones: list[Zone] | None = None
    reseller_delegation_type: str | None = None
    oid: str | None = None
    root_place: Place | None = None
    features: list[Feature] | None = None

    def __init__(
        self,
        *,
        creation_time: str | None = None,
        last_update_time: str | None = None,
        id: str = field(repr=obfuscate_id, default=None),
        location: dict[str, Any] | None = None,
        gateways: list[dict[str, Any]],
        devices: list[dict[str, Any]],
        zones: list[dict[str, Any]] | None = None,
        reseller_delegation_type: str | None = None,
        oid: str | None = None,
        root_place: dict[str, Any] | None = None,
        features: list[dict[str, Any]] | None = None,
        **_: Any,
    ) -> None:
        """Initialize a Setup and construct nested model instances."""
        self.id = id
        self.creation_time = creation_time
        self.last_update_time = last_update_time
        self.location = Location(**location) if location else None
        self.gateways = [Gateway(**g) for g in gateways]
        self.devices = [Device(**d) for d in devices]
        self.zones = [Zone(**z) for z in zones] if zones else None
        self.reseller_delegation_type = reseller_delegation_type
        self.oid = oid
        self.root_place = Place(**root_place) if root_place else None
        self.features = [Feature(**f) for f in features] if features else None


@define(init=False, kw_only=True)
class Location:
    """Geographical and address metadata for a Setup."""

    creation_time: str
    last_update_time: str | None = None
    city: str = field(repr=obfuscate_string, default=None)
    country: str = field(repr=obfuscate_string, default=None)
    postal_code: str = field(repr=obfuscate_string, default=None)
    address_line1: str = field(repr=obfuscate_string, default=None)
    address_line2: str = field(repr=obfuscate_string, default=None)
    timezone: str
    longitude: str = field(repr=obfuscate_string, default=None)
    latitude: str = field(repr=obfuscate_string, default=None)
    twilight_mode: int
    twilight_angle: str
    twilight_city: str | None = None
    summer_solstice_dusk_minutes: str
    winter_solstice_dusk_minutes: str
    twilight_offset_enabled: bool
    dawn_offset: int
    dusk_offset: int

    def __init__(
        self,
        *,
        creation_time: str,
        last_update_time: str | None = None,
        city: str = field(repr=obfuscate_string, default=None),
        country: str = field(repr=obfuscate_string, default=None),
        postal_code: str = field(repr=obfuscate_string, default=None),
        address_line1: str = field(repr=obfuscate_string, default=None),
        address_line2: str = field(repr=obfuscate_string, default=None),
        timezone: str,
        longitude: str = field(repr=obfuscate_string, default=None),
        latitude: str = field(repr=obfuscate_string, default=None),
        twilight_mode: int,
        twilight_angle: str,
        twilight_city: str | None = None,
        summer_solstice_dusk_minutes: str,
        winter_solstice_dusk_minutes: str,
        twilight_offset_enabled: bool,
        dawn_offset: int,
        dusk_offset: int,
        **_: Any,
    ) -> None:
        """Initialize Location with address and timezone information."""
        self.creation_time = creation_time
        self.last_update_time = last_update_time
        self.city = city
        self.country = country
        self.postal_code = postal_code
        self.address_line1 = address_line1
        self.address_line2 = address_line2
        self.timezone = timezone
        self.longitude = longitude
        self.latitude = latitude
        self.twilight_mode = twilight_mode
        self.twilight_angle = twilight_angle
        self.twilight_city = twilight_city
        self.summer_solstice_dusk_minutes = summer_solstice_dusk_minutes
        self.winter_solstice_dusk_minutes = winter_solstice_dusk_minutes
        self.twilight_offset_enabled = twilight_offset_enabled
        self.dawn_offset = dawn_offset
        self.dusk_offset = dusk_offset


@define(init=False, kw_only=True)
class Device:
    """Representation of a device in the setup including parsed fields and states."""

    id: str = field(repr=False)
    attributes: States
    available: bool
    enabled: bool
    label: str = field(repr=obfuscate_string)
    device_url: str = field(repr=obfuscate_id)
    gateway_id: str | None = field(repr=obfuscate_id)
    device_address: str | None = field(repr=obfuscate_id)
    subsystem_id: int | None = None
    is_sub_device: bool = False
    controllable_name: str
    definition: Definition
    data_properties: list[dict[str, Any]] | None = None
    widget: UIWidget
    ui_class: UIClass
    states: States
    type: ProductType
    place_oid: str | None = None
    protocol: Protocol | None = field(init=False, repr=False)

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
        data_properties: list[dict[str, Any]] | None = None,
        widget: str | None = None,
        widget_name: str | None = None,
        ui_class: str | None = None,
        states: list[dict[str, Any]] | None = None,
        type: int,
        place_oid: str | None = None,
        **_: Any,
    ) -> None:
        """Initialize Device and parse URL, protocol and nested definitions."""
        self.id = device_url
        self.attributes = States(attributes)
        self.available = available
        self.definition = Definition(**definition)
        self.device_url = device_url
        self.enabled = enabled
        self.label = label
        self.controllable_name = controllable_name
        self.states = States(states)
        self.data_properties = data_properties
        self.type = ProductType(type)
        self.place_oid = place_oid

        self.protocol = None
        self.gateway_id = None
        self.device_address = None
        self.subsystem_id = None
        self.is_sub_device = False

        # Split <protocol>://<gatewayId>/<deviceAddress>[#<subsystemId>] into multiple variables
        match = re.search(DEVICE_URL_RE, device_url)

        if match:
            self.protocol = Protocol(match.group("protocol"))
            self.gateway_id = match.group("gatewayId")
            self.device_address = match.group("deviceAddress")

            if match.group("subsystemId"):
                self.subsystem_id = int(match.group("subsystemId"))
                self.is_sub_device = self.subsystem_id > 1

        if ui_class:
            self.ui_class = UIClass(ui_class)
        elif self.definition.ui_class:
            self.ui_class = UIClass(self.definition.ui_class)

        if widget:
            self.widget = UIWidget(widget)
        elif self.definition.widget_name:
            self.widget = UIWidget(self.definition.widget_name)


@define(init=False, kw_only=True)
class StateDefinition:
    """Definition metadata for a state (qualified name, type and possible values)."""

    qualified_name: str
    type: str | None = None
    values: list[str] | None = None

    def __init__(
        self,
        name: str | None = None,
        qualified_name: str | None = None,
        type: str | None = None,
        values: list[str] | None = None,
        **_: Any,
    ) -> None:
        """Initialize StateDefinition and set qualified name from either `name` or `qualified_name`."""
        self.type = type
        self.values = values

        if qualified_name:
            self.qualified_name = qualified_name
        elif name:
            self.qualified_name = name


@define(init=False, kw_only=True)
class Definition:
    """Definition of device capabilities: command definitions, state definitions and UI hints."""

    commands: CommandDefinitions
    states: list[StateDefinition]
    widget_name: str | None = None
    ui_class: str | None = None
    qualified_name: str | None = None

    def __init__(
        self,
        *,
        commands: list[dict[str, Any]],
        states: list[dict[str, Any]] | None = None,
        widget_name: str | None = None,
        ui_class: str | None = None,
        qualified_name: str | None = None,
        **_: Any,
    ) -> None:
        """Initialize Definition and construct nested command/state definitions."""
        self.commands = CommandDefinitions(commands)
        self.states = [StateDefinition(**sd) for sd in states] if states else []
        self.widget_name = widget_name
        self.ui_class = ui_class
        self.qualified_name = qualified_name


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


@define(init=False, kw_only=True)
class State:
    """A single device state with typed accessors for its value."""

    name: str
    type: DataType
    value: StateType

    def __init__(
        self,
        name: str,
        type: int,
        value: StateType = None,
        **_: Any,
    ) -> None:
        """Initialize State and set its declared data type."""
        self.name = name
        self.value = value
        self.type = DataType(type)

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


@define(init=False, kw_only=True)
class EventState(State):
    """State variant used when parsing event payloads (casts string values)."""

    def __init__(
        self,
        name: str,
        type: int,
        value: str | None = None,
        **_: Any,
    ):
        """Initialize EventState and cast string values based on declared data type."""
        super().__init__(name, type, value, **_)

        # Overkiz (cloud) returns all state values as a string
        # We cast them here based on the data type provided by Overkiz
        # Overkiz (local) returns all state values in the right format
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


class Command(dict):
    """Represents an OverKiz Command."""

    name: str
    parameters: list[str | int | float] | None

    def __init__(
        self, name: str, parameters: list[str | int | float] | None = None, **_: Any
    ):
        """Initialize a command instance and mirror fields into dict base class."""
        self.name = name
        self.parameters = parameters
        dict.__init__(self, name=name, parameters=parameters)


@define(init=False, kw_only=True)
class Event:
    """Represents an Overkiz event containing metadata and device states."""

    name: EventName
    timestamp: int | None
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
    device_states: list[EventState]
    old_state: ExecutionState | None = None
    new_state: ExecutionState | None = None

    def __init__(
        self,
        name: EventName,
        timestamp: int | None = None,
        setupoid: str | None = field(repr=obfuscate_id, default=None),
        owner_key: str | None = None,
        type: int | None = None,
        sub_type: int | None = None,
        time_to_next_state: int | None = None,
        failed_commands: list[dict[str, Any]] | None = None,
        failure_type_code: FailureType | None = None,
        failure_type: str | None = None,
        condition_groupoid: str | None = None,
        place_oid: str | None = None,
        label: str | None = None,
        metadata: Any | None = None,
        camera_id: str | None = None,
        deleted_raw_devices_count: Any | None = None,
        protocol_type: Any | None = None,
        gateway_id: str | None = None,
        exec_id: str | None = None,
        device_url: str | None = None,
        device_states: list[dict[str, Any]] | None = None,
        old_state: ExecutionState | None = None,
        new_state: ExecutionState | None = None,
        **_: Any,
    ):
        """Initialize Event from raw Overkiz payload fields."""
        self.timestamp = timestamp
        self.gateway_id = gateway_id
        self.exec_id = exec_id
        self.device_url = device_url
        self.device_states = (
            [EventState(**s) for s in device_states] if device_states else []
        )
        self.old_state = ExecutionState(old_state) if old_state else None
        self.new_state = ExecutionState(new_state) if new_state else None
        self.setupoid = setupoid
        self.owner_key = owner_key
        self.type = type
        self.sub_type = sub_type
        self.time_to_next_state = time_to_next_state
        self.failed_commands = failed_commands

        self.failure_type = failure_type
        self.condition_groupoid = condition_groupoid
        self.place_oid = place_oid
        self.label = label
        self.metadata = metadata
        self.camera_id = camera_id
        self.deleted_raw_devices_count = deleted_raw_devices_count
        self.protocol_type = protocol_type
        self.name = EventName(name)
        self.failure_type_code = (
            None if failure_type_code is None else FailureType(failure_type_code)
        )


@define(init=False, kw_only=True)
class Execution:
    """Execution occurrence with owner, state and action group metadata."""

    id: str
    description: str
    owner: str = field(repr=obfuscate_email)
    state: str
    action_group: list[dict[str, Any]]

    def __init__(
        self,
        id: str,
        description: str,
        owner: str,
        state: str,
        action_group: list[dict[str, Any]],
        **_: Any,
    ):
        """Initialize Execution object from API fields."""
        self.id = id
        self.description = description
        self.owner = owner
        self.state = state
        self.action_group = action_group


@define(init=False, kw_only=True)
class Action:
    """An action consists of multiple commands related to a single device, identified by its device URL."""

    device_url: str
    commands: list[Command]

    def __init__(self, device_url: str, commands: list[dict[str, Any]]):
        """Initialize Action from API data and convert nested commands."""
        self.device_url = device_url
        self.commands = [Command(**c) for c in commands] if commands else []


@define(init=False, kw_only=True)
class Scenario:
    """An action group is composed of one or more actions.

    Each action is related to a single setup device (designated by its device URL) and
    is composed of one or more commands to be executed on that device.
    """

    id: str = field(repr=obfuscate_id)
    creation_time: int
    last_update_time: int | None = None
    label: str = field(repr=obfuscate_string)
    metadata: str | None = None
    shortcut: bool | None = None
    notification_type_mask: int | None = None
    notification_condition: str | None = None
    notification_text: str | None = None
    notification_title: str | None = None
    actions: list[Action]
    oid: str = field(repr=obfuscate_id)

    def __init__(
        self,
        creation_time: int,
        actions: list[dict[str, Any]],
        oid: str,
        metadata: str | None = None,
        last_update_time: int | None = None,
        label: str | None = None,
        shortcut: bool | None = None,
        notification_type_mask: int | None = None,
        notification_condition: str | None = None,
        notification_text: str | None = None,
        notification_title: str | None = None,
        **_: Any,
    ) -> None:
        """Initialize Scenario (action group) from API data."""
        self.id = oid
        self.creation_time = creation_time
        self.last_update_time = last_update_time
        self.label = (
            label or ""
        )  # for backwards compatibility we set label to empty string if None
        self.metadata = metadata
        self.shortcut = shortcut
        self.notification_type_mask = notification_type_mask
        self.notification_condition = notification_condition
        self.notification_text = notification_text
        self.notification_title = notification_title
        self.actions = [Action(**action) for action in actions]
        self.oid = oid


@define(init=False, kw_only=True)
class Partner:
    """Partner details for a gateway or service provider."""

    activated: bool
    name: str
    id: str = field(repr=obfuscate_id)
    status: str

    def __init__(self, activated: bool, name: str, id: str, status: str, **_: Any):
        """Initialize Partner information."""
        self.activated = activated
        self.name = name
        self.id = id
        self.status = status


@define(init=False, kw_only=True)
class Connectivity:
    """Connectivity metadata for a gateway update box."""

    status: str
    protocol_version: str

    def __init__(self, status: str, protocol_version: str, **_: Any):
        """Initialize Connectivity information."""
        self.status = status
        self.protocol_version = protocol_version


@define(init=False, kw_only=True)
class Gateway:
    """Representation of a gateway, including connectivity and partner info."""

    partners: list[Partner]
    functions: str | None = None
    sub_type: GatewaySubType | None = None
    id: str = field(repr=obfuscate_id)
    gateway_id: str = field(repr=obfuscate_id)
    alive: bool | None = None
    mode: str | None = None
    place_oid: str | None = None
    time_reliable: bool | None = None
    connectivity: Connectivity
    up_to_date: bool | None = None
    update_status: UpdateBoxStatus | None = None
    sync_in_progress: bool | None = None
    type: GatewayType | None = None

    def __init__(
        self,
        *,
        partners: list[dict[str, Any]] | None = None,
        functions: str | None = None,
        sub_type: GatewaySubType | None = None,
        gateway_id: str,
        alive: bool | None = None,
        mode: str | None = None,
        place_oid: str | None = None,
        time_reliable: bool | None = None,
        connectivity: dict[str, Any],
        up_to_date: bool | None = None,
        update_status: UpdateBoxStatus | None = None,
        sync_in_progress: bool | None = None,
        type: GatewayType | None = None,
        **_: Any,
    ) -> None:
        """Initialize Gateway from API data and child objects."""
        self.id = gateway_id
        self.gateway_id = gateway_id
        self.functions = functions
        self.alive = alive
        self.mode = mode
        self.place_oid = place_oid
        self.time_reliable = time_reliable
        self.connectivity = Connectivity(**connectivity)
        self.up_to_date = up_to_date
        self.update_status = UpdateBoxStatus(update_status) if update_status else None
        self.sync_in_progress = sync_in_progress
        self.partners = [Partner(**p) for p in partners] if partners else []
        self.type = GatewayType(type) if type else None
        self.sub_type = GatewaySubType(sub_type) if sub_type else None


@define(init=False, kw_only=True)
class HistoryExecutionCommand:
    """A command within a recorded historical execution, including its status and parameters."""

    device_url: str = field(repr=obfuscate_id)
    command: str
    rank: int
    dynamic: bool
    state: ExecutionState
    failure_type: str
    parameters: list[Any] | None = None

    def __init__(
        self,
        device_url: str,
        command: str,
        rank: int,
        dynamic: bool,
        state: ExecutionState,
        failure_type: str,
        parameters: list[Any] | None = None,
        **_: Any,
    ) -> None:
        """Initialize HistoryExecutionCommand from API fields."""
        self.device_url = device_url
        self.command = command
        self.parameters = parameters
        self.rank = rank
        self.dynamic = dynamic
        self.state = ExecutionState(state)
        self.failure_type = failure_type


@define(init=False, kw_only=True)
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
    commands: list[HistoryExecutionCommand]
    execution_type: ExecutionType
    execution_sub_type: ExecutionSubType

    def __init__(
        self,
        *,
        id: str,
        event_time: int,
        owner: str,
        source: str,
        end_time: int | None = None,
        effective_start_time: int | None = None,
        duration: int,
        label: str | None = None,
        type: str,
        state: ExecutionState,
        failure_type: str,
        commands: list[dict[str, Any]],
        execution_type: ExecutionType,
        execution_sub_type: ExecutionSubType,
        **_: Any,
    ) -> None:
        """Initialize HistoryExecution and convert nested command structures."""
        self.id = id
        self.event_time = event_time
        self.owner = owner
        self.source = source
        self.end_time = end_time
        self.effective_start_time = effective_start_time
        self.duration = duration
        self.label = label
        self.type = type
        self.state = ExecutionState(state)
        self.failure_type = failure_type
        self.commands = [HistoryExecutionCommand(**hec) for hec in commands]
        self.execution_type = ExecutionType(execution_type)
        self.execution_sub_type = ExecutionSubType(execution_sub_type)


@define(init=False, kw_only=True)
class Place:
    """Representation of a place (house/room) in a setup."""

    creation_time: int
    last_update_time: int | None = None
    label: str
    type: int
    id: str
    oid: str
    sub_places: list[Place]

    def __init__(
        self,
        *,
        creation_time: int,
        last_update_time: int | None = None,
        label: str,
        type: int,
        oid: str,
        sub_places: list[Any] | None,
        **_: Any,
    ) -> None:
        """Initialize Place from API data and convert nested sub-places."""
        self.id = oid
        self.creation_time = creation_time
        self.last_update_time = last_update_time
        self.label = label
        self.type = type
        self.oid = oid
        self.sub_places = [Place(**p) for p in sub_places] if sub_places else []


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


@define(init=False, kw_only=True)
class Zone:
    """A Zone groups related devices inside a place."""

    creation_time: str
    last_update_time: str
    label: str
    type: int
    items: list[ZoneItem] | None
    external_oid: str | None
    metadata: str | None
    oid: str

    def __init__(
        self,
        *,
        last_update_time: str,
        label: str,
        type: int,
        items: list[dict[str, Any]] | None,
        external_oid: str | None = None,
        metadata: str | None = None,
        oid: str,
        **_: Any,
    ) -> None:
        """Initialize Zone from API data and convert nested items."""
        self.last_update_time = last_update_time
        self.label = label
        self.type = type
        self.items = [ZoneItem(**z) for z in items] if items else []
        self.external_oid = external_oid
        self.metadata = metadata
        self.oid = oid


@define(kw_only=True)
class OverkizServer:
    """Class to describe an Overkiz server."""

    name: str
    endpoint: str
    manufacturer: str
    configuration_url: str | None


@define(kw_only=True)
class LocalToken:
    """Descriptor for a local gateway token."""

    label: str
    gateway_id: str = field(repr=obfuscate_id, default=None)
    gateway_creation_time: int
    uuid: str
    scope: str
    expiration_time: int | None


@define(kw_only=True)
class OptionParameter:
    """Key/value pair representing option parameter."""

    name: str
    value: str


@define(init=False, kw_only=True)
class Option:
    """A subscribed option for a setup including parameters."""

    creation_time: int
    last_update_time: int
    option_id: str
    start_date: int
    parameters: list[OptionParameter] | None

    def __init__(
        self,
        *,
        creation_time: int,
        last_update_time: int,
        option_id: str,
        start_date: int,
        parameters: list[dict[str, Any]] | None,
        **_: Any,
    ) -> None:
        """Initialize Option from API data and convert nested parameters."""
        self.creation_time = creation_time
        self.last_update_time = last_update_time
        self.option_id = option_id
        self.start_date = start_date
        self.parameters = (
            [OptionParameter(**p) for p in parameters] if parameters else []
        )
