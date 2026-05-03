"""Shared enum helpers for consistent parsing and logging."""

from __future__ import annotations

import logging
from typing import Self


class UnknownEnumMixin:
    """Mixin for enums that need an `UNKNOWN` fallback.

    Define `UNKNOWN` on the enum and optionally override
    `__missing_message__` to customize the log message.
    """

    __missing_message__ = "Unsupported value %s has been returned for %s"

    def __init_subclass__(cls, **kwargs: object) -> None:
        """Validate that concrete enum subclasses define an `UNKNOWN` member."""
        super().__init_subclass__(**kwargs)

        # _member_map_ is only present on concrete Enum subclasses.
        member_map: dict[str, object] | None = getattr(cls, "_member_map_", None)
        if member_map is not None and "UNKNOWN" not in member_map:
            raise TypeError(
                f"{cls.__name__} uses UnknownEnumMixin but does not define "
                f"an UNKNOWN member"
            )

    @classmethod
    def _missing_(cls, value: object) -> Self:  # type: ignore[override]
        """Return `UNKNOWN` and log unrecognized values.

        Intentionally overrides the Enum base `_missing_` to provide an UNKNOWN fallback.
        """
        message = cls.__missing_message__
        logging.getLogger(cls.__module__).warning(message, value, cls)
        return cls.UNKNOWN  # type: ignore[attr-defined]  # ty: ignore[unresolved-attribute]
