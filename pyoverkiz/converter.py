"""Centralized cattrs converter for structuring Overkiz API responses."""

from __future__ import annotations

import types
from enum import Enum
from typing import Any, Union, get_args, get_origin

import attr
import cattrs

from pyoverkiz.models import (
    CommandDefinition,
    CommandDefinitions,
    State,
    States,
)


def _is_primitive_union(t: Any) -> bool:
    """True for union types containing only JSON-native types and enums (no attrs classes)."""
    origin = get_origin(t)
    if origin is not Union and not isinstance(t, types.UnionType):
        return False
    return all(
        arg is type(None) or not (isinstance(arg, type) and attr.has(arg))
        for arg in get_args(t)
    )


def _make_converter() -> cattrs.Converter:
    c = cattrs.Converter()

    # Primitive unions like StateType (str | int | float | … | None): pass through as-is
    c.register_structure_hook_func(_is_primitive_union, lambda v, _: v)

    # Enums: call the constructor so UnknownEnumMixin._missing_ can handle unknown values
    c.register_structure_hook_func(
        lambda t: isinstance(t, type) and issubclass(t, Enum),
        lambda v, t: v if isinstance(v, t) else t(v),
    )

    # Custom container types that take a list in __init__
    def _structure_states(val: Any, _: type) -> States:
        if val is None:
            return States()
        return States([c.structure(s, State) for s in val])

    def _structure_command_definitions(val: Any, _: type) -> CommandDefinitions:
        return CommandDefinitions([c.structure(cd, CommandDefinition) for cd in val])

    c.register_structure_hook(States, _structure_states)
    c.register_structure_hook(CommandDefinitions, _structure_command_definitions)

    return c


converter = _make_converter()
