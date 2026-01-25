"""Tests for enum helper behaviour and expected values."""

# ruff: noqa: S101
# Tests use assert statements

from pyoverkiz.enums import (
    EventName,
    ExecutionSubType,
    ExecutionType,
    FailureType,
    GatewaySubType,
    GatewayType,
    OverkizCommandParam,
)


class TestGatewayType:
    """Tests for GatewayType enum behaviour (missing / beautify name)."""

    def test_missing(self):
        """Unsupported numeric values map to UNKNOWN."""
        assert GatewayType(102) == GatewayType.UNKNOWN

    def test_beautify_name(self):
        """Check the human friendly name conversion for various gateway types."""
        assert GatewayType.TAHOMA_V2.beautify_name == "TaHoma V2"
        assert (
            GatewayType.CONNEXOON_RTS_AUSTRALIA.beautify_name
            == "Connexoon RTS Australia"
        )
        assert GatewayType.COZYTOUCH_V2.beautify_name == "Cozytouch V2"


class TestGatewaySubType:
    """Tests for GatewaySubType enum behaviour (missing / beautify name)."""

    def test_missing(self):
        """Unknown numeric values map to UNKNOWN."""
        assert GatewaySubType(99) == GatewaySubType.UNKNOWN

    def test_beautify_name(self):
        """Check the human friendly name conversion for gateway sub types."""
        assert GatewaySubType.TAHOMA_SECURITY_PRO.beautify_name == "TaHoma Security Pro"


class TestEventName:
    """Tests for EventName enum handling of unknown values."""

    def test_missing(self):
        """Unknown event codes map to UNKNOWN."""
        assert EventName(99) == EventName.UNKNOWN


class TestFailureType:
    """Tests for FailureType enum handling of unknown values."""

    def test_missing(self):
        """Unknown failure codes map to UNKNOWN."""
        assert FailureType(99) == FailureType.UNKNOWN


class TestExecutionType:
    """Tests for ExecutionType enum fallback behaviour."""

    def test_missing(self):
        """String values not recognized map to UNKNOWN."""
        assert ExecutionType("test") == ExecutionType.UNKNOWN


class TestExecutionSubType:
    """Tests for ExecutionSubType enum fallback behaviour."""

    def test_missing(self):
        """String values not recognized map to UNKNOWN."""
        assert ExecutionSubType("test") == ExecutionSubType.UNKNOWN


class TestStrEnumBackport:
    """Tests for the backported StrEnum behaviour used in command params."""

    def test_string_concat(self):
        """Check that StrEnum members stringify and join as expected."""
        assert (
            f"{OverkizCommandParam.A},{OverkizCommandParam.B},{OverkizCommandParam.C}"
            == "A,B,C"
        )
