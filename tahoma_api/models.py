from enum import Enum
from typing import Any, Dict, List, Optional

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
        type: str,
        **_: Any
    ) -> None:
        self.id = deviceurl
        self.attributes = [State(**a) for a in attributes] if attributes else None
        self.available = available
        self.definition = Definition(**definition)
        self.deviceurl = deviceurl
        self.enabled = enabled
        self.label = label
        self.controllable_name = controllable_name
        self.states = [State(**s) for s in states] if states else None
        self.data_properties = data_properties
        self.widget = widget
        self.ui_class = ui_class
        self.qualified_name = qualified_name
        self.type = type


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
        self.commands = [CommandDefinition(**cd) for cd in commands]
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


class State:
    __slots__ = "name", "value", "type"

    def __init__(self, name: str, value: str, type: str, **_: Any):
        self.name = name
        self.value = value
        self.type = type


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
