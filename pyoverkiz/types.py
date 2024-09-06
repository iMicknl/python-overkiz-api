from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, Union

from pyoverkiz.enums import DataType

StateType = Union[str, int, float, bool, dict[str, Any], list[Any], None]


DATA_TYPE_TO_PYTHON: dict[DataType, Callable[[Any], StateType]] = {
    DataType.INTEGER: int,
    DataType.DATE: int,
    DataType.FLOAT: float,
    DataType.BOOLEAN: bool,
    DataType.JSON_ARRAY: json.loads,
    DataType.JSON_OBJECT: json.loads,
}

JSON = Union[dict[str, Any], list[dict[str, Any]]]  # pylint: disable=invalid-name
