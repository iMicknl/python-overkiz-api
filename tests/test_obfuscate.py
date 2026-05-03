"""Tests for the obfuscation utilities used in fixtures and logging."""

import pytest

from pyoverkiz.obfuscate import obfuscate_email, obfuscate_sensitive_data

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
