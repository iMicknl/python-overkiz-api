"""Unit tests for the high-level OverkizClient behaviour and responses."""

from __future__ import annotations

import json
import os
from unittest.mock import patch

import aiohttp
import pytest
from pytest_asyncio import fixture

from pyoverkiz import exceptions
from pyoverkiz.client import OverkizClient
from pyoverkiz.const import SUPPORTED_SERVERS
from pyoverkiz.enums import APIType, DataType
from pyoverkiz.models import Option
from pyoverkiz.utils import generate_local_server

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


class TestOverkizClient:
    """Tests for the public OverkizClient behaviour (API type, devices, events, setup and diagnostics)."""

    @fixture
    async def client(self):
        """Fixture providing an OverkizClient configured for the cloud server."""
        return OverkizClient("username", "password", SUPPORTED_SERVERS["somfy_europe"])

    @fixture
    async def local_client(self):
        """Fixture providing an OverkizClient configured for a local (developer) server."""
        return OverkizClient(
            "username",
            "password",
            generate_local_server("gateway-1234-5678-1243.local:8443"),
        )

    @pytest.mark.asyncio
    async def test_get_api_type_cloud(self, client: OverkizClient):
        """Verify that a cloud-configured client reports APIType.CLOUD."""
        assert client.api_type == APIType.CLOUD

    @pytest.mark.asyncio
    async def test_get_api_type_local(self, local_client: OverkizClient):
        """Verify that a local-configured client reports APIType.LOCAL."""
        assert local_client.api_type == APIType.LOCAL

    @pytest.mark.asyncio
    async def test_get_devices_basic(self, client: OverkizClient):
        """Ensure the client can fetch and parse the basic devices fixture."""
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
        self, client: OverkizClient, fixture_name: str, event_length: int
    ):
        """Parameterised test that fetches events fixture and checks the expected count."""
        with open(
            os.path.join(CURRENT_DIR, "fixtures/event/" + fixture_name),
            encoding="utf-8",
        ) as raw_events:
            resp = MockResponse(raw_events.read())

        with patch.object(aiohttp.ClientSession, "post", return_value=resp):
            events = await client.fetch_events()
            assert len(events) == event_length

    @pytest.mark.asyncio
    async def test_fetch_events_simple_cast(self, client: OverkizClient):
        """Check that event state values from the cloud (strings) are cast to appropriate types."""
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
    async def test_fetch_events_casting(self, client: OverkizClient, fixture_name: str):
        """Validate that fetched event states are cast to the expected Python types for each data type."""
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
            ("setup_hi_kumo_8_gateways.json", 16, 8),
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
            ("setup_local_with_climate.json", 33, 1),
        ],
    )
    @pytest.mark.asyncio
    async def test_get_setup(
        self,
        client: OverkizClient,
        fixture_name: str,
        device_count: int,
        gateway_count: int,
    ):
        """Ensure setup parsing yields expected device and gateway counts and device metadata."""
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
            ("setup_hi_kumo_8_gateways.json"),
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
            ("setup_local_with_climate.json"),
        ],
    )
    @pytest.mark.asyncio
    async def test_get_diagnostic_data(self, client: OverkizClient, fixture_name: str):
        """Verify that diagnostic data can be fetched and is not empty."""
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
        """Ensure client raises the correct exception for various error fixtures/status codes."""
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

    @pytest.mark.asyncio
    async def test_get_setup_options(
        self,
        client: OverkizClient,
    ):
        """Check that setup options are parsed and return the expected number of Option instances."""
        with open(
            os.path.join(CURRENT_DIR, "fixtures/endpoints/setup-options.json"),
            encoding="utf-8",
        ) as raw_events:
            resp = MockResponse(raw_events.read())

        with patch.object(aiohttp.ClientSession, "get", return_value=resp):
            options = await client.get_setup_options()
            assert len(options) == 3

            for option in options:
                assert isinstance(option, Option)

    @pytest.mark.parametrize(
        "fixture_name, option_name, instance",
        [
            (
                "setup-options-developerMode.json",
                "developerMode-1234-5678-1234",
                Option,
            ),
            ("setup-options-empty.json", "test", None),
        ],
    )
    @pytest.mark.asyncio
    async def test_get_setup_option(
        self,
        client: OverkizClient,
        fixture_name: str,
        option_name: str,
        instance: Option | None,
    ):
        """Verify retrieval of a single setup option by name, including non-existent options."""
        with open(
            os.path.join(CURRENT_DIR, "fixtures/endpoints/" + fixture_name),
            encoding="utf-8",
        ) as raw_events:
            resp = MockResponse(raw_events.read())

        with patch.object(aiohttp.ClientSession, "get", return_value=resp):
            option = await client.get_setup_option(option_name)

            if instance is None:
                assert option is None
            else:
                assert isinstance(option, instance)

    @pytest.mark.parametrize(
        "fixture_name, scenario_count",
        [
            ("action-group-cozytouch.json", 9),
            ("action-group-tahoma-box-v1.json", 17),
            ("action-group-tahoma-classic-v2.json", 2),
            ("action-group-tahoma-switch.json", 1),
        ],
    )
    @pytest.mark.asyncio
    async def test_get_action_groups(
        self,
        client: OverkizClient,
        fixture_name: str,
        scenario_count: int,
    ):
        """Ensure action groups (scenarios) are parsed correctly and contain actions and commands."""
        with open(
            os.path.join(CURRENT_DIR, "fixtures/action_groups/" + fixture_name),
            encoding="utf-8",
        ) as action_group_mock:
            resp = MockResponse(action_group_mock.read())

        with patch.object(aiohttp.ClientSession, "get", return_value=resp):
            action_groups = await client.get_action_groups()

            assert len(action_groups) == scenario_count

            for action_group in action_groups:
                assert action_group.oid
                assert action_group.label is not None
                assert action_group.actions

                for action in action_group.actions:
                    assert action.device_url
                    assert action.commands

                    for command in action.commands:
                        assert command.name


class MockResponse:
    """Simple stand-in for aiohttp responses used in tests."""

    def __init__(self, text, status=200, url=""):
        """Create a mock response with text payload and optional status/url."""
        self._text = text
        self.status = status
        self.url = url

    async def text(self):
        """Return text payload asynchronously."""
        return self._text

    # pylint: disable=unused-argument
    async def json(self, content_type=None):
        """Return parsed JSON payload asynchronously."""
        return json.loads(self._text)

    async def __aexit__(self, exc_type, exc, tb):
        """Context manager exit (noop)."""
        pass

    async def __aenter__(self):
        """Context manager enter returning self."""
        return self
