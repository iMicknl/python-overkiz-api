"""Tests for utility helper functions like server generation and gateway checks."""

import pytest

from pyoverkiz.utils import generate_local_server, is_overkiz_gateway

LOCAL_HOST = "gateway-1234-5678-1243.local:8443"
LOCAL_HOST_BY_IP = "192.168.1.105:8443"


class TestUtils:
    """Tests for utility helpers like local server generation and gateway checks."""

    def test_generate_local_server(self):
        """Create a local server descriptor using the host and default values."""
        local_server = generate_local_server(host=LOCAL_HOST)

        assert local_server
        assert (
            local_server.endpoint
            == "https://gateway-1234-5678-1243.local:8443/enduser-mobile-web/1/enduserAPI/"
        )
        assert local_server.manufacturer == "Somfy"
        assert local_server.name == "Somfy Developer Mode"
        assert local_server.configuration_url is None

    def test_generate_local_server_by_ip(self):
        """Create a local server descriptor using an IP host and custom fields."""
        local_server = generate_local_server(
            host=LOCAL_HOST_BY_IP,
            manufacturer="Test Manufacturer",
            name="Test Name",
            configuration_url="https://somfy.com",
        )

        assert local_server
        assert (
            local_server.endpoint
            == "https://192.168.1.105:8443/enduser-mobile-web/1/enduserAPI/"
        )
        assert local_server.manufacturer == "Test Manufacturer"
        assert local_server.name == "Test Name"
        assert local_server.configuration_url == "https://somfy.com"

    @pytest.mark.parametrize(
        "gateway_id, overkiz_gateway",
        [
            ("1234-5678-6968", True),
            ("SOMFY_PROTECT-v0NT53occUBPyuJRzx59kalW1hFfzimN", False),
            ("SOMFY_THERMOSTAT-19649", False),
        ],
    )
    def test_is_overkiz_gateway(self, gateway_id: str, overkiz_gateway: bool):
        """Detect whether a gateway id follows the Overkiz gateway pattern."""
        assert is_overkiz_gateway(gateway_id) == overkiz_gateway
