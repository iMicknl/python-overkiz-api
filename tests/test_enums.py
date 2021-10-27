from pyhoma.enums import EventName, FailureType, GatewaySubType, GatewayType


class TestGatewayType:
    def test_missing(self):
        assert GatewayType(99) == GatewayType.UNKNOWN


class TestGatewaySubType:
    def test_missing(self):
        assert GatewaySubType(99) == GatewaySubType.UNKNOWN


class TestEventName:
    def test_missing(self):
        assert EventName(99) == EventName.UNKNOWN


class TestFailureType:
    def test_missing(self):
        assert FailureType(99) == FailureType.UNKNOWN
