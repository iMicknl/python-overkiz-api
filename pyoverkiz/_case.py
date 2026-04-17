"""Internal camelCase / snake_case conversion utilities.

Replaces the external ``pyhumps`` dependency with a minimal implementation
covering only the patterns used by the Overkiz API.
"""

from __future__ import annotations

import functools
import re
from typing import Any

_CAMEL_RE = re.compile(r"([A-Z]+)([A-Z][a-z])|([a-z\d])([A-Z])")


@functools.lru_cache(maxsize=256)
def _decamelize_key(key: str) -> str:
    """Convert a single camelCase key to snake_case."""
    result = _CAMEL_RE.sub(r"\1\3_\2\4", key)
    return result.lower()


def _recursive_key_map(data: Any, key_fn: Any) -> Any:
    """Recursively apply *key_fn* to every dict key in *data*."""
    if isinstance(data, dict):
        return {key_fn(k): _recursive_key_map(v, key_fn) for k, v in data.items()}
    if isinstance(data, list):
        return [_recursive_key_map(item, key_fn) for item in data]
    return data


def decamelize(data: Any) -> Any:
    """Recursively convert dict keys from camelCase to snake_case."""
    return _recursive_key_map(data, _decamelize_key)


def camelize(key: str) -> str:
    """Convert a single snake_case key to camelCase."""
    parts = key.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])
