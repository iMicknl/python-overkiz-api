from __future__ import annotations

import re
from typing import Any, Iterator

import attr

from pyhoma.enums import (
    DataType,
    EventName,
    ExecutionState,
    ExecutionSubType,
    ExecutionType,
    FailureType,
    GatewaySubType,
    GatewayType,
    ProductType,
    UpdateBoxStatus,
)

# pylint: disable=unused-argument, too-many-instance-attributes, too-many-locals


def obfuscate_id(id: str | None) -> str:
    return re.sub(r"(SETUP)?\d+-", "****-", str(id))


def obfuscate_email(email: str | None) -> str:
    return re.sub(r"(.).*@.*(.\..*)", r"\1****@****\2", str(email))


def mask(input: str) -> str:
    return re.sub(r"[a-zA-Z0-9_.-]*", "*", str(input))


@attr.s(auto_attribs=True, init=False, slots=True, kw_only=True)
class Setup:
    creation_time: str
    last_update_time: str
    id: str = attr.ib(repr=obfuscate_id, default=None)
    location: Location
    gateways: list[Gateway]
    devices: list[Device]
    zones: list[Zone]
    reseller_delegation_type: str
    oid: str
    root_place: Place
    features: list[Feature] | None = None

    def __init__(
        self,
        *,
        creation_time: str,
        last_update_time: str,
        id: str = attr.ib(repr=obfuscate_id, default=None),
        location: dict[str, Any],
        gateways: list[dict[str, Any]],
        devices: list[dict[str, Any]],
        zones: list[dict[str, Any]],
        reseller_delegation_type: str,
        oid: str,
        root_place: dict[str, Any],
        features: list[dict[str, Any]] | None = None,
        **_: Any,
    ) -> None:
        self.id = id
        self.creation_time = creation_time
        self.last_update_time = last_update_time
        self.location = Location(**location)
        self.gateways = [Gateway(**g) for g in gateways]
        self.devices = [Device(**d) for d in devices]
        self.zones = [Zone(**z) for z in zones]
        self.reseller_delegation_type = reseller_delegation_type
        self.oid = oid
        self.root_place = Place(**root_place)
        self.features = [Feature(**f) for f in features] if features else None


@attr.s(auto_attribs=True, init=False, slots=True, kw_only=True)
class Location:
    creation_time: str
    last_update_time: str
    city: str = attr.ib(repr=mask, default=None)
    country: str = attr.ib(repr=mask, default=None)
    postal_code: str = attr.ib(repr=mask, default=None)
    address_line1: str = attr.ib(repr=mask, default=None)
    address_line2: str = attr.ib(repr=mask, default=None)
    timezone: str
    longitude: str = attr.ib(repr=mask, default=None)
    latitude: str = attr.ib(repr=mask, default=None)
    twilight_mode: int
    twilight_angle: str
    twilight_city: str
    summer_solstice_dusk_minutes: str
    winter_solstice_dusk_minutes: str
    twilight_offset_enabled: bool
    dawn_offset: int
    dusk_offset: int

    def __init__(
        self,
        *,
        creation_time: str,
        last_update_time: str,
        city: str = attr.ib(repr=mask, default=None),
        country: str = attr.ib(repr=mask, default=None),
        postal_code: str = attr.ib(repr=mask, default=None),
        address_line1: str = attr.ib(repr=mask, default=None),
        address_line2: str = attr.ib(repr=mask, default=None),
        timezone: str,
        longitude: str = attr.ib(repr=mask, default=None),
        latitude: str = attr.ib(repr=mask, default=None),
        twilight_mode: int,
        twilight_angle: str,
        twilight_city: str,
        summer_solstice_dusk_minutes: str,
        winter_solstice_dusk_minutes: str,
        twilight_offset_enabled: bool,
        dawn_offset: int,
        dusk_offset: int,
        **_: Any,
    ) -> None:
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


@attr.s(auto_attribs=True, init=False, slots=True, kw_only=True)
class Device:
    id: str = attr.ib(repr=False)
    attributes: States
    available: bool
    enabled: bool
    label: str
    device_url: str = attr.ib(repr=obfuscate_id)
    controllable_name: str
    definition: Definition
    data_properties: list[dict[str, Any]] | None = None
    widget: str | None = None
    ui_class: str | None = None
    states: States
    type: ProductType
    place_oid: str

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
        ui_class: str | None = None,
        states: list[dict[str, Any]] | None = None,
        type: int,
        place_oid: str,
        **_: Any,
    ) -> None:
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
        self.widget = widget
        self.ui_class = ui_class
        self.type = ProductType(type)
        self.place_oid = place_oid


