from pyoverkiz.enums import EventName, FailureType, GatewaySubType, GatewayType


class TestGatewayType:
    def test_missing(self):
        assert GatewayType(102) == GatewayType.UNKNOWN

    def test_beautify_name(self):
        assert GatewayType.TAHOMA_V2.beautify_name == "TaHoma V2"
        assert (
            GatewayType.CONNEXOON_RTS_AUSTRALIA.beautify_name
            == "Connexoon RTS Australia"
        )
        assert GatewayType.COZYTOUCH_V2.beautify_name == "Cozytouch V2"


class TestGatewaySubType:
    def test_missing(self):
        assert GatewaySubType(99) == GatewaySubType.UNKNOWN

    def test_beautify_name(self):
        assert GatewaySubType.TAHOMA_SECURITY_PRO.beautify_name == "TaHoma Security Pro"


class TestEventName:
    def test_missing(self):
        assert EventName(99) == EventName.UNKNOWN


class TestFailureType:
    def test_missing(self):
        assert FailureType(99) == FailureType.UNKNOWN
