"""Utils for Overkiz client"""

from __future__ import annotations

import re
from typing import Any

from pyoverkiz.types import JSON


def obfuscate_id(id: str | None) -> str:
    """Mask id"""
    return re.sub(r"(SETUP)?\d+-", "****-", str(id))


def obfuscate_email(email: str | None) -> str:
    """Mask email"""
    email = str(email).replace("_-_", "@")  # Replace @ for _-_ (Nexity)
    return re.sub(r"(.).*@.*(.\..*)", r"\1****@****\2", email)


def obfuscate_string(input: str) -> str:
    """Mask string"""
    return re.sub(r"[a-zA-Z0-9_.-]*", "*", str(input))


# pylint: disable=too-many-branches
def obfuscate_sensitive_data(data: dict[str, Any]) -> JSON:
    """Mask Overkiz JSON data to remove sensitive data"""
    mask_next_value = False

    for key, value in data.items():
        if key in ["gatewayId", "id", "deviceURL"]:
            data[key] = obfuscate_id(value)

        if key in [
            "label",
            "city",
            "country",
            "postalCode",
            "addressLine1",
            "addressLine2",
            "longitude",
            "latitude",
        ]:
            data[key] = obfuscate_string(value)

        if value in [
            "core:NameState",
            "homekit:SetupCode",
            "homekit:SetupPayload",
            "core:SSIDState",
        ]:
            mask_next_value = True

        if mask_next_value and key == "value":
            data[key] = obfuscate_string(value)
            mask_next_value = False

        # Mask homekit:SetupCode and homekit:SetupPayload
        if isinstance(value, dict):
            obfuscate_sensitive_data(value)
        elif isinstance(value, list):
            for val in value:
                if isinstance(val, str):
                    continue
                if isinstance(val, int):
                    continue
                if isinstance(val, float):
                    continue
                if isinstance(val, list):
                    continue
                if val is None:
                    continue

                obfuscate_sensitive_data(val)

    return data
