import json
import os
from unittest.mock import patch

import aiohttp
import pytest
from pytest import fixture

from pyhoma.client import TahomaClient
from pyhoma.models import OverkizServer

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


class TestTahomaClient:
    @fixture
    def api(self):
        return TahomaClient("username", "password", OverkizServer())

    @pytest.mark.asyncio
    async def test_get_devices_basic(self, api):
        with open(
            os.path.join(CURRENT_DIR, "devices.json"), encoding="utf-8"
        ) as raw_devices:
            resp = MockResponse(raw_devices.read())

        with patch.object(aiohttp.ClientSession, "get", return_value=resp):
            devices = await api.get_devices()
            assert len(devices) == 23

    @pytest.mark.asyncio
    async def test_fetch_events_basic(self, api):
        with open(
            os.path.join(CURRENT_DIR, "events.json"), encoding="utf-8"
        ) as raw_events:
            resp = MockResponse(raw_events.read())

        with patch.object(aiohttp.ClientSession, "post", return_value=resp):
            events = await api.fetch_events()
            assert len(events) == 16


class MockResponse:
    def __init__(self, text, status=200):
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
