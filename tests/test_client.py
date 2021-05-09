import json
import os
from unittest.mock import patch

import aiohttp
import pytest

from pyhoma.client import TahomaClient
from pytest import fixture

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


class TestTahomaClient:

    @fixture
    def api(self):
        return TahomaClient("username", "password")

    @pytest.mark.asyncio
    async def test_get_devices_basic(self, api):
        with open(os.path.join(CURRENT_DIR, "devices.json")) as raw_devices:
            resp = MockResponse(raw_devices.read(), 200)

        with patch.object(aiohttp.ClientSession, 'get', return_value=resp):
            devices = await api.get_devices()
            assert len(devices) == 23


class MockResponse:
    def __init__(self, text, status):
        self._text = text
        self.status = status

    async def text(self):
        return self._text

    async def json(self):
        return json.loads(self._text)

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def __aenter__(self):
        return self
