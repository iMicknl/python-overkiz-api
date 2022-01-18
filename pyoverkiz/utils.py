"""Utils for Overkiz client"""
from __future__ import annotations

import re

from pyoverkiz.types import JSON


def obfuscate_id(id: str | None) -> str:
    """Mask id"""
    return re.sub(r"(SETUP)?\d+-", "****-", str(id))


def obfuscate_email(email: str | None) -> str:
    """Mask email"""
    return re.sub(r"(.).*@.*(.\..*)", r"\1****@****\2", str(email))


def mask(input: str) -> str:
    """Mask string"""
    return re.sub(r"[a-zA-Z0-9_.-]*", "*", str(input))


# pylint: disable=too-many-nested-blocks
def mask_json(data: dict) -> JSON:
    """Mask Overkiz JSON data"""
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
            data[key] = mask(value)

        if value in ["core:NameState", "homekit:SetupCode", "homekit:SetupPayload"]:
            mask_next_value = True

        if mask_next_value and key == "value":
            data[key] = mask(value)
            mask_next_value = False

        # Mask homekit:SetupCode and homekit:SetupPayload
        if isinstance(value, dict):
            mask_json(value)
        elif isinstance(value, list):
            for val in value:
                if isinstance(val, str):
                    pass
                elif isinstance(val, list):
                    pass
                else:
                    mask_json(val)

    return data
