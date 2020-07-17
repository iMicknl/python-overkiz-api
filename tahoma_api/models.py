from enum import Enum
from typing import Any, Dict, List, Optional

# pylint: disable=unused-argument, too-many-instance-attributes


class Device:
    __slots__ = (
        "id",
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
        available: bool,
        label: str,
        deviceurl: str,
        controllable_name: str,
        definition: Dict[str, Any],
        states: List[Dict[str, Any]],
        data_properties: Optional[List[Dict[str, Any]]] = None,
        widget: Optional[str] = None,
        ui_class: str,
        qualified_name: Optional[str] = None,
        type: str,
        **_: Any
    ) -> None:
        self.id = deviceurl
        self.available = available
        self.definition = definition
        self.deviceurl = deviceurl
        self.label = label
        self.controllable_name = controllable_name
        self.states = states
        # self.states = [State(**s) for s in states]
        self.data_properties = data_properties
        self.widget = widget
        self.ui_class = ui_class
        self.qualified_name = qualified_name
        self.type = type


# class Definition:
#     __slots__ = (
#         "commands",
#         "states",
#         "widget_name",
#         "ui_class",
#         "ui_classifiers" "type",
#     )

#     def __init__(self, command_name: str, nparams: int, **_: Any) -> None:
#         self.command_name = command_name
#         self.nparams = nparams


class StateDefinition:
    __slots__ = (
        "qualified_name",
        "type",
        "values",
    )

    def __init__(
        self, qualified_name: str, type: str, values: Optional[str], **_: Any
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


class Command:
    """Represents an TaHoma Command."""

    __slots__ = (
        "type",
        "name",
        "parameters",
        "sensitive_parameters_indexes",
        "authentication",
        "delay",
    )

    def __init__(self, name: str, parameters: str, **_: Any):
        self.name = name
        self.parameters = parameters


class ActionGroupResponse:
    def __init__(self, exec_id: str, **_: Any):
        self.exec_id = exec_id


class CommandMode(Enum):
    high_priority = ("highPriority",)
    geolocated = ("geolocated",)
    internal = "internal"
