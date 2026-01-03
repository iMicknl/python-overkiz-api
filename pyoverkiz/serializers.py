"""Helpers for preparing API payloads.

This module centralizes JSON key formatting and any small transport-specific
fixes (like mapping "deviceUrl" -> "deviceURL"). Models should produce
logical snake_case payloads and the client should call `prepare_payload`
before sending the payload to Overkiz.
"""

from __future__ import annotations

from typing import Any

import humps

# Small mapping for keys that need special casing beyond simple camelCase.
_ABBREV_MAP: dict[str, str] = {"deviceUrl": "deviceURL"}


def _fix_abbreviations(obj: Any) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            k = _ABBREV_MAP.get(k, k)
            out[k] = _fix_abbreviations(v)
        return out
    if isinstance(obj, list):
        return [_fix_abbreviations(i) for i in obj]
    return obj


def prepare_payload(payload: Any) -> Any:
    """Convert snake_case payload to API-ready camelCase and apply fixes.

    Example:
        payload = {"device_url": "x", "commands": [{"name": "close"}]}
        => {"deviceURL": "x", "commands": [{"name": "close"}]}
    """
    camel = humps.camelize(payload)
    return _fix_abbreviations(camel)
