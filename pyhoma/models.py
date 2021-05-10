from __future__ import annotations

from typing import Any, Iterator

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


class Device:
    __slots__ = (
        "id",
        "attributes",
        "controllable_name",
        "creation_time",
        "last_update_time",
        "label",
        "deviceurl",
        "shortcut",
        "controllable_name",
        "definition",
        "states",
        "data_properties",
        "available",
        "enabled",
        "widget",
        "ui_class",
        "qualified_name",
        "type",
        "placeoid",
    )

    def __init__(
        self,
        *,
        attributes: list[dict[str, Any]] | None = None,
        available: bool,
        enabled: bool,
        label: str,
        deviceurl: str,
        controllable_name: str,
        definition: dict[str, Any],
        data_properties: list[dict[str, Any]] | None = None,
        widget: str | None = None,
        ui_class: str | None = None,
        qualified_name: str | None = None,
        states: list[dict[str, Any]] | None = None,
        type: int,
        placeoid: str,
        **_: Any
    ) -> None:
        self.id = deviceurl
        self.attributes = States(attributes) if attributes else None
        self.available = available
        self.definition = Definition(**definition)
        self.deviceurl = deviceurl
        self.enabled = enabled
        self.label = label
        self.controllable_name = controllable_name
        self.states = States(states) if states else None
        self.data_properties = data_properties
        self.widget = widget
        self.ui_class = ui_class
        self.qualified_name = qualified_name
        self.type = ProductType(type)
        self.placeoid = placeoid


class Definition:
    __slots__ = ("commands", "states", "widget_name", "ui_class", "qualified_name")

    def __init__(
        self,
        *,
        commands: list[dict[str, Any]],
        states: list[dict[str, Any]] | None = None,
        widget_name: str | None = None,
        ui_class: str | None = None,
        qualified_name: str,
        **_: Any
    ) -> None:
        self.commands = CommandDefinitions(commands)
        self.states = [StateDefinition(**sd) for sd in states] if states else None
        self.widget_name = widget_name
        self.ui_class = ui_class
        self.qualified_name = qualified_name


class StateDefinition:
    __slots__ = (
        "qualified_name",
        "type",
        "values",
    )

    def __init__(
        self, qualified_name: str, type: str, values: list[str] | None = None, **_: Any
    ) -> None:
        self.qualified_name = qualified_name
        self.type = type
        self.values = values


class CommandDefinition:
    __slots__ = (
        "command_name",
        "nparams",
    )

    def __init__(self, command_name: str, nparams: int, **_: Any) -> None:
        self.command_name = command_name
        self.nparams = nparams


class CommandDefinitions:
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


class State:
    __slots__ = "name", "value", "type"

    def __init__(self, name: str, type: int, value: str | None = None, **_: Any):
        self.name = name
        self.value = value
        self.type = DataType(type)


class States:
    def __init__(self, states: list[dict[str, Any]]) -> None:
        self._states = [State(**state) for state in states]

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

    __slots__ = (
        "name",
        "parameters",
    )

    def __init__(self, name: str, parameters: str | None = None, **_: Any):
        self.name = name
        self.parameters = parameters
        dict.__init__(self, name=name, parameters=parameters)


