"""Tests for pyoverkiz._case conversion utilities."""

from __future__ import annotations

import pytest

from pyoverkiz._case import camelize, decamelize


class TestDecamelize:
    """Tests for camelCase to snake_case conversion."""

    def test_simple_camel_case(self) -> None:
        """Simple camelCase keys are converted correctly."""
        assert decamelize({"creationTime": 1}) == {"creation_time": 1}

    def test_abbreviation_url(self) -> None:
        """Consecutive uppercase (deviceURL) is split correctly."""
        assert decamelize({"deviceURL": "x"}) == {"device_url": "x"}

    def test_abbreviation_oid(self) -> None:
        """Consecutive uppercase (setupOID) is split correctly."""
        assert decamelize({"setupOID": "x"}) == {"setup_oid": "x"}

    def test_nested_dicts(self) -> None:
        """Nested dict keys are converted recursively."""
        data = {"outerKey": {"innerKey": "v"}}
        assert decamelize(data) == {"outer_key": {"inner_key": "v"}}

    def test_list_of_dicts(self) -> None:
        """Lists of dicts have their keys converted."""
        data = [{"testKey": 1}, {"anotherKey": 2}]
        assert decamelize(data) == [{"test_key": 1}, {"another_key": 2}]

    def test_nested_list_in_dict(self) -> None:
        """Dicts containing lists of dicts are converted recursively."""
        data = {"items": [{"subKey": "v"}]}
        assert decamelize(data) == {"items": [{"sub_key": "v"}]}

    def test_non_dict_passthrough(self) -> None:
        """Non-dict/list values pass through unchanged."""
        assert decamelize("hello") == "hello"
        assert decamelize(42) == 42
        assert decamelize(None) is None

    def test_lowercase_key_unchanged(self) -> None:
        """Already lowercase keys remain unchanged."""
        assert decamelize({"nparams": 0}) == {"nparams": 0}

    @pytest.mark.parametrize(
        "camel, expected",
        [
            ("deviceURL", "device_url"),
            ("placeOID", "place_oid"),
            ("uiClass", "ui_class"),
            ("execId", "exec_id"),
            ("gatewayId", "gateway_id"),
            ("subType", "sub_type"),
            ("failureTypeCode", "failure_type_code"),
        ],
    )
    def test_api_keys(self, camel: str, expected: str) -> None:
        """All API keys used by the Overkiz client convert correctly."""
        assert decamelize({camel: None}) == {expected: None}


class TestCamelize:
    """Tests for snake_case to camelCase conversion."""

    def test_simple_snake_case(self) -> None:
        """Simple snake_case keys are converted correctly."""
        assert camelize("creation_time") == "creationTime"

    def test_single_word(self) -> None:
        """Single word without underscores is unchanged."""
        assert camelize("name") == "name"

    def test_device_url(self) -> None:
        """device_url camelizes to deviceUrl (abbreviation fix is in serializers)."""
        assert camelize("device_url") == "deviceUrl"


class TestRoundTrip:
    """Test that decamelize/camelize produce consistent round-trips for API keys."""

    @pytest.mark.parametrize(
        "camel",
        [
            "creationTime",
            "lastUpdateTime",
            "commandName",
            "qualifiedName",
            "widgetName",
            "dataProperties",
            "gatewayId",
            "subType",
            "executionType",
        ],
    )
    def test_roundtrip(self, camel: str) -> None:
        """Decamelize then camelize returns the original key."""
        snake = next(iter(decamelize({camel: None}).keys()))
        assert camelize(snake) == camel
