import pytest

from pyoverkiz.obfuscate import obfuscate_email

LOCAL_HOST = "gateway-1234-5678-1243.local:8443"
LOCAL_HOST_BY_IP = "192.168.1.105:8443"


class TestObfucscate:
    @pytest.mark.parametrize(
        "email, obfuscated",
        [
            ("contact@somfy.com", "c****@****y.com"),
            ("contact_-_nexity.com", "c****@****y.com"),
        ],
    )
    def test_email_obfuscate(self, email: str, obfuscated: str):
        assert obfuscate_email(email) == obfuscated
