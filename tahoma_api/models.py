from typing import Any, Dict, List, Optional


# TODO Rewrite camelCase to snake_case
class Device:
    __slots__ = (
        "id",
        "creation_time",
        "last_update_time",
        "label",
        "device_url",
        "shortcut",
        "controllable_name",
        "definition",
        "states",
        "data_properties",
        "available",
        "enabled",
        "widget_name",
        "widget",
        "ui_class",
        "qualified_name",
        "type",
    )

    def __init__(
        self,
        *,
        label: str,
        device_url: str,
        controllable_name: str,
        # definition: Dict[List[Any]],
        states: List[Dict[str, Any]],
        data_properties: Optional[List[Dict[str, Any]]] = None,
        widget_name: Optional[str] = None,
        ui_class: str,
        qualified_name: Optional[str] = None,
        type: str,
        **_: Any
    ) -> None:
        self.id = device_url
        self.device_url = device_url
        self.label = label
        self.controllable_name = controllable_name
        self.states = [State(**s) for s in states]
        self.data_properties = data_properties
        self.widget_name = widget_name
        self.ui_class = ui_class
        self.qualified_name = qualified_name
        self.type = type


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
