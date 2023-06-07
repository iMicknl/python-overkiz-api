import json
import os
from unittest.mock import patch

import aiohttp
import pytest
from pytest import fixture

from pyoverkiz import exceptions
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

    @pytest.mark.parametrize(
        "fixture_name, event_length",
        [
            ("events.json", 16),
            ("local_events.json", 3),
        ],
    )
    @pytest.mark.asyncio
    async def test_fetch_events_basic(
        self, client, fixture_name: str, event_length: int
    ):
        with open(
            os.path.join(CURRENT_DIR, "fixtures/event/" + fixture_name),
            encoding="utf-8",
        ) as raw_events:
            resp = MockResponse(raw_events.read())

        with patch.object(aiohttp.ClientSession, "post", return_value=resp):
            events = await client.fetch_events()
            assert len(events) == event_length

    @pytest.mark.asyncio
    async def test_fetch_events_simple_cast(self, client):
        with open(
            os.path.join(CURRENT_DIR, "fixtures/event/events.json"), encoding="utf-8"
        ) as raw_events:
            resp = MockResponse(raw_events.read())

        with patch.object(aiohttp.ClientSession, "post", return_value=resp):
            events = await client.fetch_events()

            # check if str to integer cast was succesfull
            int_state_event = events[2].device_states[0]
            assert int_state_event.value == 23247220
            assert isinstance(int_state_event.value, int)
            assert int_state_event.type == DataType.INTEGER

    @pytest.mark.parametrize(
        "fixture_name",
        [
            ("events.json"),
            ("local_events.json"),
        ],
    )
    @pytest.mark.asyncio
    async def test_fetch_events_casting(self, client, fixture_name: str):
        with open(
            os.path.join(CURRENT_DIR, "fixtures/event/" + fixture_name),
            encoding="utf-8",
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
        "fixture_name, device_count, gateway_count",
        [
            ("setup_3_gateways.json", 37, 3),
            ("setup_cozytouch.json", 12, 1),
            ("setup_cozytouch_v2.json", 5, 1),
            ("setup_cozytouch_2.json", 15, 1),
            ("setup_cozytouch_3.json", 15, 1),
            ("setup_hi_kumo.json", 3, 1),
            ("setup_hi_kumo_2.json", 3, 1),
            ("setup_nexity.json", 18, 1),
            ("setup_nexity_2.json", 17, 1),
            ("setup_rexel.json", 18, 1),
            ("setup_tahoma_1.json", 1, 1),
            ("setup_tahoma_3.json", 39, 1),
            ("setup_tahoma_climate.json", 19, 1),
            ("setup_tahoma_oceania.json", 3, 1),
            ("setup_tahoma_pro.json", 12, 1),
            ("setup_hue_and_low_speed.json", 40, 1),
            ("setup_tahoma_siren_io.json", 11, 1),
            ("setup_tahoma_siren_rtd.json", 31, 1),
            ("setup_tahoma_be.json", 15, 1),
            ("setup_local.json", 3, 1),
            ("setup_local_tahoma.json", 8, 1),
        ],
    )
    @pytest.mark.asyncio
    async def test_get_setup(
        self, client, fixture_name: str, device_count: int, gateway_count: int
    ):
        with open(
            os.path.join(CURRENT_DIR, "fixtures/setup/" + fixture_name),
            encoding="utf-8",
        ) as setup_mock:
            resp = MockResponse(setup_mock.read())

        with patch.object(aiohttp.ClientSession, "get", return_value=resp):
            setup = await client.get_setup()

            assert len(setup.devices) == device_count
            assert len(setup.gateways) == gateway_count

            for device in setup.devices:
                assert device.gateway_id
                assert device.device_address
                assert device.protocol

    @pytest.mark.parametrize(
        "fixture_name",
        [
            ("setup_3_gateways.json"),
            ("setup_cozytouch.json"),
            ("setup_cozytouch_v2.json"),
            ("setup_cozytouch_2.json"),
            ("setup_cozytouch_3.json"),
            ("setup_cozytouch_4.json"),
            ("setup_hi_kumo.json"),
            ("setup_hi_kumo_2.json"),
            ("setup_nexity.json"),
            ("setup_nexity_2.json"),
            ("setup_rexel.json"),
            ("setup_tahoma_1.json"),
            ("setup_tahoma_3.json"),
            ("setup_tahoma_climate.json"),
            ("setup_tahoma_oceania.json"),
            ("setup_tahoma_pro.json"),
            ("setup_hue_and_low_speed.json"),
            ("setup_tahoma_siren_io.json"),
            ("setup_tahoma_siren_rtd.json"),
            ("setup_tahoma_be.json"),
            ("setup_local.json"),
            ("setup_local_tahoma.json"),
        ],
    )
    @pytest.mark.asyncio
    async def test_get_diagnostic_data(self, client: OverkizClient, fixture_name: str):
        with open(
            os.path.join(CURRENT_DIR, "fixtures/setup/" + fixture_name),
            encoding="utf-8",
        ) as setup_mock:
            resp = MockResponse(setup_mock.read())

        with patch.object(aiohttp.ClientSession, "get", return_value=resp):
            diagnostics = await client.get_diagnostic_data()
            assert diagnostics

    @pytest.mark.parametrize(
        "fixture_name, exception, status_code",
        [
            ("cloud/503-empty.html", exceptions.ServiceUnavailableException, 503),
            ("cloud/503-maintenance.html", exceptions.MaintenanceException, 503),
            (
                "cloud/access-denied-to-gateway.json",
                exceptions.AccessDeniedToGatewayException,
                400,
            ),
            (
                "cloud/bad-credentials.json",
                exceptions.BadCredentialsException,
                400,
            ),
            (
                "cloud/missing-authorization-token.json",
                exceptions.MissingAuthorizationTokenException,
                400,
            ),
            (
                "cloud/no-registered-event-listener.json",
                exceptions.NoRegisteredEventListenerException,
                400,
            ),
            (
                "cloud/too-many-concurrent-requests.json",
                exceptions.TooManyConcurrentRequestsException,
                400,
            ),
            (
                "cloud/too-many-executions.json",
                exceptions.TooManyExecutionsException,
                400,
            ),
            (
                "cloud/too-many-requests.json",
                exceptions.TooManyRequestsException,
                400,
            ),
            # (
            #     "local/204-no-corresponding-execId.json",
            #     exceptions.OverkizException,
            #     204,
            # ),
            (
                "local/400-bad-parameters.json",
                exceptions.OverkizException,
                400,
            ),
            ("local/400-bus-error.json", exceptions.OverkizException, 400),
            (
                "local/400-malformed-action-group.json",
                exceptions.OverkizException,
                400,
            ),
            (
                "local/400-malformed-fetch-id.json",
                exceptions.OverkizException,
                400,
            ),
            (
                "local/400-missing-execution-id.json",
                exceptions.OverkizException,
                400,
            ),
            (
                "local/400-missing-parameters.json",
                exceptions.OverkizException,
                400,
            ),
            (
                "local/400-no-registered-event-listener.json",
                exceptions.NoRegisteredEventListenerException,
                400,
            ),
            (
                "local/400-no-such-device.json",
                exceptions.OverkizException,
                400,
            ),
            (
                "local/400-unknown-object.json",
                exceptions.UnknownObjectException,
                400,
            ),
            (
                "local/400-unspecified-error.json",
                exceptions.OverkizException,
                400,
            ),
            (
                "local/401-missing-authorization-token.json",
                exceptions.MissingAuthorizationTokenException,
                401,
            ),
            (
                "local/401-not-authenticated.json",
                exceptions.NotAuthenticatedException,
                401,
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_check_response_exception_handling(
        self,
        client: OverkizClient,
        fixture_name: str,
        status_code: int,
        exception: Exception,
    ):
        with pytest.raises(exception):
            if fixture_name:
                with open(
                    os.path.join(CURRENT_DIR, "fixtures/exceptions/" + fixture_name),
                    encoding="utf-8",
                ) as raw_events:
                    resp = MockResponse(raw_events.read(), status_code)
            else:
                resp = MockResponse(None, status_code)

            await client.check_response(resp)


class MockResponse:
    def __init__(self, text, status=200, url=""):
        self._text = text
        self.status = status
        self.url = url

    async def text(self):
        return self._text

    # pylint: disable=unused-argument
    async def json(self, content_type=None):
        return json.loads(self._text)

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def __aenter__(self):
        return self
