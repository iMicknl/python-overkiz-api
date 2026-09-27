"""Regression coverage for bounded authentication and listener recovery."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import aiohttp
import pytest

from pyoverkiz.client import OverkizClient
from pyoverkiz.exceptions import (
    BadCredentialsError,
    InvalidEventListenerIdError,
    NotAuthenticatedError,
)
from tests.helpers import MockResponse


@pytest.mark.asyncio
async def test_registration_reauthenticates_without_double_registration(
    client: OverkizClient,
) -> None:
    """Auth recovery must not create a listener that the retry immediately replaces."""
    with (
        patch("backoff._async.asyncio.sleep", new=AsyncMock()),
        patch.object(client._auth, "login", new=AsyncMock()) as login,
        patch.object(
            aiohttp.ClientSession,
            "post",
            side_effect=[
                NotAuthenticatedError("expired"),
                MockResponse('{"id": "replacement"}'),
            ],
        ) as post,
    ):
        assert await client.register_event_listener() == "replacement"

    assert login.await_count == 1
    assert post.call_count == 2
    assert client.event_listener_id == "replacement"
    await client.session.close()


@pytest.mark.asyncio
async def test_registration_auth_failure_is_bounded(client: OverkizClient) -> None:
    """Repeated rejection must exhaust the original auth budget without recursion."""
    with (
        patch("backoff._async.asyncio.sleep", new=AsyncMock()),
        patch.object(client._auth, "login", new=AsyncMock()) as login,
        patch.object(
            aiohttp.ClientSession, "post", side_effect=NotAuthenticatedError("expired")
        ) as post,
        pytest.raises(NotAuthenticatedError),
    ):
        await client.register_event_listener()

    assert login.await_count == 1
    assert post.call_count == 2
    await client.session.close()


@pytest.mark.asyncio
async def test_registration_transport_budget(client: OverkizClient) -> None:
    """Registration must use one transport retry budget at the HTTP boundary."""
    with (
        patch("backoff._async.asyncio.sleep", new=AsyncMock()),
        patch.object(
            aiohttp.ClientSession, "post", side_effect=TimeoutError("offline")
        ) as post,
        pytest.raises(TimeoutError),
    ):
        await client.register_event_listener()

    assert post.call_count == 3
    await client.session.close()


@pytest.mark.asyncio
async def test_login_retries_auth_transport_only(client: OverkizClient) -> None:
    """Authentication retries must finish before listener registration starts."""
    client._event_listener_id = "stale"
    with (
        patch("backoff._async.asyncio.sleep", new=AsyncMock()),
        patch.object(
            client._auth,
            "login",
            new=AsyncMock(side_effect=[TimeoutError("offline"), None]),
        ) as login,
        patch.object(
            aiohttp.ClientSession, "post", return_value=MockResponse('{"id": "new"}')
        ) as post,
    ):
        await client.login()

    assert login.await_count == 2
    assert post.call_count == 1
    assert client.event_listener_id == "new"
    await client.session.close()


@pytest.mark.asyncio
async def test_relogin_exhaustion_preserves_transport_error(
    client: OverkizClient,
) -> None:
    """A failed recovery must not retry the original request without authentication."""
    failure = TimeoutError("login offline")
    with (
        patch("backoff._async.asyncio.sleep", new=AsyncMock()),
        patch.object(
            client._auth, "login", new=AsyncMock(side_effect=failure)
        ) as login,
        patch.object(
            aiohttp.ClientSession, "get", side_effect=NotAuthenticatedError("expired")
        ) as get,
        pytest.raises(TimeoutError) as raised,
    ):
        await client.get_api_version()

    assert raised.value is failure
    assert login.await_count == 3
    assert get.call_count == 1
    await client.session.close()


@pytest.mark.asyncio
async def test_listener_outage_recovers_on_next_poll(client: OverkizClient) -> None:
    """An exhausted registration must stop fetching until a later poll recovers."""
    client._event_listener_id = "stale"
    failure = TimeoutError("registration offline")
    with (
        patch("backoff._async.asyncio.sleep", new=AsyncMock()),
        patch.object(
            aiohttp.ClientSession,
            "post",
            side_effect=[
                InvalidEventListenerIdError("stale"),
                failure,
                failure,
                failure,
                MockResponse('{"id": "new"}'),
                MockResponse("[]"),
            ],
        ) as post,
    ):
        with pytest.raises(TimeoutError) as raised:
            await client.fetch_events()
        assert raised.value is failure
        assert post.call_count == 4
        assert client.event_listener_id is None

        assert await client.fetch_events() == []

    paths = [call.args[0].split("enduserAPI/")[1] for call in post.call_args_list]
    assert paths == [
        "events/stale/fetch",
        "events/register",
        "events/register",
        "events/register",
        "events/register",
        "events/new/fetch",
    ]
    await client.session.close()


@pytest.mark.asyncio
async def test_fetch_reauthenticates_and_registers_once(client: OverkizClient) -> None:
    """Fetching after session expiry must use exactly one replacement listener."""
    client._event_listener_id = "stale"
    with (
        patch("backoff._async.asyncio.sleep", new=AsyncMock()),
        patch.object(client._auth, "login", new=AsyncMock()) as login,
        patch.object(
            aiohttp.ClientSession,
            "post",
            side_effect=[
                NotAuthenticatedError("expired"),
                MockResponse('{"id": "new"}'),
                MockResponse("[]"),
            ],
        ) as post,
    ):
        assert await client.fetch_events() == []

    assert login.await_count == 1
    paths = [call.args[0].split("enduserAPI/")[1] for call in post.call_args_list]
    assert paths == ["events/stale/fetch", "events/register", "events/new/fetch"]
    await client.session.close()


@pytest.mark.asyncio
async def test_fatal_login_error_is_not_retried(client: OverkizClient) -> None:
    """Bad credentials must escape auth recovery without transport retries."""
    with (
        patch("backoff._async.asyncio.sleep", new=AsyncMock()),
        patch.object(
            client._auth,
            "login",
            new=AsyncMock(side_effect=BadCredentialsError("invalid")),
        ) as login,
        patch.object(
            aiohttp.ClientSession, "get", side_effect=NotAuthenticatedError("expired")
        ) as get,
        pytest.raises(BadCredentialsError),
    ):
        await client.get_api_version()

    assert login.await_count == 1
    assert get.call_count == 1
    await client.session.close()


@pytest.mark.asyncio
async def test_local_login_validation_does_not_recurse(
    local_client: OverkizClient,
) -> None:
    """A rejected static local token cannot be repaired by recursively logging in."""
    with (
        patch("backoff._async.asyncio.sleep", new=AsyncMock()),
        patch.object(
            aiohttp.ClientSession, "get", side_effect=NotAuthenticatedError("invalid")
        ) as get,
        patch.object(
            aiohttp.ClientSession, "post", side_effect=NotAuthenticatedError("invalid")
        ) as post,
        pytest.raises(NotAuthenticatedError),
    ):
        await local_client.login(register_event_listener=False)

    assert get.call_count == 1
    assert post.call_count == 0
    await local_client.session.close()


@pytest.mark.asyncio
async def test_relogin_retries_real_auth_http_before_fetching(
    client: OverkizClient,
) -> None:
    """Exercise OAuth, listener registration, and fetch recovery without auth mocks."""
    client._event_listener_id = "stale"
    with (
        patch("backoff._async.asyncio.sleep", new=AsyncMock()),
        patch.object(
            aiohttp.ClientSession,
            "post",
            side_effect=[
                NotAuthenticatedError("expired"),
                TimeoutError("token endpoint offline"),
                MockResponse('{"access_token": "token", "expires_in": 3600}'),
                MockResponse('{"id": "new"}'),
                MockResponse("[]"),
            ],
        ) as post,
    ):
        assert await client.fetch_events() == []

    paths = [call.args[0] for call in post.call_args_list]
    assert paths[0].endswith("/events/stale/fetch")
    assert paths[1].endswith("/oauth/oauth/v2/token/jwt")
    assert paths[2] == paths[1]
    assert paths[3].endswith("/events/register")
    assert paths[4].endswith("/events/new/fetch")
    assert client.event_listener_id == "new"
    await client.session.close()


@pytest.mark.asyncio
async def test_login_does_not_repeat_auth_when_registration_times_out(
    client: OverkizClient,
) -> None:
    """A registration outage must not restart the already completed OAuth login."""
    with (
        patch("backoff._async.asyncio.sleep", new=AsyncMock()),
        patch.object(
            aiohttp.ClientSession,
            "post",
            side_effect=[
                MockResponse('{"access_token": "token", "expires_in": 3600}'),
                TimeoutError("offline"),
                TimeoutError("offline"),
                TimeoutError("offline"),
            ],
        ) as post,
        pytest.raises(TimeoutError),
    ):
        await client.login()

    paths = [call.args[0] for call in post.call_args_list]
    assert paths[0].endswith("/oauth/oauth/v2/token/jwt")
    assert all(path.endswith("/events/register") for path in paths[1:])
    assert post.call_count == 4
    assert client.event_listener_id is None
    await client.session.close()


@pytest.mark.asyncio
async def test_relogin_preserves_non_transient_client_errors(
    client: OverkizClient,
) -> None:
    """Invalid URLs must propagate rather than being mistaken for transient failures."""
    failure = aiohttp.InvalidURL("invalid endpoint")
    with (
        patch("backoff._async.asyncio.sleep", new=AsyncMock()),
        patch.object(
            aiohttp.ClientSession, "get", side_effect=NotAuthenticatedError("expired")
        ) as get,
        patch.object(aiohttp.ClientSession, "post", side_effect=failure) as post,
        pytest.raises(aiohttp.InvalidURL) as raised,
    ):
        await client.get_api_version()

    assert raised.value is failure
    assert get.call_count == 1
    assert post.call_count == 1
    await client.session.close()
