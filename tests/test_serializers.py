"""Tests for pyoverkiz.serializers."""

from __future__ import annotations

from pyoverkiz.serializers import prepare_payload


def test_prepare_payload_camelizes_and_fixes_device_url():
    """Test that prepare_payload converts snake_case to camelCase and fixes abbreviations."""
    payload = {
        "label": "test",
        "actions": [{"device_url": "rts://1/2", "commands": [{"name": "close"}]}],
    }

    final = prepare_payload(payload)

    assert final["label"] == "test"
    assert "deviceURL" in final["actions"][0]
    assert final["actions"][0]["deviceURL"] == "rts://1/2"


def test_prepare_payload_nested_lists_and_dicts():
    """Test that prepare_payload handles nested lists and dicts correctly."""
    payload = {
        "actions": [
            {
                "device_url": "rts://1/2",
                "commands": [{"name": "setLevel", "parameters": [10, "A"]}],
            }
        ]
    }

    final = prepare_payload(payload)

    cmd = final["actions"][0]["commands"][0]
    assert cmd["name"] == "setLevel"
    assert cmd["parameters"] == [10, "A"]
