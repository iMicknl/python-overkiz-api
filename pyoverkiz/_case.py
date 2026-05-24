"""Internal camelCase / snake_case conversion utilities."""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any


def recursive_key_map(data: Any, key_fn: Callable[[str], str]) -> Any:
    """Recursively apply *key_fn* to every dict key in *data*."""
    if isinstance(data, dict):
        return {key_fn(k): recursive_key_map(v, key_fn) for k, v in data.items()}
    if isinstance(data, list):
        return [recursive_key_map(item, key_fn) for item in data]
    return data


_CAMELIZE_OVERRIDES: dict[str, str] = {
    "device_url": "deviceURL",
    "place_oid": "placeOID",
    "setup_oid": "setupOID",
}


@functools.lru_cache(maxsize=1024)
def camelize_key(key: str) -> str:
    """Convert a single snake_case key to camelCase.

    Handles non-standard API casing (e.g. deviceURL, placeOID) via overrides.
    """
    if key in _CAMELIZE_OVERRIDES:
        return _CAMELIZE_OVERRIDES[key]
    parts = key.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])
