"""Centralized cattrs converter for structuring Overkiz API responses into models."""

from __future__ import annotations

import types
from enum import Enum
from typing import Any, Union, get_args, get_origin

import attr
import cattrs
from cattrs.dispatch import StructureHook

from pyoverkiz.models import (
    CommandDefinition,
    CommandDefinitions,
    State,
    States,
)


def _is_union(t: Any) -> bool:
    """Check if a type is a Union or PEP 604 union (X | Y)."""
    return get_origin(t) is Union or isinstance(t, types.UnionType)


def _is_primitive_union(t: Any) -> bool:
    """Check if a union type only contains primitive/JSON-native types and enums.

    Returns False if any union member is an attrs class (needs structuring).
    """
    if not _is_union(t):
        return False
    for arg in get_args(t):
        if arg is type(None):
            continue
        if isinstance(arg, type) and attr.has(arg):
            return False
    return True


def _make_converter() -> cattrs.Converter:
    c = cattrs.Converter(forbid_extra_keys=False)

    # ------------------------------------------------------------------
    # Primitive union types (str | Enum, StateType, etc.): passthrough
    # These only contain JSON-native types and enums, no attrs classes.
    # ------------------------------------------------------------------
    c.register_structure_hook_func(_is_primitive_union, lambda v, _: v)

    # ------------------------------------------------------------------
    # Optional[AttrsClass] unions: structure the non-None member
    # ------------------------------------------------------------------
    def _is_optional_attrs(t: Any) -> bool:
        if not _is_union(t):
            return False
        args = get_args(t)
        non_none = [a for a in args if a is not type(None)]
        return (
            len(non_none) == 1
            and isinstance(non_none[0], type)
            and attr.has(non_none[0])
        )

    def _structure_optional_attrs(v: Any, t: Any) -> Any:
        if v is None:
            return None
        args = get_args(t)
        cls = next(a for a in args if a is not type(None))
        return c.structure(v, cls)

    c.register_structure_hook_func(_is_optional_attrs, _structure_optional_attrs)

    # ------------------------------------------------------------------
    # Enums: use the enum constructor which handles UnknownEnumMixin
    # ------------------------------------------------------------------
    c.register_structure_hook_func(
        lambda t: isinstance(t, type) and issubclass(t, Enum),
        lambda v, t: v if isinstance(v, t) else t(v),
    )

    # ------------------------------------------------------------------
    # attrs classes: silently discard unknown keys from API responses
    # ------------------------------------------------------------------
    def _make_attrs_hook(cls: type) -> StructureHook:
        inner: StructureHook = cattrs.gen.make_dict_structure_fn(cls, c)

        def hook(val: Any, _: type) -> Any:
            if isinstance(val, dict):
                fields = {a.name for a in attr.fields(cls)}
                val = {k: v for k, v in val.items() if k in fields}
            return inner(val, cls)

        return hook

    c.register_structure_hook_factory(attr.has, _make_attrs_hook)

    # ------------------------------------------------------------------
    # Container types with custom __init__
    # ------------------------------------------------------------------
    def _structure_states(val: Any, _: type) -> States:
        if isinstance(val, States):
            return val
        if val is None:
            return States()
        return States([c.structure(s, State) for s in val])

    def _structure_command_definitions(val: Any, _: type) -> CommandDefinitions:
        if isinstance(val, CommandDefinitions):
            return val
        return CommandDefinitions([c.structure(cd, CommandDefinition) for cd in val])

    c.register_structure_hook(States, _structure_states)
    c.register_structure_hook(CommandDefinitions, _structure_command_definitions)

    return c


converter = _make_converter()
