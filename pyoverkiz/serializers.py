"""Helpers for preparing API payloads.

This module centralizes JSON key formatting for outgoing requests.
Models produce logical snake_case payloads and the client calls
`prepare_payload` before sending to Overkiz.
"""

from __future__ import annotations

from typing import Any

from pyoverkiz._case import camelize_key, recursive_key_map


def prepare_payload(payload: Any) -> Any:
    """Convert snake_case payload to API-ready camelCase.

    Example:
        payload = {"device_url": "x", "commands": [{"name": "close"}]}
        => {"deviceURL": "x", "commands": [{"name": "close"}]}
    """
    return recursive_key_map(payload, camelize_key)
