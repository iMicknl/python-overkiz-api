"""Tests for the obfuscation utilities used in fixtures and logging."""

import pytest

from pyoverkiz.obfuscate import (
    obfuscate_email,
    obfuscate_sensitive_data,
    obfuscate_string,
)

LOCAL_HOST = "gateway-1234-5678-1243.local:8443"
LOCAL_HOST_BY_IP = "192.168.1.105:8443"


class TestObfucscate:
    """Tests for obfuscation utilities (emails and sensitive data)."""

    @pytest.mark.parametrize(
        ("email", "obfuscated"),
        [
            ("contact@somfy.com", "c****@****y.com"),
            ("contact_-_nexity.com", "c****@****y.com"),
        ],
    )
    def test_email_obfuscate(self, email: str, obfuscated: str):
        """Verify email obfuscation produces the expected masked result."""
        assert obfuscate_email(email) == obfuscated


class TestObfuscateString:
    """Tests for obfuscate_string with various character sets."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("My Room", "* *"),
            ("Séjour", "*"),
            ("Étage", "*"),
            ("Entrée", "*"),
            ("Volet Fenêtre", "* *"),
            ("Ré-de-chaussée", "*"),
            ("Büro", "*"),
            ("abc123", "*"),
            ("", ""),
        ],
    )
    def test_obfuscate_string(self, value: str, expected: str):
        """Verify string obfuscation handles Unicode characters."""
        assert obfuscate_string(value) == expected


class TestObfucscateSensitive:
    """Tests around obfuscating sensitive structures while preserving non-sensitive content."""

    def test_obfuscate_list_with_none(self):
        """Ensure lists containing None values are handled without modification."""
        data = {
            "d": [
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            ]
        }
        assert obfuscate_sensitive_data(data) == data

    def test_obfuscate_list_of_dicts(self):
        """Ensure obfuscate_sensitive_data handles a list of dicts."""
        data = [
            {"label": "My Scene", "oid": "abc-123"},
            {"label": "Night Mode", "deviceURL": "io://1234-5678-1234/12345678"},
        ]
        result = obfuscate_sensitive_data(data)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["label"] != "My Scene"
        assert result[0]["oid"] == "abc-123"  # oid is not a sensitive key
        assert result[1]["label"] != "Night Mode"
        assert result[1]["deviceURL"] != "io://1234-5678-1234/12345678"

    def test_obfuscate_infra_config_state(self):
        """Ensure internal:CurrentInfraConfigState value is redacted."""
        data = {
            "name": "internal:CurrentInfraConfigState",
            "type": 3,
            "value": "wifi_ssid:MyNetwork;password:secret123",
        }
        result = obfuscate_sensitive_data(data)
        assert result["name"] == "internal:CurrentInfraConfigState"
        assert result["value"] != "wifi_ssid:MyNetwork;password:secret123"

    @pytest.mark.parametrize(
        "state_name",
        [
            "core:NameState",
            "homekit:SetupCode",
            "homekit:SetupPayload",
            "core:SSIDState",
            "core:NetworkMacState",
            "internal:CurrentInfraConfigState",
            "core:LocalIPv4AddressState",
            "core:IPAddress",
            "core:MacAddress",
            "core:SerialNumber",
            "core:DeviceSerialNumberState",
            "core:IPAddressState",
            "core:LabelState",
            "core:LocationLatitudeState",
            "core:LocationLongitudeState",
        ],
    )
    def test_obfuscate_sensitive_states(self, state_name: str):
        """Ensure all sensitive state names trigger value redaction."""
        data = {"name": state_name, "type": 3, "value": "sensitive_data"}
        result = obfuscate_sensitive_data(data)
        assert result["name"] == state_name
        assert result["value"] != "sensitive_data"

    def test_obfuscate_unicode_label(self):
        """Ensure labels with Unicode characters are fully redacted."""
        data = {"label": "Volet Séjour"}
        result = obfuscate_sensitive_data(data)
        assert "Séjour" not in result["label"]
        assert "é" not in result["label"]

    @pytest.mark.parametrize(
        "state_name",
        ["core:SerialNumber", "core:NameState"],
    )
    def test_obfuscate_sensitive_value_before_name(self, state_name: str):
        """Value is redacted even when it precedes name in key order.

        Some hubs return attributes/states as {"value", "type", "name"}, so
        redaction must not depend on "name" being seen before "value".
        """
        data = {"value": "34-7E-5C-FA-A2-86:9", "type": 3, "name": state_name}
        result = obfuscate_sensitive_data(data)
        assert result["name"] == state_name
        assert result["value"] != "34-7E-5C-FA-A2-86:9"
