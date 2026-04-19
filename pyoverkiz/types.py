"""Type helpers used across the package (state types and JSON helpers)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from pyoverkiz.enums import DataType

if TYPE_CHECKING:
    from collections.abc import Callable

StateType = str | int | float | bool | dict[str, Any] | list[Any] | None


DATA_TYPE_TO_PYTHON: dict[DataType, Callable[[Any], StateType]] = {
    DataType.INTEGER: int,
    DataType.DATE: int,
    DataType.FLOAT: float,
    DataType.BOOLEAN: bool,
    DataType.JSON_ARRAY: json.loads,
    DataType.JSON_OBJECT: json.loads,
}

JSON = dict[str, Any] | list[dict[str, Any]]  # pylint: disable=invalid-name
