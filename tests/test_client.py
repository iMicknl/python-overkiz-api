import json
import os
from unittest.mock import patch

import aiohttp
import pytest
from pytest import fixture

from pyhoma.client import TahomaClient
from pyhoma.const import SUPPORTED_SERVERS

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


class TestTahomaClient:
    @fixture
    def client(self):
        return TahomaClient("username", "password", SUPPORTED_SERVERS["somfy_europe"])

    @pytest.mark.asyncio
    async def test_get_devices_basic(self, client):
        with open(
            os.path.join(CURRENT_DIR, "devices.json"), encoding="utf-8"
        ) as raw_devices:
            resp = MockResponse(raw_devices.read())

        with patch.object(aiohttp.ClientSession, "get", return_value=resp):
            devices = await client.get_devices()
            assert len(devices) == 23

    @pytest.mark.asyncio
    async def test_fetch_events_basic(self, client):
        with open(
            os.path.join(CURRENT_DIR, "events.json"), encoding="utf-8"
        ) as raw_events:
            resp = MockResponse(raw_events.read())

        with patch.object(aiohttp.ClientSession, "post", return_value=resp):
            events = await client.fetch_events()
            assert len(events) == 16

    @pytest.mark.parametrize(
        "fixture_name, device_count",
        [
            ("setup_cozytouch.json", 12),
            ("setup_hi_kumo.json", 3),
            ("setup_hi_kumo2.json", 3),
            ("setup_nexity.json", 18),
            ("setup_rexel.json", 18),
            ("setup_tahoma_3.json", 39),
            ("setup_tahoma_climate.json", 19),
            ("setup_tahoma_oceania.json", 3),
            ("setup_tahoma_pro.json", 12),
        ],
    )
    @pytest.mark.asyncio
    async def test_get_setup(self, client, fixture_name: str, device_count: int):
        with open(
            os.path.join(CURRENT_DIR, "fixtures/setup/" + fixture_name),
            encoding="utf-8",
        ) as setup_mock:
            resp = MockResponse(setup_mock.read())

        with patch.object(aiohttp.ClientSession, "get", return_value=resp):
            setup = await client.get_setup()

            assert len(setup.devices) == device_count


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
