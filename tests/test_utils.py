from pyoverkiz.utils import generate_local_server

LOCAL_HOST = "gateway-1234-5678-1243.local:8443"


class TestUtils:
    def test_empty_states(self):

        local_server = generate_local_server(host=LOCAL_HOST)

        assert local_server
        assert (
            local_server.endpoint
            == "https://gateway-1234-5678-1243.local:8443/enduser-mobile-web/1/enduserAPI/"
        )
        assert local_server.manufacturer == "Somfy"
        assert local_server.name == "Somfy Developer Mode"
