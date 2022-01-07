from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Union

from pyoverkiz.enums import DataType

StateType = Union[str, int, float, bool, Dict[Any, Any], List[Any], None]


def none(value: str | None = None) -> None | str:
    return value


DATA_TYPE_TO_PYTHON: dict[DataType, Callable[[Any], StateType]] = {
    DataType.NONE: none,
    DataType.INTEGER: int,
    DataType.DATE: int,
    DataType.STRING: str,
    DataType.FLOAT: float,
    DataType.BOOLEAN: bool,
    DataType.JSON_ARRAY: json.loads,
    DataType.JSON_OBJECT: json.loads,
}
