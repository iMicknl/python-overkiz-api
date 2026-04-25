"""Behavioral configuration for OverkizClient."""

from __future__ import annotations

from dataclasses import dataclass

from pyoverkiz.action_queue import ActionQueueSettings


@dataclass(frozen=True, slots=True)
class OverkizClientSettings:
    """Behavioral configuration for OverkizClient.

    All fields are optional and default to passive behavior.
    """

    action_queue: ActionQueueSettings | None = None
    rts_command_duration: int | None = None
