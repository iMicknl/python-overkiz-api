import json
import os
from unittest.mock import patch

import aiohttp
import pytest
from pytest import fixture

from pyoverkiz.client import OverkizClient
from pyoverkiz.const import SUPPORTED_SERVERS
from pyoverkiz.enums import DataType

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


class TestOverkizClient:
    @fixture
    def client(self):
        return OverkizClient("username", "password", SUPPORTED_SERVERS["somfy_europe"])

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

    @pytest.mark.asyncio
    async def test_fetch_events_simple_cast(self, client):
        with open(
            os.path.join(CURRENT_DIR, "events.json"), encoding="utf-8"
        ) as raw_events:
            resp = MockResponse(raw_events.read())

        with patch.object(aiohttp.ClientSession, "post", return_value=resp):
            events = await client.fetch_events()

            # check if str to integer cast was succesfull
            int_state_event = events[2].device_states[0]
            assert int_state_event.value == 23247220
            assert isinstance(int_state_event.value, int)
            assert int_state_event.type == DataType.INTEGER

    @pytest.mark.asyncio
    async def test_fetch_events_casting(self, client):
        with open(
            os.path.join(CURRENT_DIR, "events.json"), encoding="utf-8"
        ) as raw_events:
            resp = MockResponse(raw_events.read())

        with patch.object(aiohttp.ClientSession, "post", return_value=resp):
            events = await client.fetch_events()

            for event in events:
                for state in event.device_states:

                    if state.type == 0:
                        assert state.value is None

                    if state.type == 1:
                        assert isinstance(state.value, int)

                    if state.type == 2:
                        assert isinstance(state.value, float)

                    if state.type == 3:
                        assert isinstance(state.value, str)

                    if state.type == 6:
                        assert isinstance(state.value, bool)

                    if state.type == 10:
                        assert isinstance(state.value, list)

                    if state.type == 11:
                        assert isinstance(state.value, dict)

    @pytest.mark.parametrize(
        "fixture_name, device_count",
        [
            ("setup_cozytouch.json", 12),
            ("setup_cozytouch2.json", 15),
            ("setup_hi_kumo.json", 3),
            ("setup_hi_kumo2.json", 3),
            ("setup_nexity.json", 18),
            ("setup_rexel.json", 18),
            ("setup_tahoma_3.json", 39),
            ("setup_tahoma_climate.json", 19),
            ("setup_tahoma_oceania.json", 3),
            ("setup_tahoma_pro.json", 12),
            ("setup_hue_and_low_speed.json", 40),
            ("setup_tahoma_siren_io.json", 11),
            ("setup_tahoma_siren_rtd.json", 31),
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
            assert len(setup.gateways) == 1


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
