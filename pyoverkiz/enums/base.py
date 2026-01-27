"""Shared enum helpers for consistent parsing and logging."""

from __future__ import annotations

import logging
from enum import Enum
from typing import TypeVar, cast

_EnumT = TypeVar("_EnumT", bound=Enum)


class UnknownEnumMixin:
    """Mixin for enums that need an `UNKNOWN` fallback.

    Define `UNKNOWN` on the enum and optionally override
    `__missing_message__` to customize the log message.
    """

    __missing_message__ = "Unsupported value %s has been returned for %s"

    @classmethod
    def _missing_(cls, value):  # type: ignore[override]
        """Return `UNKNOWN` and log unrecognized values."""
        message = getattr(cls, "__missing_message__", cls.__missing_message__)
        logging.getLogger(cls.__module__).warning(message, value, cls)
        return cls.UNKNOWN

    @classmethod
    def from_value(cls: type[_EnumT], value: object) -> _EnumT:
        """Return enum for `value`, falling back to `UNKNOWN`."""
        return cast(_EnumT, cls(value))
