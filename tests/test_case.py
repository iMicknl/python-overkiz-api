"""Tests for pyoverkiz._case conversion utilities."""

from __future__ import annotations

from pyoverkiz._case import camelize_key


class TestCamelize:
    """Tests for snake_case to camelCase conversion."""

    def test_simple_snake_case(self):
        """Simple snake_case keys are converted correctly."""
        assert camelize_key("creation_time") == "creationTime"

    def test_single_word(self):
        """Single word without underscores is unchanged."""
        assert camelize_key("name") == "name"

    def test_device_url(self):
        """device_url camelizes to deviceURL (non-standard API casing)."""
        assert camelize_key("device_url") == "deviceURL"

    def test_acronym_overrides(self):
        """Keys ending in OID/URL(s) use the API's uppercase acronym casing."""
        assert camelize_key("setup_oid") == "setupOID"
        assert camelize_key("place_oid") == "placeOID"
        assert camelize_key("zone_oid") == "zoneOID"
        assert camelize_key("device_urls") == "deviceURLs"
        assert camelize_key("place_oids") == "placeOIDs"
