from __future__ import annotations
from dataclasses import dataclass
from typing import NamedTuple

import json
from typing import Any, Callable, Dict, List, Union

from pyoverkiz.enums import DataType

StateType = Union[str, int, float, bool, Dict[Any, Any], List[Any], None]


DATA_TYPE_TO_PYTHON: dict[DataType, Callable[[Any], StateType]] = {
    DataType.INTEGER: int,
    DataType.DATE: int,
    DataType.FLOAT: float,
    DataType.BOOLEAN: bool,
    DataType.JSON_ARRAY: json.loads,
    DataType.JSON_OBJECT: json.loads,
}


@dataclass
class OverkizAuth():
    """Overkiz auth data object."""

@dataclass
class CloudAuth(OverkizAuth):
    """Overkiz cloud auth data object."""
    username: str
    password: str

@dataclass
class LocalAuth(OverkizAuth):
    """Overkiz local auth data object."""
    host: str
    api_token: str
