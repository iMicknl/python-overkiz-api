"""Utils for Overkiz client."""

from __future__ import annotations

import re
from typing import Any, cast


def obfuscate_id(value: str | None) -> str:
    """Mask id."""
    return re.sub(r"(SETUP)?\d+-", "****-", str(value))


def obfuscate_email(email: str | None) -> str:
    """Mask email."""
    email = str(email).replace("_-_", "@")  # Replace @ for _-_ (Nexity)
    return re.sub(r"(.).*@.*(.\..*)", r"\1****@****\2", email)


def obfuscate_string(value: str) -> str:
    """Mask string."""
    return re.sub(r"[a-zA-Z0-9_.-]*", "*", str(value))


def _obfuscate_value(key: str, value: Any, mask_next_value: bool) -> tuple[Any, bool]:
    """Return (obfuscated_value, mask_next_value) for a single key/value pair."""
    result = value

    if key in {"gatewayId", "id", "deviceURL"}:
        result = obfuscate_id(value)
    elif key in {
        "label",
        "city",
        "country",
        "postalCode",
        "addressLine1",
        "addressLine2",
        "longitude",
        "latitude",
    }:
        result = obfuscate_string(value)
    elif mask_next_value and key == "value":
        result = obfuscate_string(value)
        return result, False

    if result in (
        "core:NameState",
        "homekit:SetupCode",
        "homekit:SetupPayload",
        "core:SSIDState",
        "core:NetworkMacState",
    ):
        mask_next_value = True

    if isinstance(result, dict):
        result = obfuscate_sensitive_data(result)
    elif isinstance(result, list):
        result = [
            obfuscate_sensitive_data(item) if isinstance(item, dict) else item
            for item in result
        ]

    return result, mask_next_value


def obfuscate_sensitive_data(
    data: dict[str, Any] | list[dict[str, Any]],
) -> dict[str, Any] | list[dict[str, Any]]:
    """Return a copy of Overkiz JSON data with sensitive values masked."""
    if isinstance(data, list):
        return cast(
            list[dict[str, Any]], [obfuscate_sensitive_data(item) for item in data]
        )

    result: dict[str, Any] = {}
    mask_next_value = False

    for key, value in data.items():
        obfuscated, mask_next_value = _obfuscate_value(key, value, mask_next_value)
        result[key] = obfuscated

    return result