@attr.s(auto_attribs=True, init=False, slots=True, kw_only=True)
class StateDefinition:

    qualified_name: str
    type: str
    values: list[str] | None = None

    def __init__(
        self, qualified_name: str, type: str, values: list[str] | None = None, **_: Any
    ) -> None:
        self.qualified_name = qualified_name
        self.type = type
        self.values = values


@attr.s(auto_attribs=True, init=False, slots=True, kw_only=True)
class Definition:
    commands: CommandDefinitions
    states: list[StateDefinition]
    widget_name: str | None = None
    ui_class: str | None = None
    qualified_name: str

    def __init__(
        self,
        *,
        commands: list[dict[str, Any]],
        states: list[dict[str, Any]] | None = None,
        widget_name: str | None = None,
        ui_class: str | None = None,
        qualified_name: str,
        **_: Any,
    ) -> None:
        self.commands = CommandDefinitions(commands)
        self.states = [StateDefinition(**sd) for sd in states] if states else []
        self.widget_name = widget_name
        self.ui_class = ui_class
        self.qualified_name = qualified_name


@attr.s(auto_attribs=True, init=False, slots=True, kw_only=True)
class CommandDefinition:
    command_name: str
    nparams: int

    def __init__(self, command_name: str, nparams: int, **_: Any) -> None:
        self.command_name = command_name
        self.nparams = nparams


@attr.s(auto_attribs=True, init=False, slots=True)
class CommandDefinitions:
    _commands: list[CommandDefinition]

    def __init__(self, commands: list[dict[str, Any]]):
        self._commands = [CommandDefinition(**command) for command in commands]

    def __iter__(self) -> Iterator[CommandDefinition]:
        return self._commands.__iter__()

    def __contains__(self, name: str) -> bool:
        return self.__getitem__(name) is not None

    def __getitem__(self, command: str) -> CommandDefinition | None:
        return next((cd for cd in self._commands if cd.command_name == command), None)

    def __len__(self) -> int:
        return len(self._commands)

    get = __getitem__


@attr.s(auto_attribs=True, init=False, slots=True, kw_only=True)
class State:
    name: str
    type: DataType
    value: str | None = None

    def __init__(self, name: str, type: int, value: str | None = None, **_: Any):
        self.name = name
        self.value = value
        self.type = DataType(type)


@attr.s(auto_attribs=True, init=False, slots=True)
class States:
    _states: list[State]

    def __init__(self, states: list[dict[str, Any]] | None = None) -> None:
        if states:
            self._states = [State(**state) for state in states]
        else:
            self._states = []

    def __iter__(self) -> Iterator[State]:
        return self._states.__iter__()

    def __contains__(self, name: str) -> bool:
        return self.__getitem__(name) is not None

    def __getitem__(self, name: str) -> State | None:
        return next((state for state in self._states if state.name == name), None)

    def __setitem__(self, name: str, state: State) -> None:
        found = self.__getitem__(name)
        if found is None:
            self._states.append(state)
        else:
            self._states[self._states.index(found)] = state

    def __len__(self) -> int:
        return len(self._states)

    get = __getitem__


class Command(dict):  # type: ignore
    """Represents an TaHoma Command."""

    def __init__(self, name: str, parameters: list[str] | None = None, **_: Any):
        self.name = name
        self.parameters = parameters
        dict.__init__(self, name=name, parameters=parameters)


