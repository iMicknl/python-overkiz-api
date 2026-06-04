"""Tests for enum helper behaviour and expected values."""

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


class TestOverkizCommandParamApiValues:
    """Guard against casing regressions in state-comparison params (see #2093).

    The real Overkiz API returns these state values in lowercase. A capitalized
    command-input value in the server catalog (e.g. Hi Kumo's ``["On", "Off"]``)
    must never clobber the lowercase value that downstream consumers compare
    against, so pin the expected API values here.
    """

    def test_lowercase_state_values(self):
        """ON/OFF/UNKNOWN/BATTERY must equal their lowercase API state values."""
        assert OverkizCommandParam.ON == "on"
        assert OverkizCommandParam.OFF == "off"
        assert OverkizCommandParam.UNKNOWN == "unknown"
        assert OverkizCommandParam.BATTERY == "battery"
        assert OverkizCommandParam.STANDARD == "standard"
        assert OverkizCommandParam.HISTORICAL == "historical"
        assert OverkizCommandParam.ERROR == "error"
        assert OverkizCommandParam.UNHEALTHY == "unhealthy"
