# tests/test_rts_injection.py
"""Tests for RTS command duration injection in execute_action_group."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from pyoverkiz.auth.credentials import UsernamePasswordCredentials
from pyoverkiz.client import OverkizClient, OverkizClientSettings
from pyoverkiz.enums import ProductType, Server
from pyoverkiz.models import (
    Action,
    Command,
    CommandDefinition,
    CommandDefinitions,
    Definition,
    Device,
    States,
)


def _rts_device(
    device_url: str = "rts://1234-5678-9012/1",
    commands: list[CommandDefinition] | None = None,
) -> Device:
    """Create a minimal RTS Device for testing."""
    if commands is None:
        commands = [
            CommandDefinition(command_name="close", nparams=1),
            CommandDefinition(command_name="open", nparams=1),
            CommandDefinition(command_name="identify", nparams=0),
        ]
    return Device(
        attributes=States(),
        available=True,
        enabled=True,
        label="RTS Blind",
        device_url=device_url,
        controllable_name="rts:blind",
        definition=Definition(
            commands=CommandDefinitions(commands),
            widget_name="SomeWidget",
            ui_class="RollerShutter",
        ),
        type=ProductType.ACTUATOR,
    )


def _io_device(device_url: str = "io://1234-5678-9012/2") -> Device:
    """Create a minimal IO device for testing."""
    return Device(
        attributes=States(),
        available=True,
        enabled=True,
        label="IO Blind",
        device_url=device_url,
        controllable_name="io:blind",
        definition=Definition(
            commands=CommandDefinitions(
                [CommandDefinition(command_name="close", nparams=1)]
            ),
            widget_name="SomeWidget",
            ui_class="RollerShutter",
        ),
        type=ProductType.ACTUATOR,
    )


@pytest_asyncio.fixture
async def client_with_rts() -> OverkizClient:
    """Client with RTS duration enabled."""
    return OverkizClient(
        server=Server.SOMFY_EUROPE,
        credentials=UsernamePasswordCredentials("user", "pass"),
        settings=OverkizClientSettings(rts_command_duration=0),
    )


@pytest_asyncio.fixture
async def client_without_rts() -> OverkizClient:
    """Client without RTS duration (default behavior)."""
    return OverkizClient(
        server=Server.SOMFY_EUROPE,
        credentials=UsernamePasswordCredentials("user", "pass"),
    )


@pytest.mark.asyncio
async def test_rts_device_gets_duration_appended(client_with_rts):
    """RTS device command with room for extra param gets duration appended."""
    client_with_rts.devices = [_rts_device()]

    action = Action(
        device_url="rts://1234-5678-9012/1",
        commands=[Command(name="close")],
    )

    with patch.object(
        client_with_rts, "_execute_action_group_direct", new_callable=AsyncMock
    ) as mock_exec:
        mock_exec.return_value = "exec-123"
        await client_with_rts.execute_action_group([action])

        called_actions = mock_exec.call_args[0][0]
        assert called_actions[0].commands[0].parameters == [0]


@pytest.mark.asyncio
async def test_rts_command_already_has_max_params_not_modified(client_with_rts):
    """RTS command that already has nparams parameters is not modified."""
    client_with_rts.devices = [_rts_device()]

    action = Action(
        device_url="rts://1234-5678-9012/1",
        commands=[Command(name="close", parameters=[50])],
    )

    with patch.object(
        client_with_rts, "_execute_action_group_direct", new_callable=AsyncMock
    ) as mock_exec:
        mock_exec.return_value = "exec-123"
        await client_with_rts.execute_action_group([action])

        called_actions = mock_exec.call_args[0][0]
        # nparams=1 and already has 1 param — should NOT add another
        assert called_actions[0].commands[0].parameters == [50]


@pytest.mark.asyncio
async def test_rts_command_with_zero_nparams_not_modified(client_with_rts):
    """RTS command with nparams=0 (e.g., identify) is not modified."""
    client_with_rts.devices = [_rts_device()]

    action = Action(
        device_url="rts://1234-5678-9012/1",
        commands=[Command(name="identify")],
    )

    with patch.object(
        client_with_rts, "_execute_action_group_direct", new_callable=AsyncMock
    ) as mock_exec:
        mock_exec.return_value = "exec-123"
        await client_with_rts.execute_action_group([action])

        called_actions = mock_exec.call_args[0][0]
        assert called_actions[0].commands[0].parameters is None


@pytest.mark.asyncio
async def test_io_device_not_modified(client_with_rts):
    """Non-RTS device commands are never modified, even with rts_command_duration set."""
    client_with_rts.devices = [_io_device()]

    action = Action(
        device_url="io://1234-5678-9012/2",
        commands=[Command(name="close")],
    )

    with patch.object(
        client_with_rts, "_execute_action_group_direct", new_callable=AsyncMock
    ) as mock_exec:
        mock_exec.return_value = "exec-123"
        await client_with_rts.execute_action_group([action])

        called_actions = mock_exec.call_args[0][0]
        assert called_actions[0].commands[0].parameters is None


@pytest.mark.asyncio
async def test_no_rts_setting_means_no_injection(client_without_rts):
    """When rts_command_duration is None, no injection happens for any device."""
    client_without_rts.devices = [_rts_device()]

    action = Action(
        device_url="rts://1234-5678-9012/1",
        commands=[Command(name="close")],
    )

    with patch.object(
        client_without_rts, "_execute_action_group_direct", new_callable=AsyncMock
    ) as mock_exec:
        mock_exec.return_value = "exec-123"
        await client_without_rts.execute_action_group([action])

        called_actions = mock_exec.call_args[0][0]
        assert called_actions[0].commands[0].parameters is None


@pytest.mark.asyncio
async def test_rts_device_not_in_devices_list_skipped(client_with_rts):
    """If device URL is not in client.devices, skip injection (no crash)."""
    client_with_rts.devices = []  # No devices loaded

    action = Action(
        device_url="rts://1234-5678-9012/1",
        commands=[Command(name="close")],
    )

    with patch.object(
        client_with_rts, "_execute_action_group_direct", new_callable=AsyncMock
    ) as mock_exec:
        mock_exec.return_value = "exec-123"
        await client_with_rts.execute_action_group([action])

        called_actions = mock_exec.call_args[0][0]
        # Not modified — device not found, so we can't know nparams
        assert called_actions[0].commands[0].parameters is None


@pytest.mark.asyncio
async def test_rts_device_without_command_definitions_skipped(client_with_rts):
    """RTS device without command definitions doesn't crash, just skips injection."""
    device = Device(
        attributes=States(),
        available=True,
        enabled=True,
        label="RTS No Def",
        device_url="rts://1234-5678-9012/1",
        controllable_name="rts:blind",
        definition=Definition(widget_name="SomeWidget", ui_class="RollerShutter"),
        type=ProductType.ACTUATOR,
    )
    client_with_rts.devices = [device]

    action = Action(
        device_url="rts://1234-5678-9012/1",
        commands=[Command(name="close")],
    )

    with patch.object(
        client_with_rts, "_execute_action_group_direct", new_callable=AsyncMock
    ) as mock_exec:
        mock_exec.return_value = "exec-123"
        await client_with_rts.execute_action_group([action])

        called_actions = mock_exec.call_args[0][0]
        assert called_actions[0].commands[0].parameters is None


@pytest.mark.asyncio
async def test_original_action_not_mutated(client_with_rts):
    """Injection creates new Command objects; original actions are not mutated."""
    client_with_rts.devices = [_rts_device()]

    original_cmd = Command(name="close")
    action = Action(
        device_url="rts://1234-5678-9012/1",
        commands=[original_cmd],
    )

    with patch.object(
        client_with_rts, "_execute_action_group_direct", new_callable=AsyncMock
    ) as mock_exec:
        mock_exec.return_value = "exec-123"
        await client_with_rts.execute_action_group([action])

    # Original command should NOT have been mutated
    assert original_cmd.parameters is None
