import pytest

from pyoverkiz.obfuscate import obfuscate_email, obfuscate_sensitive_data

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

class TestObfucscateSensitive:
    def test_obfuscate_list_with_none(self):
        input = {'d': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, None, None, None, None, None, None, None]}
        assert obfuscate_sensitive_data(input) == input
