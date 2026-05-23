"""Centralized cattrs converter for structuring Overkiz API responses."""

from __future__ import annotations

import types
import typing
from enum import Enum
from typing import Any, Union, get_args, get_origin

import attr
import cattrs
from cattrs.gen import make_dict_structure_fn, override

from pyoverkiz._case import snake_to_api_key
from pyoverkiz.models import (
    CommandDefinition,
    CommandDefinitions,
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
    # Exclude pure Optional[Enum] unions — those need the Enum structure hook.
    return not all(isinstance(arg, type) and issubclass(arg, Enum) for arg in non_none)


def _compute_rename_overrides(cls: type) -> dict[str, Any]:
    """Compute cattrs rename overrides for an attrs class."""
    fields = attr.fields(cls)
    overrides = {}
    for f in fields:
        if not f.init:
            continue
        snake = f.name
        if snake.startswith("_"):
            continue
        if f.alias is not None and f.alias != snake:
            continue
        api_key = snake_to_api_key(snake)
        if api_key != snake:
            overrides[snake] = override(rename=api_key)
    return overrides


def _collect_attrs_deps(cls: type, all_attrs: set[type]) -> set[type]:
    """Collect attrs classes referenced by fields of cls (resolving string annotations)."""
    deps: set[type] = set()
    try:
        hints = typing.get_type_hints(cls)
    except (TypeError, NameError, AttributeError):
        return deps

    for field_type in hints.values():
        _extract_attrs_types(field_type, all_attrs, deps)
    return deps


def _extract_attrs_types(tp: Any, all_attrs: set[type], result: set[type]) -> None:
    """Recursively extract attrs types from a type annotation."""
    if isinstance(tp, type) and tp in all_attrs:
        result.add(tp)
        return
    origin = get_origin(tp)
    if origin is not None or isinstance(tp, types.UnionType):
        for arg in get_args(tp):
            _extract_attrs_types(arg, all_attrs, result)


def _toposort(classes: list[type], all_attrs: set[type]) -> list[type]:
    """Topological sort: leaf classes (no deps) first, then classes that reference them."""
    order: list[type] = []
    visited: set[type] = set()
    visiting: set[type] = set()

    def visit(cls: type) -> None:
        if cls in visited:
            return
        if cls in visiting:
            # Cycle — just add it
            visited.add(cls)
            order.append(cls)
            return
        visiting.add(cls)
        for dep in _collect_attrs_deps(cls, all_attrs):
            if dep in all_attrs and dep != cls:
                visit(dep)
        visiting.discard(cls)
        visited.add(cls)
        order.append(cls)

    for cls in classes:
        visit(cls)

    return order


def _make_converter() -> cattrs.Converter:
    c = cattrs.Converter()

    # JSON-native unions like StateType (str | int | float | … | None) are already the
    # correct Python type after JSON parsing — tell cattrs to pass them through as-is.
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
        if val is None:
            return CommandDefinitions()
        return CommandDefinitions([c.structure(cd, CommandDefinition) for cd in val])

    def _structure_state_definitions(val: Any, _: type) -> StateDefinitions:
        if val is None:
            return StateDefinitions()
        return StateDefinitions([c.structure(sd, StateDefinition) for sd in val])

    c.register_structure_hook(States, _structure_states)
    c.register_structure_hook(CommandDefinitions, _structure_command_definitions)
    c.register_structure_hook(StateDefinitions, _structure_state_definitions)

    # Register camelCase->snake_case rename hooks for all attrs model classes.
    import pyoverkiz.models as models_mod

    skip = {States, CommandDefinitions, StateDefinitions}

    attrs_classes: list[type] = [
        getattr(models_mod, name)
        for name in dir(models_mod)
        if isinstance(getattr(models_mod, name, None), type)
        and attr.has(getattr(models_mod, name))
        and getattr(models_mod, name) not in skip
    ]

    all_attrs = set(attrs_classes)

    # Register in dependency order (leaf classes first) so that make_dict_structure_fn
    # captures the correct rename-aware hooks for nested types.
    for cls in _toposort(attrs_classes, all_attrs):
        overrides = _compute_rename_overrides(cls)
        if overrides:
            c.register_structure_hook(cls, make_dict_structure_fn(cls, c, **overrides))

    return c


converter = _make_converter()


def structure_response[T](data: Any, cls: type[T]) -> T:
    """Structure an API response (with camelCase keys) into the target type."""
    return converter.structure(data, cls)
