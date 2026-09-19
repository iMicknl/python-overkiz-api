"""Adversarial stress tests for transport and authentication fault resilience (Milestone M5)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from pyoverkiz import exceptions
from pyoverkiz.client import OverkizClient, refresh_listener, relogin
from tests.helpers import MockResponse

CURRENT_DIR = Path(__file__).resolve().parent


class TestAdversarialTransportAndAuthFaultResilience:
    """Adversarial suite for transport and auth failure injection in python-overkiz-api."""

    # =========================================================================
    # Scenario 1: Prolonged Network Disconnects & Multi-Fault Reconnection
    # =========================================================================

    @pytest.mark.asyncio
    async def test_prolonged_network_disconnect_consecutive_timeouts(
        self, client: OverkizClient
    ) -> None:
        """Simulate prolonged network disconnect with multiple consecutive connection timeouts.

        Verify exponential backoff retries 3 times, raises TimeoutError, and does not corrupt client state.
        """
        with (
            patch("backoff._async.asyncio.sleep", new=AsyncMock()) as sleep_mock,
            patch.object(
                aiohttp.ClientSession,
                "get",
                side_effect=[
                    TimeoutError("Socket connect timeout (attempt 1)"),
                    TimeoutError("Socket connect timeout (attempt 2)"),
                    TimeoutError("Socket connect timeout (attempt 3)"),
                ],
            ) as get_mock,
            pytest.raises(TimeoutError),
        ):
            await client.get_api_version()

        assert get_mock.call_count == 3
        assert sleep_mock.await_count == 2

    @pytest.mark.asyncio
    async def test_network_disconnect_followed_by_recovery(
        self, client: OverkizClient
    ) -> None:
        """Simulate 2 consecutive network failures (ClientConnectorError, TimeoutError) followed by recovery."""
        resp = MockResponse(json.dumps({"protocolVersion": "2"}))

        with (
            patch("backoff._async.asyncio.sleep", new=AsyncMock()) as sleep_mock,
            patch.object(
                aiohttp.ClientSession,
                "get",
                side_effect=[
                    aiohttp.ClientConnectorError(
                        MagicMock(), OSError("Host unreachable")
                    ),
                    TimeoutError("Gateway timeout"),
                    resp,
                ],
            ) as get_mock,
        ):
            version = await client.get_api_version()

        assert version == "2"
        assert get_mock.call_count == 3
        assert sleep_mock.await_count == 2

    # =========================================================================
    # Scenario 2: Session Expiration During Network Outage & Relogin
    # =========================================================================

    @pytest.mark.asyncio
    async def test_session_expiration_on_first_reconnect_triggers_relogin(
        self, client: OverkizClient
    ) -> None:
        """When connectivity is restored, first request hits 401 NotAuthenticatedError.

        Verify client catches 401, resets listener ID, executes relogin, and retries request successfully.
        """
        client._event_listener_id = "stale-listener-999"
        client.login = AsyncMock()

        with (
            patch("backoff._async.asyncio.sleep", new=AsyncMock()) as sleep_mock,
            patch.object(
                OverkizClient,
                "_get",
                side_effect=[
                    exceptions.NotAuthenticatedError("Session expired during outage"),
                    {"protocolVersion": "1"},
                ],
            ) as get_mock,
        ):
            version = await client.get_api_version()

        assert version == "1"
        assert get_mock.await_count == 2
        assert client.login.await_count == 1
        assert sleep_mock.await_count == 1
        assert client._event_listener_id is None

    @pytest.mark.asyncio
    async def test_relogin_during_transient_network_outage_does_not_crash(
        self, client: OverkizClient
    ) -> None:
        """During relogin callback, if network is still flaky, relogin handler catches ClientError/TimeoutError safely."""
        client._event_listener_id = "listener-before-relogin"
        client.login = AsyncMock(
            side_effect=aiohttp.ClientConnectorError(
                MagicMock(), OSError("DNS resolution failure")
            )
        )

        invocation = {"args": (client,)}
        # Must execute without throwing unhandled exception
        await relogin(invocation)

        assert client._event_listener_id is None
        assert client.login.await_count == 1

    @pytest.mark.asyncio
    async def test_refresh_listener_during_transient_network_outage_does_not_crash(
        self, client: OverkizClient
    ) -> None:
        """During refresh_listener callback, if network drops, refresh_listener handler catches OSError/TimeoutError safely."""
        client._event_listener_id = "listener-before-refresh"
        client.register_event_listener = AsyncMock(
            side_effect=TimeoutError("Timeout contacting /events/register")
        )

        invocation = {"args": (client,)}
        await refresh_listener(invocation)

        assert client._event_listener_id is None
        assert client.register_event_listener.await_count == 1

    # =========================================================================
    # Scenario 3: Fatal Auth Failure (BadCredentialsError)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_fatal_bad_credentials_not_retried_as_transient_auth(
        self, client: OverkizClient
    ) -> None:
        """Verify BadCredentialsError is fatal and NOT caught by retry_on_auth_error."""
        client.login = AsyncMock()

        with (
            patch("backoff._async.asyncio.sleep", new=AsyncMock()) as sleep_mock,
            patch.object(
                aiohttp.ClientSession,
                "get",
                side_effect=exceptions.BadCredentialsError(
                    "Invalid username or password"
                ),
            ),
            pytest.raises(exceptions.BadCredentialsError),
        ):
            await client.get_api_version()

        # Should fail immediately without calling login() or backoff sleep
        assert client.login.await_count == 0
        assert sleep_mock.await_count == 0

    # =========================================================================
    # Scenario 4: Server Maintenance / 503 / 502 Responses
    # =========================================================================

    @pytest.mark.parametrize(
        ("fixture_file", "expected_exception"),
        [
            ("exceptions/cloud/503-maintenance.html", exceptions.MaintenanceError),
            ("exceptions/cloud/503-empty.html", exceptions.ServiceUnavailableError),
            (
                "exceptions/cloud/502-bad-gateway.html",
                exceptions.ServiceUnavailableError,
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_server_outage_and_maintenance_handling(
        self,
        client: OverkizClient,
        fixture_file: str,
        expected_exception: type[Exception],
    ) -> None:
        """Verify server maintenance and 502/503 gateway outages raise structured domain exceptions."""
        with (CURRENT_DIR / "fixtures" / fixture_file).open(encoding="utf-8") as f:
            resp = MockResponse(f.read(), status=503 if "503" in fixture_file else 502)

        with (
            patch.object(aiohttp.ClientSession, "get", return_value=resp),
            pytest.raises(expected_exception),
        ):
            await client.get_api_version()

    # =========================================================================
    # Scenario 5: Multi-Stage Cascading Fault Resilience
    # =========================================================================

    @pytest.mark.asyncio
    async def test_register_event_listener_cascading_fault_recovery(
        self, client: OverkizClient
    ) -> None:
        """Stress-test register_event_listener recovering through cascading faults.

        1. 401 NotAuthenticatedError -> triggers relogin()
        2. ClientConnectorError -> retries connection
        3. Event listener successfully registered.
        """
        client.login = AsyncMock()

        with (
            patch("backoff._async.asyncio.sleep", new=AsyncMock()) as sleep_mock,
            patch.object(
                OverkizClient,
                "_post",
                side_effect=[
                    exceptions.NotAuthenticatedError("Session expired"),
                    aiohttp.ClientConnectorError(
                        MagicMock(), OSError("Connection reset")
                    ),
                    {"id": "listener-resilience-ok"},
                ],
            ) as post_mock,
        ):
            listener_id = await client.register_event_listener()

        assert listener_id == "listener-resilience-ok"
        assert client._event_listener_id == "listener-resilience-ok"
        assert client.login.await_count == 1
        assert post_mock.await_count == 3
        assert sleep_mock.await_count == 2
