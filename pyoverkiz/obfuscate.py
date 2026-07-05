"""Utils for Overkiz client."""

from __future__ import annotations

import re
from typing import Any, cast

# Keys whose value is an identifier (gateway id, device url, ...).
_ID_KEYS = frozenset({"gatewayId", "id", "deviceURL"})

# Keys whose value is free text / location data to fully mask.
_STRING_KEYS = frozenset(
    {
        "label",
        "city",
        "country",
        "postalCode",
        "addressLine1",
        "addressLine2",
        "longitude",
        "latitude",
    }
)

# Overkiz attributes/states are {"name": ..., "value": ...} dicts. When "name"
# is one of these, the sibling "value" holds PII and must be masked.
_SENSITIVE_STATE_NAMES = frozenset(
    {
        "core:NameState",
        "homekit:SetupCode",
        "homekit:SetupPayload",
        "core:SSIDState",
        "core:NetworkMacState",
        "internal:CurrentInfraConfigState",
        "core:LocalIPv4AddressState",
        "core:IPAddress",
        "core:MacAddress",
        "core:SerialNumber",
        "core:DeviceSerialNumberState",
        "core:IPAddressState",
        "core:LabelState",
        "core:LocationLatitudeState",
        "core:LocationLongitudeState",
    }
)


def obfuscate_id(value: str | None) -> str:
    """Mask id."""
    return re.sub(r"(SETUP)?\d+-", "****-", str(value))


def obfuscate_email(email: str | None) -> str:
    """Mask email."""
    email = str(email).replace("_-_", "@")  # Replace @ for _-_ (Nexity)
    return re.sub(r"(.).*@.*(.\..*)", r"\1****@****\2", email)


def obfuscate_string(value: str) -> str:
    """Mask string."""
    return re.sub(r"[\w.-]+", "*", str(value), flags=re.UNICODE)


def obfuscate_sensitive_data(
    data: dict[str, Any] | list[dict[str, Any]],
) -> dict[str, Any] | list[dict[str, Any]]:
    """Return a copy of Overkiz JSON data with sensitive values masked."""
    if isinstance(data, list):
        return cast(
            list[dict[str, Any]], [obfuscate_sensitive_data(item) for item in data]
        )

    # Decide up front whether this dict's "value" is sensitive, so masking does
    # not depend on "name" appearing before "value" in the key iteration order.
    mask_value = data.get("name") in _SENSITIVE_STATE_NAMES

    result: dict[str, Any] = {}
    for key, value in data.items():
        if key in _ID_KEYS:
            result[key] = obfuscate_id(value)
        elif key in _STRING_KEYS or (key == "value" and mask_value):
            result[key] = obfuscate_string(value)
        elif isinstance(value, dict):
            result[key] = obfuscate_sensitive_data(value)
        elif isinstance(value, list):
            result[key] = [
                obfuscate_sensitive_data(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value

    return result