# pylint: disable-msg=too-many-locals
class Event:
    __slots__ = (
        "timestamp",
        "name",
        "gateway_id",
        "exec_id",
        "deviceurl",
        "device_states",
        "old_state",
        "new_state",
        "owner_key",
        "setupoid",
        "owner_key",
        "type",
        "sub_type",
        "time_to_next_state",
        "failed_commands",
        "failure_type_code",
        "failure_type",
        "condition_groupoid",
        "placeoid",
        "label",
        "metadata",
        "camera_id",
        "deleted_raw_devices_count",
        "protocol_type",
    )

    def __init__(
        self,
        timestamp: int,
        name: EventName,
        setupoid: str | None = None,
        owner_key: str | None = None,
        type: int | None = None,
        sub_type: int | None = None,
        time_to_next_state: int | None = None,
        failed_commands: list[dict[str, Any]] | None = None,
        failure_type_code: FailureType | None = None,
        failure_type: str | None = None,
        condition_groupoid: str | None = None,
        placeoid: str | None = None,
        label: str | None = None,
        metadata: Any | None = None,
        camera_id: str | None = None,
        deleted_raw_devices_count: Any | None = None,
        protocol_type: Any | None = None,
        gateway_id: str | None = None,
        exec_id: str | None = None,
        deviceurl: str | None = None,
        device_states: list[dict[str, Any]] | None = None,
        old_state: ExecutionState | None = None,
        new_state: ExecutionState | None = None,
        **_: Any
    ):
        self.timestamp = timestamp
        self.gateway_id = gateway_id
        self.exec_id = exec_id
        self.deviceurl = deviceurl
        self.device_states = (
            [State(**s) for s in device_states] if device_states else None
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
        self.placeoid = placeoid
        self.label = label
        self.metadata = metadata
        self.camera_id = camera_id
        self.deleted_raw_devices_count = deleted_raw_devices_count
        self.protocol_type = protocol_type

        try:
            self.name = EventName(name)
        except ValueError:
            self.name = name

        try:
            self.failure_type_code = (
                FailureType(failure_type_code) if failure_type_code else None
            )
        except ValueError:
            self.failure_type_code = failure_type_code


class Execution:

    __slots__ = (
        "id",
        "description",
        "owner",
        "state",
        "action_group",
    )

    def __init__(
        self,
        id: str,
        description: str,
        owner: str,
        state: str,
        action_group: list[dict[str, Any]],
        **_: Any
    ):
        self.id = id
        self.description = description
        self.owner = owner
        self.state = state
        self.action_group = action_group


class Scenario:
    __slots__ = ("label", "oid")

    def __init__(self, label: str, oid: str, **_: Any):
        self.label = label
        self.oid = oid


class Partner:
    __slots__ = ("activated", "name", "id", "status")

    def __init__(self, activated: bool, name: str, id: str, status: str, **_: Any):
        self.activated = activated
        self.name = name
        self.id = id
        self.status = status


class Connectivity:
    __slots__ = ("status", "protocol_version")

    def __init__(self, status: str, protocol_version: str, **_: Any):
        self.status = status
        self.protocol_version = protocol_version


class Gateway:
    __slots__ = (
        "id",
        "partners",
        "functions",
        "sub_type",
        "gateway_id",
        "alive",
        "mode",
        "placeoid",
        "time_reliable",
        "connectivity",
        "up_to_date",
        "update_status",
        "sync_in_progress",
        "type",
    )

    def __init__(
        self,
        *,
        partners: list[dict[str, Any]] | None = None,
        functions: str | None = None,
        sub_type: GatewaySubType,
        gateway_id: str,
        alive: bool | None = None,
        mode: str,
        placeoid: str | None = None,
        time_reliable: bool,
        connectivity: dict[str, Any],
        up_to_date: bool | None = None,
        update_status: UpdateBoxStatus,
        sync_in_progress: bool,
        type: GatewayType,
        **_: Any
    ) -> None:
        self.id = gateway_id
        self.functions = functions
        self.alive = alive
        self.mode = mode
        self.placeoid = placeoid
        self.time_reliable = time_reliable
        self.connectivity = Connectivity(**connectivity)
        self.up_to_date = up_to_date
        self.update_status = UpdateBoxStatus(update_status)
        self.sync_in_progress = sync_in_progress
        self.partners = [Partner(**p) for p in partners] if partners else None

        try:
            self.type = GatewayType(type)
        except ValueError:
            self.type = type

        try:
            self.sub_type = GatewaySubType(sub_type)
        except ValueError:
            self.sub_type = sub_type


class HistoryExecutionCommand:
    __slots__ = (
        "deviceurl",
        "command",
        "parameters",
        "rank",
        "dynamic",
        "state",
        "failure_type",
    )

    def __init__(
        self,
        deviceurl: str,
        command: str,
        rank: int,
        dynamic: bool,
        state: ExecutionState,
        failure_type: str,
        parameters: list[Any] | None = None,
        **_: Any
    ) -> None:
        self.deviceurl = deviceurl
        self.command = command
        self.parameters = parameters
        self.rank = rank
        self.dynamic = dynamic
        self.state = ExecutionState(state)
        self.failure_type = failure_type


class HistoryExecution:
    __slots__ = (
        "id",
        "event_time",
        "owner",
        "source",
        "end_time",
        "effective_start_time",
        "duration",
        "label",
        "type",
        "state",
        "failure_type",
        "commands",
        "execution_type",
        "execution_sub_type",
    )

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
        label: str,
        type: str,
        state: ExecutionState,
        failure_type: str,
        commands: list[dict[str, Any]],
        execution_type: ExecutionType,
        execution_sub_type: ExecutionSubType,
        **_: Any
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


class Place:
    __slots__ = (
        "id",
        "creation_time",
        "last_update_time",
        "label",
        "type",
        "oid",
        "sub_places",
    )

    def __init__(
        self,
        *,
        creation_time: int,
        last_update_time: int | None = None,
        label: str,
        type: int,
        oid: str,
        sub_places: list[Any] | None,
        **_: Any
    ) -> None:
        self.id = oid
        self.creation_time = creation_time
        self.last_update_time = last_update_time
        self.label = label
        self.type = type
        self.oid = oid
        self.sub_places = [Place(**p) for p in sub_places] if sub_places else None
