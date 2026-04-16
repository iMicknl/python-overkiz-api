"""Helpers for preparing API payloads.

This module centralizes JSON key formatting and any small transport-specific
fixes (like mapping "deviceUrl" -> "deviceURL"). Models should produce
logical snake_case payloads and the client should call `prepare_payload`
before sending the payload to Overkiz.
"""

from __future__ import annotations

from typing import Any

from pyoverkiz._case import camelize

_ABBREV_MAP: dict[str, str] = {"deviceUrl": "deviceURL"}


def _camelize_key(key: str) -> str:
    """Camelize a single key and apply abbreviation fixes in one step."""
    camel = camelize(key)
    return _ABBREV_MAP.get(camel, camel)


def prepare_payload(payload: Any) -> Any:
    """Convert snake_case payload to API-ready camelCase and apply fixes.

    Performs camelization and abbreviation fixes in a single recursive pass
    to avoid walking the structure twice.

    Example:
        payload = {"device_url": "x", "commands": [{"name": "close"}]}
        => {"deviceURL": "x", "commands": [{"name": "close"}]}
    """
    if isinstance(payload, dict):
        return {_camelize_key(k): prepare_payload(v) for k, v in payload.items()}
    if isinstance(payload, list):
        return [prepare_payload(item) for item in payload]
    return payload
