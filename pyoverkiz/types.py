from __future__ import annotations

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

JSON = Union[Dict[str, Any], List[Dict[str, Any]]]
