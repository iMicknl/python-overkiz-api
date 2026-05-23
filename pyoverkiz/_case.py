"""Internal camelCase / snake_case conversion utilities."""

from __future__ import annotations

import functools
import re
from collections.abc import Callable
from typing import Any

_CAMEL_RE = re.compile(r"([A-Z]+)([A-Z][a-z])|([a-z\d])([A-Z])")


@functools.lru_cache(maxsize=1024)
def _decamelize_key(key: str) -> str:
    """Convert a single camelCase key to snake_case."""
    result = _CAMEL_RE.sub(r"\1\3_\2\4", key)
    return result.lower()


def recursive_key_map(data: Any, key_fn: Callable[[str], str]) -> Any:
    """Recursively apply *key_fn* to every dict key in *data*."""
    if isinstance(data, dict):
        return {key_fn(k): recursive_key_map(v, key_fn) for k, v in data.items()}
    if isinstance(data, list):
        return [recursive_key_map(item, key_fn) for item in data]
    return data


def decamelize(data: Any) -> Any:
    """Recursively convert dict keys from camelCase to snake_case."""
    return recursive_key_map(data, _decamelize_key)


@functools.lru_cache(maxsize=1024)
def camelize_key(key: str) -> str:
    """Convert a single snake_case key to camelCase."""
    parts = key.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


# Fields where the API uses non-standard casing that camelize_key cannot produce.
_API_KEY_OVERRIDES: dict[str, str] = {
    "device_url": "deviceURL",
    "place_oid": "placeOID",
    "setup_oid": "setupOID",
}


@functools.lru_cache(maxsize=1024)
def snake_to_api_key(snake: str) -> str:
    """Convert a snake_case field name to the camelCase key the API sends.

    Handles non-standard API casing (e.g. deviceURL, placeOID) that
    camelize_key cannot produce from standard snake_case conversion.
    """
    if snake in _API_KEY_OVERRIDES:
        return _API_KEY_OVERRIDES[snake]
    return camelize_key(snake)
