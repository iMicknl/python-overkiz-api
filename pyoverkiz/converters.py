"""Converters for structuring API data into model instances using cattrs."""

from __future__ import annotations

from enum import Enum, IntEnum
from typing import TypeVar

import cattrs

from pyoverkiz.enums import StrEnum

E = TypeVar("E", bound=Enum)

# Global converter instance configured to ignore extra keys from API responses
converter = cattrs.Converter(forbid_extra_keys=False)


def _structure_enum(val: int | str | None, enum_cls: type[E]) -> E | None:
    """Structure an enum value, returning None if the input is None."""
    if val is None:
        return None
    return enum_cls(val)


def configure_converter() -> None:
    """Register structure hooks for all pyoverkiz enums.

    This must be called after importing the enums module to ensure all enum
    classes are available for registration.
    """
    from pyoverkiz import enums

    # Exclude base enum classes that are re-exported from the enums module
    base_classes = (Enum, IntEnum, StrEnum)

    for name in dir(enums):
        obj = getattr(enums, name)
        if isinstance(obj, type) and issubclass(obj, Enum) and obj not in base_classes:
            converter.register_structure_hook(obj, _structure_enum)


# Configure the converter when this module is imported
configure_converter()
