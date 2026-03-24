"""Cattrs converter for structuring API responses into typed models."""

from __future__ import annotations

import types
from enum import Enum, IntEnum
from typing import Any

import attrs
import cattrs

from pyoverkiz.enums.base import UnknownEnumMixin

converter = cattrs.Converter(forbid_extra_keys=False)


def _structure_enum(val: int | str | None, enum_cls: type[Enum]) -> Enum | None:
    """Structure an enum value, returning None for None input."""
    if val is None:
        return None
    return enum_cls(val)


def _structure_union(val: Any, union_type: types.UnionType) -> Any:
    """Structure a union type (``X | Y``).

    If one of the union members is an attrs class and the value is a dict,
    structure it into that class. Otherwise pass the value through unchanged.
    """
    if val is None:
        return None
    for arg in union_type.__args__:
        if arg is type(None):
            continue
        if attrs.has(arg) and isinstance(val, dict):
            return converter.structure(val, arg)
    return val


def _register_hooks() -> None:
    """Register structure hooks for enums and union types."""
    from pyoverkiz import enums as _enums_mod

    skip = (Enum, IntEnum, UnknownEnumMixin)
    for name in dir(_enums_mod):
        obj = getattr(_enums_mod, name)
        if isinstance(obj, type) and issubclass(obj, Enum) and obj not in skip:
            converter.register_structure_hook(obj, _structure_enum)

    converter.register_structure_hook_func(
        lambda t: isinstance(t, types.UnionType),
        _structure_union,
    )


_register_hooks()


def structure(data: Any, cls: type) -> Any:
    """Structure *data* into *cls* using the pre-configured converter."""
    return converter.structure(data, cls)
