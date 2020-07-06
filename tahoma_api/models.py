from typing import Any, Dict, List, Optional, Union

# TODO Rewrite camelCase to snake_case
class Device:
    __slots__ = (
        "id",
        "creationTime",
        "lastUpdateTime",
        "label",
        "deviceURL",
        "shortcut",
        "controllableName",
        "definition",
        "states",
        "dataProperties",
        "available",
        "enabled",
        "widgetName",
        "widget",
        "uiClass",
        "qualifiedName",
        "type",
    )

    def __init__(
        self,
        *,
        label: str,
        deviceURL: str,
        controllableName: str,
        # definition: Dict[List[Any]],
        states: List[Dict[str, Any]],
        dataProperties: Optional[List[Dict[str, Any]]] = None,
        widgetName: Optional[str] = None,
        uiClass: str,
        qualifiedName: Optional[str] = None,
        type: str,
        **kwargs: Any
    ):
        self.id = deviceURL
        self.deviceURL = deviceURL
        self.label = label
        self.controllableName = controllableName
        self.states = [State(**s) for s in states]


class StateDefinition:
    __slots__ = (
        "qualifiedName",
        "type",
        "values",
    )

    def __init__(
        self, qualifiedName: str, type: str, values: Optional[str], **kwargs: Any
    ):
        self.qualifiedName = qualifiedName
        self.type = type
        self.values = values


class CommandDefinition:
    __slots__ = (
        "commandName",
        "nparams",
    )

    def __init__(self, commandName: str, nparams: int, **kwargs: Any):
        self.commandName = commandName
        self.nparams = nparams


class State:
    __slots__ = "name", "value", "type"

    def __init__(self, name: str, value: str, type: str, **kwargs: Any):
        self.name = name
        self.value = value
        self.type = type


class Command:
    """Represents an TaHoma Command."""

    __slots__ = (
        "type",
        "name",
        "parameters",
        "sensitiveParametersIndexes",
        "authentication",
        "delay",
    )

    def __init__(self, name: str, parameters: str, **kwargs: Any):
        self.name = name
        self.parameters = parameters
