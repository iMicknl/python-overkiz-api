"""Internal camelCase / snake_case conversion utilities.

Replaces the external ``pyhumps`` dependency with a minimal implementation
covering only the patterns used by the Overkiz API.
"""

from __future__ import annotations

import re
from typing import Any

_CAMEL_RE = re.compile(r"([A-Z]+)([A-Z][a-z])|([a-z\d])([A-Z])")


def _decamelize_key(key: str) -> str:
    """Convert a single camelCase key to snake_case."""
    result = _CAMEL_RE.sub(r"\1\3_\2\4", key)
    return result.lower()


def decamelize(data: Any) -> Any:
    """Recursively convert dict keys from camelCase to snake_case."""
    if isinstance(data, dict):
        return {_decamelize_key(k): decamelize(v) for k, v in data.items()}
    if isinstance(data, list):
        return [decamelize(item) for item in data]
    return data


def camelize(key: str) -> str:
    """Convert a single snake_case key to camelCase."""
    parts = key.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])
