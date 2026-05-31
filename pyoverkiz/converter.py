"""Centralized cattrs converter for structuring Overkiz API responses."""

from __future__ import annotations

import types
from enum import Enum
from typing import Any, Union, get_args, get_origin

import attr
import cattrs
from cattrs.gen import make_dict_structure_fn, override

from pyoverkiz._case import camelize_key
from pyoverkiz.models import (
    CommandDefinition,
    CommandDefinitions,
    EventState,
    State,
    StateDefinition,
    StateDefinitions,
    States,
)


def _is_primitive_union(t: Any) -> bool:
    """True for unions of JSON-native types (e.g. StateType).

    Excludes unions containing attrs classes (e.g. Definition | None) since those
    need actual structuring by cattrs.
    """
    origin = get_origin(t)
    if origin is not Union and not isinstance(t, types.UnionType):
        return False
    non_none = [arg for arg in get_args(t) if arg is not type(None)]
    if any(isinstance(arg, type) and attr.has(arg) for arg in non_none):
        return False
    return not all(isinstance(arg, type) and issubclass(arg, Enum) for arg in non_none)


def _rename_hook_factory(cls: type, converter: cattrs.Converter) -> Any:
    """Generate a structuring hook that maps camelCase API keys to snake_case fields."""
    overrides = {}
    for f in attr.fields(cls):
        if not f.init or f.name.startswith("_"):
            continue
        if f.alias and f.alias != f.name:
            continue
        api_key = camelize_key(f.name)
        if api_key != f.name:
            overrides[f.name] = override(rename=api_key)
    return make_dict_structure_fn(cls, converter, **overrides)  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type]


def _make_converter() -> cattrs.Converter:
    # Converter (not GenConverter) so unknown API keys are silently dropped for forward-compat.
    c = cattrs.Converter()

    # JSON-native unions like StateType (str | int | float | … | None) are already the
    # correct Python type after JSON parsing — tell cattrs to pass them through as-is.
    c.register_structure_hook_func(_is_primitive_union, lambda v, _: v)

    # Enums: call the constructor so UnknownEnumMixin._missing_ can handle unknown values
    c.register_structure_hook_func(
        lambda t: isinstance(t, type) and issubclass(t, Enum),
        lambda v, t: v if isinstance(v, t) else t(v),
    )

    # Custom container types that wrap a list in __init__
    def _structure_states(val: Any, _: type) -> States:
        if val is None:
            return States()
        return States([c.structure(s, State) for s in val])

    def _structure_command_definitions(val: Any, _: type) -> CommandDefinitions:
        if val is None:
            return CommandDefinitions()
        return CommandDefinitions([c.structure(cd, CommandDefinition) for cd in val])

    def _structure_state_definitions(val: Any, _: type) -> StateDefinitions:
        if val is None:
            return StateDefinitions()
        return StateDefinitions([c.structure(sd, StateDefinition) for sd in val])

    # Event.device_states is a plain list[EventState], but the API may send an
    # explicit `deviceStates: null`. cattrs' generic list hook iterates the value
    # directly, so it raises on None; tolerate it the way 1.x did (None -> []).
    def _structure_event_states(val: Any, _: type) -> list[EventState]:
        if val is None:
            return []
        return [c.structure(s, EventState) for s in val]

    c.register_structure_hook(States, _structure_states)
    c.register_structure_hook(CommandDefinitions, _structure_command_definitions)
    c.register_structure_hook(StateDefinitions, _structure_state_definitions)
    c.register_structure_hook_func(
        lambda t: t == list[EventState], _structure_event_states
    )

    # For all other attrs classes: lazily generate a hook that renames camelCase
    # API keys to snake_case on first use. This avoids manual dependency ordering.
    skip = {States, CommandDefinitions, StateDefinitions}
    c.register_structure_hook_factory(
        lambda t: isinstance(t, type) and attr.has(t) and t not in skip,
        _rename_hook_factory,
    )

    return c


converter = _make_converter()
