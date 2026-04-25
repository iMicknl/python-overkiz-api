"""Type helpers used across the package (state types and JSON helpers)."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from pyoverkiz.enums import DataType

StateType = str | int | float | bool | dict[str, Any] | list[Any] | None


def _parse_bool(value: str) -> bool:
    """Parse a string value into a boolean.

    bool() won't work since bool("false") is True.
    """
    return value.lower() in ("true", "1")


DATA_TYPE_TO_PYTHON: dict[DataType, Callable[[str], StateType]] = {
    DataType.INTEGER: int,
    DataType.DATE: int,
    DataType.FLOAT: float,
    DataType.BOOLEAN: _parse_bool,
    DataType.JSON_ARRAY: json.loads,
    DataType.JSON_OBJECT: json.loads,
}

JSON = dict[str, Any] | list[dict[str, Any]]  # pylint: disable=invalid-name
