from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Iterator, List, Optional

# pylint: disable=unused-argument, too-many-instance-attributes


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
    )

    def __init__(
        self,
        *,
        attributes: Optional[List[Dict[str, Any]]] = None,
        available: bool,
        enabled: bool,
        label: str,
        deviceurl: str,
        controllable_name: str,
        definition: Dict[str, Any],
        data_properties: Optional[List[Dict[str, Any]]] = None,
        widget: Optional[str] = None,
        ui_class: str,
        qualified_name: Optional[str] = None,
        states: Optional[List[Dict[str, Any]]] = None,
        type: int,
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


class Definition:
    __slots__ = ("commands", "states", "widget_name", "ui_class", "qualified_name")

    def __init__(
        self,
        *,
        commands: List[Dict[str, Any]],
        states: Optional[List[Dict[str, Any]]] = None,
        widget_name: str,
        ui_class: str,
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
        self,
        qualified_name: str,
        type: str,
        values: Optional[List[str]] = None,
        **_: Any
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
    def __init__(self, commands: List[Dict[str, Any]]):
        self._commands = [CommandDefinition(**command) for command in commands]

    def __iter__(self) -> Iterator[CommandDefinition]:
        return self._commands.__iter__()

    def __contains__(self, name: str) -> bool:
        return self.__getitem__(name) is not None

    def __getitem__(self, command: str) -> Optional[CommandDefinition]:
        return next((cd for cd in self._commands if cd.command_name == command), None)

    def __len__(self) -> int:
        return len(self._commands)

    get = __getitem__


class State:
    __slots__ = "name", "value", "type"

    def __init__(self, name: str, type: int, value: Optional[str] = None, **_: Any):
        self.name = name
        self.value = value
        self.type = DataType(type)


class States:
    def __init__(self, states: List[Dict[str, Any]]) -> None:
        self._states = [State(**state) for state in states]

    def __iter__(self) -> Iterator[State]:
        return self._states.__iter__()

    def __contains__(self, name: str) -> bool:
        return self.__getitem__(name) is not None

    def __getitem__(self, name: str) -> Optional[State]:
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

    def __init__(self, name: str, parameters: Optional[str] = None, **_: Any):
        self.name = name
        self.parameters = parameters
        dict.__init__(self, name=name, parameters=parameters)


class CommandMode(Enum):
    high_priority = ("highPriority",)
    geolocated = ("geolocated",)
    internal = "internal"


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
    )

    def __init__(
        self,
        timestamp: int,
        name: str,
        gateway_id: Optional[str] = None,
        exec_id: Optional[str] = None,
        deviceurl: Optional[str] = None,
        device_states: Optional[List[Dict[str, Any]]] = None,
        old_state: Optional[str] = None,
        new_state: Optional[str] = None,
        **_: Any
    ):
        self.timestamp = timestamp
        self.name = name
        self.gateway_id = gateway_id
        self.exec_id = exec_id
        self.deviceurl = deviceurl
        self.device_states = (
            [State(**s) for s in device_states] if device_states else None
        )
        self.old_state = old_state
        self.new_state = new_state


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
        action_group: List[Dict[str, Any]],
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


class ProductType(Enum):
    ACTUATOR = 1
    SENSOR = 2
    VIDEO = 3
    CONTROLLABLE = 4
    GATEWAY = 5
    INFRASTRUCTURE_COMPONENT = 6


class DataType(Enum):
    NONE = 0
    INTEGER = 1
    FLOAT = 2
    STRING = 3
    BLOB = 4
    DATE = 5
    BOOLEAN = 6
    JSON_ARRAY = 10
    JSON_OBJECT = 11