@attr.s(auto_attribs=True, init=False, slots=True, kw_only=True)
class Event:
    timestamp: int
    name: EventName
    setupoid: str | None = attr.ib(repr=obfuscate_id, default=None)
    owner_key: str | None = attr.ib(repr=obfuscate_id, default=None)
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
    gateway_id: str | None = attr.ib(repr=obfuscate_id, default=None)
    exec_id: str | None = None
    device_url: str | None = attr.ib(repr=obfuscate_id, default=None)
    device_states: list[State]
    old_state: ExecutionState | None = None
    new_state: ExecutionState | None = None

    def __init__(
        self,
        timestamp: int,
        name: EventName,
        setupoid: str | None = attr.ib(repr=obfuscate_id, default=None),
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
        self.timestamp = timestamp
        self.gateway_id = gateway_id
        self.exec_id = exec_id
        self.device_url = device_url
        self.device_states = (
            [State(**s) for s in device_states] if device_states else []
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


@attr.s(auto_attribs=True, init=False, slots=True, kw_only=True)
class Execution:
    id: str
    description: str
    owner: str = attr.ib(repr=obfuscate_email)
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
        self.id = id
        self.description = description
        self.owner = owner
        self.state = state
        self.action_group = action_group


@attr.s(auto_attribs=True, init=False, slots=True, kw_only=True)
class Scenario:
    label: str
    oid: str = attr.ib(repr=obfuscate_id)

    def __init__(self, label: str, oid: str, **_: Any):
        self.label = label
        self.oid = oid


@attr.s(auto_attribs=True, init=False, slots=True, kw_only=True)
class Partner:
    activated: bool
    name: str
    id: str = attr.ib(repr=obfuscate_id)
    status: str

    def __init__(self, activated: bool, name: str, id: str, status: str, **_: Any):
        self.activated = activated
        self.name = name
        self.id = id
        self.status = status


@attr.s(auto_attribs=True, init=False, slots=True, kw_only=True)
class Connectivity:
    status: str
    protocol_version: str

    def __init__(self, status: str, protocol_version: str, **_: Any):
        self.status = status
        self.protocol_version = protocol_version


@attr.s(auto_attribs=True, init=False, slots=True, kw_only=True)
class Gateway:
    partners: list[Partner]
    functions: str | None = None
    sub_type: GatewaySubType | None = None
    id: str = attr.ib(repr=obfuscate_id)
    gateway_id: str
    alive: bool | None = None
    mode: str
    place_oid: str | None = None
    time_reliable: bool
    connectivity: Connectivity
    up_to_date: bool | None = None
    update_status: UpdateBoxStatus
    sync_in_progress: bool
    type: GatewayType

    def __init__(
        self,
        *,
        partners: list[dict[str, Any]] | None = None,
        functions: str | None = None,
        sub_type: GatewaySubType | None = None,
        gateway_id: str,
        alive: bool | None = None,
        mode: str,
        place_oid: str | None = None,
        time_reliable: bool,
        connectivity: dict[str, Any],
        up_to_date: bool | None = None,
        update_status: UpdateBoxStatus,
        sync_in_progress: bool,
        type: GatewayType,
        **_: Any,
    ) -> None:
        self.id = gateway_id
        self.functions = functions
        self.alive = alive
        self.mode = mode
        self.place_oid = place_oid
        self.time_reliable = time_reliable
        self.connectivity = Connectivity(**connectivity)
        self.up_to_date = up_to_date
        self.update_status = UpdateBoxStatus(update_status)
        self.sync_in_progress = sync_in_progress
        self.partners = [Partner(**p) for p in partners] if partners else []
        self.type = GatewayType(type)
        self.sub_type = GatewaySubType(sub_type) if sub_type else None


@attr.s(auto_attribs=True, init=False, slots=True, kw_only=True)
class HistoryExecutionCommand:
    device_url: str = attr.ib(repr=obfuscate_id)
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
        self.device_url = device_url
        self.command = command
        self.parameters = parameters
        self.rank = rank
        self.dynamic = dynamic
        self.state = ExecutionState(state)
        self.failure_type = failure_type


@attr.s(auto_attribs=True, init=False, slots=True, kw_only=True)
class HistoryExecution:
    id: str
    event_time: int
    owner: str = attr.ib(repr=obfuscate_email)
    source: str
    end_time: int
    effective_start_time: int
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
        end_time: int,
        effective_start_time: int,
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


@attr.s(auto_attribs=True, init=False, slots=True, kw_only=True)
class Place:
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
        self.id = oid
        self.creation_time = creation_time
        self.last_update_time = last_update_time
        self.label = label
        self.type = type
        self.oid = oid
        self.sub_places = [Place(**p) for p in sub_places] if sub_places else []


@attr.s(auto_attribs=True, slots=True, kw_only=True)
class Feature:
    name: str
    source: str


@attr.s(auto_attribs=True, slots=True, kw_only=True)
class ZoneItem:
    item_type: str
    device_oid: str
    device_url: str


@attr.s(auto_attribs=True, init=False, slots=True, kw_only=True)
class Zone:
    creation_time: str
    last_update_time: str
    label: str
    type: int
    items: list[ZoneItem] | None
    external_oid: str
    metadata: str
    oid: str

    def __init__(
        self,
        *,
        last_update_time: str,
        label: str,
        type: int,
        items: list[dict[str, Any]] | None,
        external_oid: str,
        metadata: str,
        oid: str,
        **_: Any,
    ) -> None:
        self.last_update_time = last_update_time
        self.label = label
        self.type = type
        self.items = [ZoneItem(**z) for z in items] if items else []
        self.external_oid = external_oid
        self.metadata = metadata
        self.oid = oid


@attr.s(auto_attribs=True, slots=True, kw_only=True)
class OverkizServer:
    """Class to describe an Overkiz server."""

    name: str
    endpoint: str
    manufacturer: str
    configuration_url: str | None
