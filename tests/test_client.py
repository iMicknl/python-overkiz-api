"""Unit tests for the high-level OverkizClient behaviour and responses."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest

from pyoverkiz import exceptions
from pyoverkiz.client import OverkizClient
from pyoverkiz.enums import (
    APIType,
    DataType,
    ExecutionState,
    ExecutionSubType,
    ExecutionType,
)
from pyoverkiz.models import (
    Action,
    Command,
    Execution,
    HistoryExecution,
    Option,
    Place,
    State,
)
from pyoverkiz.response_handler import check_response
from tests.helpers import MockResponse

CURRENT_DIR = Path(__file__).resolve().parent


class TestOverkizClient:
    """Tests for the public OverkizClient behaviour (API type, devices, events, setup and diagnostics)."""

    @pytest.mark.asyncio
    async def test_get_api_type_cloud(self, client: OverkizClient):
        """Verify that a cloud-configured client reports APIType.CLOUD."""
        assert client.server_config.api_type == APIType.CLOUD

    @pytest.mark.asyncio
    async def test_get_api_type_local(self, local_client: OverkizClient):
        """Verify that a local-configured client reports APIType.LOCAL."""
        assert local_client.server_config.api_type == APIType.LOCAL

    @pytest.mark.asyncio
    async def test_get_devices_basic(self, client: OverkizClient):
        """Ensure the client can fetch and parse the basic devices fixture."""
        with (CURRENT_DIR / "devices.json").open(encoding="utf-8") as raw_devices:
            resp = MockResponse(raw_devices.read())

        with patch.object(aiohttp.ClientSession, "get", return_value=resp):
            devices = await client.get_devices()
            assert len(devices) == 23

    @pytest.mark.parametrize(
        ("fixture_name", "event_length"),
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
        with (CURRENT_DIR / "fixtures" / "event" / fixture_name).open(
            encoding="utf-8",
        ) as raw_events:
            resp = MockResponse(raw_events.read())

        with patch.object(aiohttp.ClientSession, "post", return_value=resp):
            events = await client.fetch_events()
            assert len(events) == event_length

    @pytest.mark.asyncio
    async def test_fetch_events_simple_cast(self, client: OverkizClient):
        """Check that event state values from the cloud (strings) are cast to appropriate types."""
        with (CURRENT_DIR / "fixtures" / "event" / "events.json").open(
            encoding="utf-8",
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
    async def test_backoff_relogin_on_auth_error(self, client: OverkizClient):
        """Ensure auth backoff retries and triggers `login()` on failure."""
        client.login = AsyncMock()

        with (
            patch("backoff._async.asyncio.sleep", new=AsyncMock()) as sleep_mock,
            patch.object(
                OverkizClient,
                "_get",
                new=AsyncMock(
                    side_effect=[
                        exceptions.NotAuthenticatedError("expired"),
                        {"protocolVersion": "1"},
                    ]
                ),
            ) as get_mock,
        ):
            result = await client.get_api_version()

        assert result == "1"
        assert get_mock.await_count == 2
        assert client.login.await_count == 1
        assert sleep_mock.await_count == 1

    @pytest.mark.asyncio
    async def test_backoff_refresh_listener_on_listener_error(
        self, client: OverkizClient
    ) -> None:
        """Ensure listener backoff retries and triggers `register_event_listener()`."""
        client.event_listener_id = "listener-1"
        client.register_event_listener = AsyncMock(return_value="listener-2")

        with (
            patch("backoff._async.asyncio.sleep", new=AsyncMock()) as sleep_mock,
            patch.object(
                OverkizClient,
                "_post",
                new=AsyncMock(
                    side_effect=[
                        exceptions.InvalidEventListenerIdError("bad listener"),
                        [],
                    ]
                ),
            ) as post_mock,
        ):
            events = await client.fetch_events()

        assert events == []
        assert post_mock.await_count == 2
        assert client.register_event_listener.await_count == 1
        assert sleep_mock.await_count == 1

    @pytest.mark.asyncio
    async def test_backoff_retries_on_concurrent_requests(
        self, client: OverkizClient
    ) -> None:
        """Ensure concurrent request backoff retries and succeeds afterwards."""
        with (
            patch("backoff._async.asyncio.sleep", new=AsyncMock()) as sleep_mock,
            patch.object(
                OverkizClient,
                "_post",
                new=AsyncMock(
                    side_effect=[
                        exceptions.TooManyConcurrentRequestsError("busy"),
                        {"id": "listener-3"},
                    ]
                ),
            ) as post_mock,
        ):
            listener_id = await client.register_event_listener()

        assert listener_id == "listener-3"
        assert post_mock.await_count == 2
        assert sleep_mock.await_count == 1

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
        with (CURRENT_DIR / "fixtures" / "event" / fixture_name).open(
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
        ("fixture_name", "device_count", "gateway_count"),
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
        with (CURRENT_DIR / "fixtures" / "setup" / fixture_name).open(
            encoding="utf-8",
        ) as setup_mock:
            resp = MockResponse(setup_mock.read())

        with patch.object(aiohttp.ClientSession, "get", return_value=resp):
            setup = await client.get_setup()

            assert len(setup.devices) == device_count
            assert len(setup.gateways) == gateway_count

            if fixture_name.startswith("setup_local"):
                assert setup.id is None

            for device in setup.devices:
                assert device.identifier.gateway_id is not None
                assert device.identifier.device_address is not None
                assert device.identifier.protocol is not None

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
        with (CURRENT_DIR / "fixtures" / "setup" / fixture_name).open(
            encoding="utf-8",
        ) as setup_mock:
            resp = MockResponse(setup_mock.read())

        with patch.object(aiohttp.ClientSession, "get", return_value=resp):
            diagnostics = await client.get_diagnostic_data()
            assert diagnostics

    @pytest.mark.asyncio
    async def test_get_diagnostic_data_redacted_by_default(self, client: OverkizClient):
        """Ensure diagnostics are redacted when no argument is provided."""
        with (CURRENT_DIR / "fixtures" / "setup" / "setup_tahoma_1.json").open(
            encoding="utf-8",
        ) as setup_mock:
            resp = MockResponse(setup_mock.read())

        with (
            patch.object(aiohttp.ClientSession, "get", return_value=resp),
            patch(
                "pyoverkiz.client.obfuscate_sensitive_data",
                return_value={"masked": True},
            ) as obfuscate,
        ):
            diagnostics = await client.get_diagnostic_data()
            assert diagnostics == {"masked": True}
            obfuscate.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_diagnostic_data_without_masking(self, client: OverkizClient):
        """Ensure diagnostics can be returned without masking when requested."""
        with (CURRENT_DIR / "fixtures" / "setup" / "setup_tahoma_1.json").open(
            encoding="utf-8",
        ) as setup_mock:
            raw_setup = setup_mock.read()
            resp = MockResponse(raw_setup)

        with (
            patch.object(aiohttp.ClientSession, "get", return_value=resp),
            patch("pyoverkiz.client.obfuscate_sensitive_data") as obfuscate,
        ):
            diagnostics = await client.get_diagnostic_data(mask_sensitive_data=False)
            assert diagnostics == json.loads(raw_setup)
            obfuscate.assert_not_called()

    @pytest.mark.parametrize(
        ("fixture_name", "exception", "status_code"),
        [
            ("cloud/503-empty.html", exceptions.ServiceUnavailableError, 503),
            ("cloud/503-maintenance.html", exceptions.MaintenanceError, 503),
            (
                "cloud/access-denied-to-gateway.json",
                exceptions.AccessDeniedToGatewayError,
                400,
            ),
            (
                "cloud/application-not-allowed.json",
                exceptions.ApplicationNotAllowedError,
                400,
            ),
            (
                "cloud/bad-credentials.json",
                exceptions.BadCredentialsError,
                400,
            ),
            (
                "cloud/missing-authorization-token.json",
                exceptions.MissingAuthorizationTokenError,
                400,
            ),
            (
                "cloud/no-registered-event-listener.json",
                exceptions.NoRegisteredEventListenerError,
                400,
            ),
            (
                "cloud/too-many-concurrent-requests.json",
                exceptions.TooManyConcurrentRequestsError,
                400,
            ),
            (
                "cloud/too-many-executions.json",
                exceptions.TooManyExecutionsError,
                400,
            ),
            (
                "cloud/too-many-requests.json",
                exceptions.TooManyRequestsError,
                400,
            ),
            (
                "cloud/no-such-resource.json",
                exceptions.NoSuchResourceError,
                400,
            ),
            (
                "cloud/exec-queue-full.json",
                exceptions.ExecutionQueueFullError,
                400,
            ),
            (
                "cloud/missing-api-key.json",
                exceptions.MissingAPIKeyError,
                400,
            ),
            (
                "cloud/unknown-user-account.json",
                exceptions.UnknownUserError,
                400,
            ),
            (
                "cloud/no-such-command.json",
                exceptions.InvalidCommandError,
                400,
            ),
            (
                "cloud/invalid-event-listener-id.json",
                exceptions.InvalidEventListenerIdError,
                400,
            ),
            (
                "cloud/session-and-bearer.json",
                exceptions.SessionAndBearerInSameRequestError,
                400,
            ),
            (
                "cloud/too-many-attempts-banned.json",
                exceptions.TooManyAttemptsBannedError,
                400,
            ),
            (
                "cloud/invalid-token.json",
                exceptions.InvalidTokenError,
                400,
            ),
            (
                "cloud/not-such-token.json",
                exceptions.NoSuchTokenError,
                400,
            ),
            (
                "cloud/unknown-auth-error.json",
                exceptions.BadCredentialsError,
                400,
            ),
            (
                "cloud/unknown-resource-access-denied.json",
                exceptions.ResourceAccessDeniedError,
                400,
            ),
            (
                "cloud/resource-access-denied-device-setup-mismatch.json",
                exceptions.ResourceAccessDeniedError,
                400,
            ),
            (
                "cloud/resource-access-denied-gateway-not-in-setup.json",
                exceptions.ResourceAccessDeniedError,
                400,
            ),
            (
                "cloud/no-such-action-group.json",
                exceptions.NoSuchActionGroupError,
                404,
            ),
            (
                "cloud/action-group-setup-not-found.json",
                exceptions.ActionGroupSetupNotFoundError,
                400,
            ),
            (
                "cloud/no-such-controllable.json",
                exceptions.OverkizError,
                400,
            ),
            (
                "cloud/no-such-ui-profile.json",
                exceptions.OverkizError,
                400,
            ),
            (
                "local/400-bad-parameters.json",
                exceptions.OverkizError,
                400,
            ),
            ("local/400-bus-error.json", exceptions.OverkizError, 400),
            (
                "local/400-malformed-action-group.json",
                exceptions.OverkizError,
                400,
            ),
            (
                "local/400-malformed-fetch-id.json",
                exceptions.OverkizError,
                400,
            ),
            (
                "local/400-missing-execution-id.json",
                exceptions.OverkizError,
                400,
            ),
            (
                "local/400-missing-parameters.json",
                exceptions.OverkizError,
                400,
            ),
            (
                "local/400-duplicate-action-on-device.json",
                exceptions.DuplicateActionOnDeviceError,
                400,
            ),
            (
                "local/400-action-group-setup-not-found.json",
                exceptions.ActionGroupSetupNotFoundError,
                400,
            ),
            (
                "local/400-no-registered-event-listener.json",
                exceptions.NoRegisteredEventListenerError,
                400,
            ),
            (
                "local/400-no-such-device.json",
                exceptions.NoSuchDeviceError,
                400,
            ),
            (
                "local/400-unknown-object.json",
                exceptions.UnknownObjectError,
                400,
            ),
            (
                "local/400-unspecified-error.json",
                exceptions.OverkizError,
                400,
            ),
            (
                "local/401-missing-authorization-token.json",
                exceptions.MissingAuthorizationTokenError,
                401,
            ),
            (
                "local/401-not-authenticated.json",
                exceptions.NotAuthenticatedError,
                401,
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_check_response_exception_handling(
        self,
        fixture_name: str,
        status_code: int,
        exception: Exception,
    ):
        """Ensure client raises the correct error for various error fixtures/status codes."""
        if fixture_name:
            with (CURRENT_DIR / "fixtures" / "exceptions" / fixture_name).open(
                encoding="utf-8",
            ) as raw_events:
                resp = MockResponse(raw_events.read(), status_code)
        else:
            resp = MockResponse(None, status_code)

        with pytest.raises(exception):
            await check_response(resp)

    @pytest.mark.asyncio
    async def test_get_setup_options(
        self,
        client: OverkizClient,
    ):
        """Check that setup options are parsed and return the expected number of Option instances."""
        with (CURRENT_DIR / "fixtures" / "endpoints" / "setup-options.json").open(
            encoding="utf-8",
        ) as raw_events:
            resp = MockResponse(raw_events.read())

        with patch.object(aiohttp.ClientSession, "get", return_value=resp):
            options = await client.get_setup_options()
            assert len(options) == 3

            for option in options:
                assert isinstance(option, Option)

    @pytest.mark.asyncio
    async def test_get_returns_none_for_204_without_json_parse(
        self, client: OverkizClient
    ) -> None:
        """Ensure `_get` skips JSON parsing for 204 responses and returns `None`."""
        resp = MockResponse("", status=204)
        resp.json = AsyncMock(return_value={})

        with (
            patch.object(client, "_refresh_token_if_expired", new=AsyncMock()),
            patch.object(aiohttp.ClientSession, "get", return_value=resp),
        ):
            result = await client._get("setup/options")

        assert result is None
        assert not resp.json.called

    @pytest.mark.asyncio
    async def test_post_returns_none_for_204_without_json_parse(
        self, client: OverkizClient
    ) -> None:
        """Ensure `_post` skips JSON parsing for 204 responses and returns `None`."""
        resp = MockResponse("", status=204)
        resp.json = AsyncMock(return_value={})

        with (
            patch.object(client, "_refresh_token_if_expired", new=AsyncMock()),
            patch.object(aiohttp.ClientSession, "post", return_value=resp),
        ):
            result = await client._post("setup/devices/states/refresh")

        assert result is None
        assert not resp.json.called

    @pytest.mark.asyncio
    async def test_execute_action_group_omits_none_fields(self, client: OverkizClient):
        """Ensure `type` and `parameters` that are None are omitted from the request payload."""
        from pyoverkiz.enums.command import OverkizCommand
        from pyoverkiz.models import Action, Command

        action = Action(
            device_url="rts://2025-8464-6867/16756006",
            commands=[Command(name=OverkizCommand.CLOSE, parameters=None, type=None)],
        )

        resp = MockResponse('{"execId": "exec-123"}')

        with patch.object(aiohttp.ClientSession, "post") as mock_post:
            mock_post.return_value = resp

            exec_id = await client.execute_action_group([action])

            assert exec_id == "exec-123"

            assert mock_post.called
            _, kwargs = mock_post.call_args
            sent_json = kwargs.get("json")
            assert sent_json is not None

            # The client should have converted payload to camelCase and applied
            # abbreviation fixes (deviceURL) before sending.
            action_sent = sent_json["actions"][0]
            assert action_sent.get("deviceURL") == action.device_url

            cmd = action_sent["commands"][0]
            assert "type" not in cmd
            assert "parameters" not in cmd
            assert cmd["name"] == "close"

    @pytest.mark.parametrize(
        ("fixture_name", "option_name", "instance"),
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
        with (CURRENT_DIR / "fixtures" / "endpoints" / fixture_name).open(
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
        "fixture_name",
        [
            "exec-current-empty-object.json",
            "exec-current-empty-list.json",
        ],
    )
    @pytest.mark.asyncio
    async def test_get_current_execution_returns_none_for_empty_response(
        self,
        client: OverkizClient,
        fixture_name: str,
    ):
        """Cloud returns {} and local returns [] for non-existent exec_ids."""
        with (CURRENT_DIR / "fixtures" / "endpoints" / fixture_name).open(
            encoding="utf-8",
        ) as f:
            resp = MockResponse(f.read())

        with patch.object(aiohttp.ClientSession, "get", return_value=resp):
            result = await client.get_current_execution(
                "00000000-0000-0000-0000-000000000000"
            )
            assert result is None

    @pytest.mark.parametrize(
        ("fixture_name", "scenario_count"),
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
        with (CURRENT_DIR / "fixtures" / "action_groups" / fixture_name).open(
            encoding="utf-8",
        ) as action_group_mock:
            resp = MockResponse(action_group_mock.read())

        with patch.object(aiohttp.ClientSession, "get", return_value=resp):
            action_groups = await client.get_action_groups()

            assert len(action_groups) == scenario_count

            for action_group in action_groups:
                assert action_group.oid is not None
                assert action_group.label is not None
                assert action_group.actions

                for action in action_group.actions:
                    assert action.device_url is not None
                    assert action.commands

                    for command in action.commands:
                        assert command.name is not None

    @pytest.mark.asyncio
    async def test_get_current_execution_returns_execution(self, client: OverkizClient):
        """Verify a running execution is parsed into an Execution model."""
        with (CURRENT_DIR / "fixtures" / "exec" / "current-single.json").open(
            encoding="utf-8",
        ) as f:
            resp = MockResponse(f.read())

        with patch.object(aiohttp.ClientSession, "get", return_value=resp):
            result = await client.get_current_execution(
                "699dd967-0a19-0481-7a62-99b990a2feb8"
            )
            assert isinstance(result, Execution)
            assert result.id == "699dd967-0a19-0481-7a62-99b990a2feb8"
            assert result.state == ExecutionState.TRANSMITTED
            assert result.start_time == 1767003511145
            assert result.execution_type == ExecutionType.IMMEDIATE_EXECUTION
            assert result.execution_sub_type == ExecutionSubType.MANUAL_CONTROL
            assert result.action_group.oid is None
            assert (
                result.action_group.actions[0].device_url
                == "rts://1234-5678-1234/12345678"
            )

    @pytest.mark.asyncio
    async def test_get_current_executions(self, client: OverkizClient):
        """Verify parsing a list of running executions with RTS device commands."""
        with (CURRENT_DIR / "fixtures" / "exec" / "current-tahoma-switch.json").open(
            encoding="utf-8",
        ) as f:
            resp = MockResponse(f.read())

        with patch.object(aiohttp.ClientSession, "get", return_value=resp):
            executions = await client.get_current_executions()
            assert len(executions) == 1
            assert isinstance(executions[0], Execution)
            assert executions[0].state == ExecutionState.TRANSMITTED
            assert len(executions[0].action_group.actions) == 2
            assert executions[0].action_group.actions[0].commands[0].name == "close"
            assert executions[0].action_group.actions[1].commands[0].name == "identify"

    @pytest.mark.asyncio
    async def test_get_execution_history(self, client: OverkizClient):
        """Verify execution history parsing including completed and failed executions."""
        with (CURRENT_DIR / "fixtures" / "endpoints" / "history-executions.json").open(
            encoding="utf-8",
        ) as f:
            resp = MockResponse(f.read())

        with patch.object(aiohttp.ClientSession, "get", return_value=resp):
            history = await client.get_execution_history()
            assert len(history) == 2

            completed = history[0]
            assert isinstance(completed, HistoryExecution)
            assert completed.state.value == "COMPLETED"
            assert completed.failure_type == "NO_FAILURE"
            assert completed.commands[0].command == "close"
            assert completed.commands[0].device_url == "rts://2025-8464-6867/16756006"

            failed = history[1]
            assert failed.state.value == "FAILED"
            assert failed.failure_type == "CMDCANCELLED"
            assert failed.commands[0].command == "open"

    @pytest.mark.asyncio
    async def test_get_state(self, client: OverkizClient):
        """Verify device state retrieval and parsing."""
        with (CURRENT_DIR / "fixtures" / "endpoints" / "device-states.json").open(
            encoding="utf-8",
        ) as f:
            resp = MockResponse(f.read())

        with patch.object(aiohttp.ClientSession, "get", return_value=resp):
            states = await client.get_state("io://1234-5678-1234/12345678")
            assert len(states) == 3
            assert all(isinstance(s, State) for s in states)
            assert states[0].name == "core:StatusState"
            assert states[0].value == "available"
            assert states[1].name == "core:ClosureState"
            assert states[1].value == 0
            assert states[2].name == "core:OpenClosedState"
            assert states[2].value == "open"

    @pytest.mark.asyncio
    async def test_get_places(self, client: OverkizClient):
        """Verify hierarchical place structure is parsed recursively."""
        with (CURRENT_DIR / "fixtures" / "endpoints" / "setup-places.json").open(
            encoding="utf-8",
        ) as f:
            resp = MockResponse(f.read())

        with patch.object(aiohttp.ClientSession, "get", return_value=resp):
            places = await client.get_places()
            assert isinstance(places, Place)
            assert places.label == "My House"
            assert len(places.sub_places) == 2
            assert places.sub_places[0].label == "Living Room"
            assert places.sub_places[1].label == "Bedroom"
            assert places.sub_places[1].last_update_time is None

    @pytest.mark.asyncio
    async def test_execute_action_group_rts_close(self, client: OverkizClient):
        """Verify executing a close command on an RTS cover."""
        action = Action(
            device_url="rts://2025-8464-6867/16756006",
            commands=[Command(name="close", parameters=None, type=1)],
        )
        resp = MockResponse('{"execId": "ee7a5676-c68f-43a3-956d-6f5efc745954"}')

        with patch.object(aiohttp.ClientSession, "post") as mock_post:
            mock_post.return_value = resp
            exec_id = await client.execute_action_group([action])

            assert exec_id == "ee7a5676-c68f-43a3-956d-6f5efc745954"
            _, kwargs = mock_post.call_args
            sent_json = kwargs.get("json")
            assert (
                sent_json["actions"][0]["deviceURL"] == "rts://2025-8464-6867/16756006"
            )
            assert sent_json["actions"][0]["commands"][0]["name"] == "close"

    @pytest.mark.asyncio
    async def test_execute_action_group_multiple_rts_devices(
        self, client: OverkizClient
    ):
        """Verify executing commands on multiple RTS devices in a single action group."""
        actions = [
            Action(
                device_url="rts://2025-8464-6867/16756006",
                commands=[Command(name="close", parameters=None, type=1)],
            ),
            Action(
                device_url="rts://2025-8464-6867/16756007",
                commands=[Command(name="open", parameters=None, type=1)],
            ),
        ]
        resp = MockResponse('{"execId": "aaa-bbb-ccc"}')

        with patch.object(aiohttp.ClientSession, "post") as mock_post:
            mock_post.return_value = resp
            exec_id = await client.execute_action_group(actions)

            assert exec_id == "aaa-bbb-ccc"
            _, kwargs = mock_post.call_args
            sent_json = kwargs.get("json")
            assert len(sent_json["actions"]) == 2
            assert sent_json["actions"][0]["commands"][0]["name"] == "close"
            assert sent_json["actions"][1]["commands"][0]["name"] == "open"

    @pytest.mark.asyncio
    async def test_execute_persisted_action_group(self, client: OverkizClient):
        """Verify executing a persisted action group by OID."""
        resp = MockResponse('{"execId": "ee7a5676-c68f-43a3-956d-6f5efc745954"}')

        with patch.object(aiohttp.ClientSession, "post", return_value=resp):
            exec_id = await client.execute_persisted_action_group(
                "12345678-abcd-efgh-ijkl-123456789012"
            )
            assert exec_id == "ee7a5676-c68f-43a3-956d-6f5efc745954"

    @pytest.mark.asyncio
    async def test_schedule_persisted_action_group(self, client: OverkizClient):
        """Verify scheduling a persisted action group."""
        with (CURRENT_DIR / "fixtures" / "endpoints" / "exec-schedule.json").open(
            encoding="utf-8",
        ) as f:
            resp = MockResponse(f.read())

        with patch.object(aiohttp.ClientSession, "post", return_value=resp):
            trigger_id = await client.schedule_persisted_action_group(
                "12345678-abcd-efgh-ijkl-123456789012", 1767003511145
            )
            assert trigger_id == "abc12345-def6-7890-abcd-ef1234567890"

    @pytest.mark.asyncio
    async def test_cancel_execution(self, client: OverkizClient):
        """Verify cancel_execution sends DELETE and does not raise on 204."""
        resp = MockResponse("", status=204)

        with patch.object(aiohttp.ClientSession, "delete", return_value=resp):
            await client.cancel_execution("699dd967-0a19-0481-7a62-99b990a2feb8")

    @pytest.mark.asyncio
    async def test_register_event_listener(self, client: OverkizClient):
        """Verify event listener registration returns and stores the listener ID."""
        with (CURRENT_DIR / "fixtures" / "endpoints" / "events-register.json").open(
            encoding="utf-8",
        ) as f:
            resp = MockResponse(f.read())

        with patch.object(aiohttp.ClientSession, "post", return_value=resp):
            listener_id = await client.register_event_listener()
            assert listener_id == "a70f6d96-0a19-0483-72d9-ac5f6bd7da26"
            assert client.event_listener_id == listener_id

    @pytest.mark.asyncio
    async def test_refresh_states(self, client: OverkizClient):
        """Verify refresh_states sends POST and does not raise on 204."""
        resp = MockResponse("", status=204)

        with patch.object(aiohttp.ClientSession, "post", return_value=resp):
            await client.refresh_states()

    @pytest.mark.asyncio
    async def test_refresh_device_states(self, client: OverkizClient):
        """Verify refresh_device_states sends POST for a specific device."""
        resp = MockResponse("", status=204)

        with patch.object(aiohttp.ClientSession, "post", return_value=resp):
            await client.refresh_device_states("rts://2025-8464-6867/16756006")

    # --- Local API specific tests ---
    # The local gateway (KizOs) behaves differently from the cloud API
    # in several cases. These tests verify the client raises proper errors
    # instead of crashing when called via the local API.

    @pytest.mark.asyncio
    async def test_local_get_current_execution_empty_list(
        self, local_client: OverkizClient
    ):
        """Local gateway returns [] for non-existent exec_id (cloud returns {})."""
        resp = MockResponse("[]")

        with patch.object(aiohttp.ClientSession, "get", return_value=resp):
            result = await local_client.get_current_execution(
                "00000000-0000-0000-0000-000000000000"
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_local_get_state_no_such_device(self, local_client: OverkizClient):
        """Local gateway raises NoSuchDeviceError for unknown device URLs."""
        resp = MockResponse(
            '{"error":"No such device : \\"io://0000-0000-0000/12345678\\"","errorCode":"NO_SUCH_DEVICE"}',
            status=400,
        )

        with (
            patch.object(aiohttp.ClientSession, "get", return_value=resp),
            pytest.raises(exceptions.NoSuchDeviceError),
        ):
            await local_client.get_state("io://0000-0000-0000/12345678")

    @pytest.mark.asyncio
    async def test_local_get_device_definition_no_such_device(
        self, local_client: OverkizClient
    ):
        """Local gateway raises NoSuchDeviceError for unknown device definition lookups."""
        resp = MockResponse(
            '{"error":"No such device : \\"io://0000-0000-0000/12345678\\"","errorCode":"NO_SUCH_DEVICE"}',
            status=400,
        )

        with (
            patch.object(aiohttp.ClientSession, "get", return_value=resp),
            pytest.raises(exceptions.NoSuchDeviceError),
        ):
            await local_client.get_device_definition("io://0000-0000-0000/12345678")

    @pytest.mark.asyncio
    async def test_local_get_setup_option_unknown_object(
        self, local_client: OverkizClient
    ):
        """Local gateway raises UnknownObjectError for non-existent options (cloud returns {})."""
        resp = MockResponse(
            '{"error":"Unknown object.","errorCode":"UNSPECIFIED_ERROR"}',
            status=400,
        )

        with (
            patch.object(aiohttp.ClientSession, "get", return_value=resp),
            pytest.raises(exceptions.UnknownObjectError),
        ):
            await local_client.get_setup_option("nonExistentOption")

    @pytest.mark.asyncio
    async def test_local_refresh_device_states_unknown_object(
        self, local_client: OverkizClient
    ):
        """Local gateway raises UnknownObjectError for unknown device refresh."""
        resp = MockResponse(
            '{"error":"Unknown object.","errorCode":"UNSPECIFIED_ERROR"}',
            status=400,
        )

        with (
            patch.object(aiohttp.ClientSession, "post", return_value=resp),
            pytest.raises(exceptions.UnknownObjectError),
        ):
            await local_client.refresh_device_states("io://0000-0000-0000/12345678")

    @pytest.mark.asyncio
    async def test_local_get_reference_controllable_unknown_object(
        self, local_client: OverkizClient
    ):
        """Local gateway raises UnknownObjectError for unknown controllable names."""
        resp = MockResponse(
            '{"error":"Unknown object.","errorCode":"UNSPECIFIED_ERROR"}',
            status=400,
        )

        with (
            patch.object(aiohttp.ClientSession, "get", return_value=resp),
            pytest.raises(exceptions.UnknownObjectError),
        ):
            await local_client.get_reference_controllable("io:NonExistentControllable")

    @pytest.mark.asyncio
    async def test_local_cancel_execution_succeeds_on_unknown_id(
        self, local_client: OverkizClient
    ):
        """Local gateway returns 200 with [] for cancel on unknown exec_id (idempotent)."""
        resp = MockResponse("[]", status=200)

        with patch.object(aiohttp.ClientSession, "delete", return_value=resp):
            await local_client.cancel_execution("00000000-0000-0000-0000-000000000000")

    @pytest.mark.asyncio
    async def test_local_execute_action_group_rts_close(
        self, local_client: OverkizClient
    ):
        """Verify executing an RTS command via the local API."""
        action = Action(
            device_url="rts://2025-8464-6867/16756006",
            commands=[Command(name="close")],
        )
        resp = MockResponse('{"execId": "45e52d27-3c08-4fd5-87f2-03d650b67f4b"}')

        with patch.object(aiohttp.ClientSession, "post") as mock_post:
            mock_post.return_value = resp
            exec_id = await local_client.execute_action_group([action])

            assert exec_id == "45e52d27-3c08-4fd5-87f2-03d650b67f4b"

    @pytest.mark.asyncio
    async def test_local_no_registered_event_listener(
        self, local_client: OverkizClient
    ):
        """Local gateway raises NoRegisteredEventListenerError for unregistered fetch."""
        resp = MockResponse(
            '{"error":"\\"No registered event listener.\\"","errorCode":"UNSPECIFIED_ERROR"}',
            status=400,
        )

        with pytest.raises(exceptions.NoRegisteredEventListenerError):
            await check_response(resp)

    @pytest.mark.asyncio
    async def test_local_schedule_persisted_action_group_unknown_object(
        self, local_client: OverkizClient
    ):
        """Local gateway raises UnknownObjectError when scheduling a non-existent action group."""
        resp = MockResponse(
            '{"error":"Unknown object.","errorCode":"UNSPECIFIED_ERROR"}',
            status=400,
        )

        with (
            patch.object(aiohttp.ClientSession, "post", return_value=resp),
            pytest.raises(exceptions.UnknownObjectError),
        ):
            await local_client.schedule_persisted_action_group(
                "00000000-0000-0000-0000-000000000000", 9999999999
            )
