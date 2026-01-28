"""Shared enum helpers for consistent parsing and logging."""

from __future__ import annotations

import logging
from typing import Self, cast


class UnknownEnumMixin:
    """Mixin for enums that need an `UNKNOWN` fallback.

    Define `UNKNOWN` on the enum and optionally override
    `__missing_message__` to customize the log message.
    """

    __missing_message__ = "Unsupported value %s has been returned for %s"

    @classmethod
    def _missing_(cls, value: object) -> Self:  # type: ignore[override]
        """Return `UNKNOWN` and log unrecognized values.

        Intentionally overrides `StrEnum._missing_` to provide UNKNOWN fallback.
        """
        message = cls.__missing_message__
        logging.getLogger(cls.__module__).warning(message, value, cls)
        # Type checker cannot infer UNKNOWN exists on Self, but all subclasses define it
        return cast(Self, cls.UNKNOWN)  # type: ignore[attr-defined]
