"""Tests for OverkizClientSettings."""

from pyoverkiz.action_queue import ActionQueueSettings
from pyoverkiz.client_settings import OverkizClientSettings


def test_defaults():
    """Default settings have no queue and no RTS duration."""
    settings = OverkizClientSettings()
    assert settings.action_queue is None
    assert settings.rts_command_duration is None


def test_with_rts_duration():
    """RTS command duration can be set."""
    settings = OverkizClientSettings(rts_command_duration=0)
    assert settings.rts_command_duration == 0


def test_with_action_queue_settings():
    """Passing ActionQueueSettings stores it directly."""
    qs = ActionQueueSettings(delay=1.0, max_actions=10)
    settings = OverkizClientSettings(action_queue=qs)
    assert settings.action_queue is qs
