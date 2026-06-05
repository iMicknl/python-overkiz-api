"""Centralized cattrs converter for structuring Overkiz API responses."""

from __future__ import annotations

import logging
import types
from enum import Enum
from typing import Any, Union, get_args, get_origin

import attr
import cattrs
from cattrs.errors import ClassValidationError
from cattrs.gen import make_dict_structure_fn, override

from pyoverkiz._case import camelize_key
from pyoverkiz.enums import EventName, GatewaySubType
from pyoverkiz.models import (
    EVENT_TYPE_BY_NAME,
    CommandDefinition,
    CommandDefinitions,
    Event,
    EventState,
    State,
    StateDefinition,
    StateDefinitions,
    States,
)

_LOGGER = logging.getLogger(__name__)


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

    # Gateways report subType 0 to mean "no specific sub-type" — surface that as None
    # rather than GatewaySubType.UNKNOWN, which stays reserved for genuinely unrecognised
    # values. Scoped to the Optional field (GatewaySubType | None) so bare GatewaySubType
    # structuring keeps the generic enum behaviour; exact-type hook (direct dispatch) so it
    # overrides the primitive-union and generic enum hooks.
    c.register_structure_hook(
        GatewaySubType | None,
        lambda v, _: None if v in (0, None) else c.structure(v, GatewaySubType),
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

    c.register_structure_hook(States, _structure_states)
    c.register_structure_hook(CommandDefinitions, _structure_command_definitions)
    c.register_structure_hook(StateDefinitions, _structure_state_definitions)

    # DeviceStateChangedEvent.device_states: the API may send "deviceStates": null
    # instead of omitting the key. cattrs' default list hook would choke on None,
    # so tolerate it as an empty list.
    def _structure_event_states(val: Any, _: type) -> list[EventState]:
        if not val:
            return []
        return [c.structure(s, EventState) for s in val]

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

    # Event is a discriminated union keyed on the "name" field. Resolve the
    # concrete subtype, then delegate to that class's generated (rename-aware)
    # hook. Unknown / unmodeled names fall back to the base Event.
    #
    # We pre-build each class's hook and call it directly. Routing through
    # c.structure(val, subtype) would re-enter this hook (cattrs dispatches a
    # subclass to its base class's registered hook), causing infinite recursion.
    event_types: set[type[Event]] = {Event, *EVENT_TYPE_BY_NAME.values()}
    event_hooks: dict[type[Event], Any] = {
        cls: _rename_hook_factory(cls, c) for cls in event_types
    }

    def _structure_event(val: Any, _: type) -> Event:
        name = val.get("name") if isinstance(val, dict) else None
        target: type[Event] = Event
        if name is not None:
            target = EVENT_TYPE_BY_NAME.get(EventName(name), Event)
        try:
            return event_hooks[target](val, target)  # type: ignore[no-any-return]
        except ClassValidationError as err:
            # Subtypes declare the fields the API is documented to send as
            # required. If a payload omits one (undocumented quirk, partial
            # data), degrade that single event to the base Event rather than
            # failing the whole batch. The warning flags a field worth
            # loosening — strictness stays the default, resilience the
            # fallback.
            if target is Event:
                raise
            _LOGGER.warning(
                "Could not structure %s as %s (%s); falling back to base Event",
                name,
                target.__name__,
                err,
            )
            return event_hooks[Event](val, Event)  # type: ignore[no-any-return]

    c.register_structure_hook(Event, _structure_event)

    return c


converter = _make_converter()
