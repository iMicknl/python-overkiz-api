# tests/test_rts_injection.py
"""Tests for RTS command duration injection in execute_action_group.

This feature replaces the old COMMANDS_WITHOUT_DELAY blocklist approach that
was used in the Home Assistant overkiz executor. The old approach blindly
appended 0 to all RTS commands except a hardcoded list (identify, off, on,
onWithTimer, test, tiltPositive, tiltNegative). The new approach uses the
device's command definition nparams to decide whether a duration parameter
can be added — this is more correct and future-proof.
"""

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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _rts_device(
    device_url: str = "rts://1234-5678-9012/1",
    commands: list[CommandDefinition] | None = None,
) -> Device:
    """Create a minimal RTS Device for testing."""
    if commands is None:
        # Realistic nparams values based on actual Overkiz API fixtures
        commands = [
            CommandDefinition(command_name="close", nparams=1),
            CommandDefinition(command_name="open", nparams=1),
            CommandDefinition(command_name="up", nparams=1),
            CommandDefinition(command_name="down", nparams=1),
            CommandDefinition(command_name="stop", nparams=1),
            CommandDefinition(command_name="my", nparams=1),
            CommandDefinition(command_name="rest", nparams=1),
            CommandDefinition(command_name="identify", nparams=0),
            CommandDefinition(command_name="test", nparams=0),
            CommandDefinition(command_name="tiltPositive", nparams=2),
            CommandDefinition(command_name="tiltNegative", nparams=2),
            CommandDefinition(command_name="moveOf", nparams=2),
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


def _zwave_device(device_url: str = "zwave://1234-5678-9012/3") -> Device:
    """Create a minimal Z-Wave device for testing."""
    return Device(
        attributes=States(),
        available=True,
        enabled=True,
        label="ZWave Blind",
        device_url=device_url,
        controllable_name="zwave:blind",
        definition=Definition(
            commands=CommandDefinitions(
                [CommandDefinition(command_name="close", nparams=1)]
            ),
            widget_name="SomeWidget",
            ui_class="RollerShutter",
        ),
        type=ProductType.ACTUATOR,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client_rts_0() -> OverkizClient:
    """Client with RTS duration=0 (most common HA config)."""
    return OverkizClient(
        server=Server.SOMFY_EUROPE,
        credentials=UsernamePasswordCredentials("user", "pass"),
        settings=OverkizClientSettings(rts_command_duration=0),
    )


@pytest_asyncio.fixture
async def client_rts_5() -> OverkizClient:
    """Client with RTS duration=5 (custom delay)."""
    return OverkizClient(
        server=Server.SOMFY_EUROPE,
        credentials=UsernamePasswordCredentials("user", "pass"),
        settings=OverkizClientSettings(rts_command_duration=5),
    )


@pytest_asyncio.fixture
async def client_no_rts() -> OverkizClient:
    """Client without RTS duration (default/passive)."""
    return OverkizClient(
        server=Server.SOMFY_EUROPE,
        credentials=UsernamePasswordCredentials("user", "pass"),
    )


# ---------------------------------------------------------------------------
# Basic injection tests
# ---------------------------------------------------------------------------


class TestBasicInjection:
    """Core tests: commands that accept a duration get it injected."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "command_name",
        ["close", "open", "up", "down", "stop", "my"],
    )
    async def test_movement_commands_get_duration_injected(
        self, client_rts_0, command_name
    ):
        """Movement commands (nparams=1, no params yet) get duration appended."""
        client_rts_0.devices = [_rts_device()]

        action = Action(
            device_url="rts://1234-5678-9012/1",
            commands=[Command(name=command_name)],
        )

        with patch.object(
            client_rts_0, "_execute_action_group_direct", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "exec-123"
            await client_rts_0.execute_action_group([action])

            called_actions = mock_exec.call_args[0][0]
            assert called_actions[0].commands[0].parameters == [0], (
                f"Command '{command_name}' should have gotten duration=0 appended"
            )

    @pytest.mark.asyncio
    async def test_custom_duration_value_injected(self, client_rts_5):
        """A non-zero duration is injected correctly."""
        client_rts_5.devices = [_rts_device()]

        action = Action(
            device_url="rts://1234-5678-9012/1",
            commands=[Command(name="close")],
        )

        with patch.object(
            client_rts_5, "_execute_action_group_direct", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "exec-123"
            await client_rts_5.execute_action_group([action])

            called_actions = mock_exec.call_args[0][0]
            assert called_actions[0].commands[0].parameters == [5]


# ---------------------------------------------------------------------------
# Commands that should NOT get injection (old COMMANDS_WITHOUT_DELAY list)
# ---------------------------------------------------------------------------


class TestCommandsNotInjected:
    """Commands that must NOT receive duration injection."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "command_name",
        ["identify", "test"],
    )
    async def test_zero_nparams_commands_not_injected(self, client_rts_0, command_name):
        """Commands with nparams=0 do not get any duration appended."""
        client_rts_0.devices = [_rts_device()]

        action = Action(
            device_url="rts://1234-5678-9012/1",
            commands=[Command(name=command_name)],
        )

        with patch.object(
            client_rts_0, "_execute_action_group_direct", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "exec-123"
            await client_rts_0.execute_action_group([action])

            called_actions = mock_exec.call_args[0][0]
            assert called_actions[0].commands[0].parameters is None, (
                f"Command '{command_name}' (nparams=0) should NOT get duration"
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "command_name",
        ["tiltPositive", "tiltNegative", "moveOf"],
    )
    async def test_multi_nparams_commands_not_injected(
        self, client_rts_0, command_name
    ):
        """Commands with nparams=2 (tilt, moveOf) have domain-specific params, not duration."""
        client_rts_0.devices = [_rts_device()]

        action = Action(
            device_url="rts://1234-5678-9012/1",
            commands=[Command(name=command_name)],
        )

        with patch.object(
            client_rts_0, "_execute_action_group_direct", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "exec-123"
            await client_rts_0.execute_action_group([action])

            called_actions = mock_exec.call_args[0][0]
            assert called_actions[0].commands[0].parameters is None, (
                f"Command '{command_name}' (nparams=2) should NOT get duration"
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("command_name", "params"),
        [
            ("tiltPositive", [1]),
            ("tiltNegative", [15]),
            ("moveOf", [50]),
        ],
    )
    async def test_multi_nparams_commands_with_partial_params_not_injected(
        self, client_rts_0, command_name, params
    ):
        """Commands with nparams=2 and 1 param filled still don't get injection."""
        client_rts_0.devices = [_rts_device()]

        action = Action(
            device_url="rts://1234-5678-9012/1",
            commands=[Command(name=command_name, parameters=params)],
        )

        with patch.object(
            client_rts_0, "_execute_action_group_direct", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "exec-123"
            await client_rts_0.execute_action_group([action])

            called_actions = mock_exec.call_args[0][0]
            assert called_actions[0].commands[0].parameters == params, (
                f"Command '{command_name}' (nparams=2) should NOT get duration injected"
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("command_name", "params"),
        [
            ("tiltPositive", [1, 0]),
            ("tiltNegative", [15, 1]),
            ("moveOf", [50, 100]),
        ],
    )
    async def test_multi_nparams_commands_fully_filled_not_injected(
        self, client_rts_0, command_name, params
    ):
        """Commands with nparams=2 and all params filled pass through unchanged."""
        client_rts_0.devices = [_rts_device()]

        action = Action(
            device_url="rts://1234-5678-9012/1",
            commands=[Command(name=command_name, parameters=params)],
        )

        with patch.object(
            client_rts_0, "_execute_action_group_direct", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "exec-123"
            await client_rts_0.execute_action_group([action])

            called_actions = mock_exec.call_args[0][0]
            assert called_actions[0].commands[0].parameters == params


# ---------------------------------------------------------------------------
# Non-RTS protocols should never be modified
# ---------------------------------------------------------------------------


class TestNonRtsProtocols:
    """Non-RTS devices are never touched regardless of rts_command_duration."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("device_factory", "device_url"),
        [
            (_io_device, "io://1234-5678-9012/2"),
            (_zwave_device, "zwave://1234-5678-9012/3"),
        ],
        ids=["io", "zwave"],
    )
    async def test_non_rts_device_not_modified(
        self, client_rts_0, device_factory, device_url
    ):
        """IO and Z-Wave commands are never modified even with rts_command_duration set."""
        client_rts_0.devices = [device_factory()]

        action = Action(
            device_url=device_url,
            commands=[Command(name="close")],
        )

        with patch.object(
            client_rts_0, "_execute_action_group_direct", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "exec-123"
            await client_rts_0.execute_action_group([action])

            called_actions = mock_exec.call_args[0][0]
            assert called_actions[0].commands[0].parameters is None


# ---------------------------------------------------------------------------
# Setting disabled (rts_command_duration=None)
# ---------------------------------------------------------------------------


class TestSettingDisabled:
    """When rts_command_duration is None (default), no injection occurs."""

    @pytest.mark.asyncio
    async def test_no_setting_means_no_injection(self, client_no_rts):
        """RTS device commands pass through unmodified when setting is None."""
        client_no_rts.devices = [_rts_device()]

        action = Action(
            device_url="rts://1234-5678-9012/1",
            commands=[Command(name="close")],
        )

        with patch.object(
            client_no_rts, "_execute_action_group_direct", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "exec-123"
            await client_no_rts.execute_action_group([action])

            called_actions = mock_exec.call_args[0][0]
            assert called_actions[0].commands[0].parameters is None

    @pytest.mark.asyncio
    async def test_no_setting_multiple_rts_commands_unmodified(self, client_no_rts):
        """Multiple RTS commands all pass through when setting is None."""
        client_no_rts.devices = [_rts_device()]

        action = Action(
            device_url="rts://1234-5678-9012/1",
            commands=[
                Command(name="close"),
                Command(name="open"),
                Command(name="my"),
            ],
        )

        with patch.object(
            client_no_rts, "_execute_action_group_direct", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "exec-123"
            await client_no_rts.execute_action_group([action])

            called_actions = mock_exec.call_args[0][0]
            for cmd in called_actions[0].commands:
                assert cmd.parameters is None


# ---------------------------------------------------------------------------
# Parameter capacity tests
# ---------------------------------------------------------------------------


class TestParameterCapacity:
    """Tests verifying injection only for nparams=1 commands with 0 params."""

    @pytest.mark.asyncio
    async def test_nparams_1_already_has_param_not_modified(self, client_rts_0):
        """Command with nparams=1 that already has its parameter is not modified."""
        client_rts_0.devices = [_rts_device()]

        action = Action(
            device_url="rts://1234-5678-9012/1",
            commands=[Command(name="close", parameters=[50])],
        )

        with patch.object(
            client_rts_0, "_execute_action_group_direct", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "exec-123"
            await client_rts_0.execute_action_group([action])

            called_actions = mock_exec.call_args[0][0]
            assert called_actions[0].commands[0].parameters == [50]

    @pytest.mark.asyncio
    async def test_nparams_1_with_extra_params_not_modified(self, client_rts_0):
        """Command that somehow has MORE params than nparams is not modified (defensive)."""
        device = _rts_device(
            commands=[CommandDefinition(command_name="close", nparams=1)]
        )
        client_rts_0.devices = [device]

        action = Action(
            device_url="rts://1234-5678-9012/1",
            commands=[Command(name="close", parameters=[10, 20])],
        )

        with patch.object(
            client_rts_0, "_execute_action_group_direct", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "exec-123"
            await client_rts_0.execute_action_group([action])

            called_actions = mock_exec.call_args[0][0]
            assert called_actions[0].commands[0].parameters == [10, 20]

    @pytest.mark.asyncio
    async def test_empty_parameters_list_counts_as_zero(self, client_rts_0):
        """Explicit empty list [] counts as 0 params — duration gets appended."""
        client_rts_0.devices = [_rts_device()]

        action = Action(
            device_url="rts://1234-5678-9012/1",
            commands=[Command(name="close", parameters=[])],
        )

        with patch.object(
            client_rts_0, "_execute_action_group_direct", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "exec-123"
            await client_rts_0.execute_action_group([action])

            called_actions = mock_exec.call_args[0][0]
            assert called_actions[0].commands[0].parameters == [0]

    @pytest.mark.asyncio
    async def test_nparams_2_never_gets_injection(self, client_rts_0):
        """Commands with nparams >= 2 never get injection regardless of param count."""
        device = _rts_device(
            commands=[CommandDefinition(command_name="setClosure", nparams=3)]
        )
        client_rts_0.devices = [device]

        for params in [None, [], [50], [50, 100]]:
            action = Action(
                device_url="rts://1234-5678-9012/1",
                commands=[Command(name="setClosure", parameters=params)],
            )

            with patch.object(
                client_rts_0, "_execute_action_group_direct", new_callable=AsyncMock
            ) as mock_exec:
                mock_exec.return_value = "exec-123"
                await client_rts_0.execute_action_group([action])

                called_actions = mock_exec.call_args[0][0]
                assert called_actions[0].commands[0].parameters == params, (
                    f"nparams=3 with params={params} should NOT be modified"
                )


# ---------------------------------------------------------------------------
# Multi-command and multi-action tests
# ---------------------------------------------------------------------------


class TestMultiCommandActions:
    """Tests for actions with multiple commands."""

    @pytest.mark.asyncio
    async def test_mixed_commands_in_single_action(self, client_rts_0):
        """Action with injectable and non-injectable commands handles each correctly."""
        client_rts_0.devices = [_rts_device()]

        action = Action(
            device_url="rts://1234-5678-9012/1",
            commands=[
                Command(name="close"),  # nparams=1, no params -> inject
                Command(name="identify"),  # nparams=0 -> skip
                Command(name="open", parameters=[50]),  # nparams=1, full -> skip
                Command(name="up"),  # nparams=1, no params -> inject
            ],
        )

        with patch.object(
            client_rts_0, "_execute_action_group_direct", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "exec-123"
            await client_rts_0.execute_action_group([action])

            cmds = mock_exec.call_args[0][0][0].commands
            assert cmds[0].parameters == [0]  # close: injected
            assert cmds[1].parameters is None  # identify: skipped
            assert cmds[2].parameters == [50]  # open: already full
            assert cmds[3].parameters == [0]  # up: injected

    @pytest.mark.asyncio
    async def test_multiple_actions_mixed_protocols(self, client_rts_0):
        """Multiple actions in one call: RTS gets injection, IO does not."""
        rts = _rts_device()
        io = _io_device()
        client_rts_0.devices = [rts, io]

        actions = [
            Action(
                device_url="rts://1234-5678-9012/1",
                commands=[Command(name="close")],
            ),
            Action(
                device_url="io://1234-5678-9012/2",
                commands=[Command(name="close")],
            ),
        ]

        with patch.object(
            client_rts_0, "_execute_action_group_direct", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "exec-123"
            await client_rts_0.execute_action_group(actions)

            called_actions = mock_exec.call_args[0][0]
            assert called_actions[0].commands[0].parameters == [0]  # RTS
            assert called_actions[1].commands[0].parameters is None  # IO

    @pytest.mark.asyncio
    async def test_multiple_rts_actions(self, client_rts_0):
        """Multiple RTS actions all get duration injected independently."""
        rts1 = _rts_device(device_url="rts://1234-5678-9012/1")
        rts2 = _rts_device(device_url="rts://1234-5678-9012/4")
        client_rts_0.devices = [rts1, rts2]

        actions = [
            Action(
                device_url="rts://1234-5678-9012/1",
                commands=[Command(name="close")],
            ),
            Action(
                device_url="rts://1234-5678-9012/4",
                commands=[Command(name="open")],
            ),
        ]

        with patch.object(
            client_rts_0, "_execute_action_group_direct", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "exec-123"
            await client_rts_0.execute_action_group(actions)

            called_actions = mock_exec.call_args[0][0]
            assert called_actions[0].commands[0].parameters == [0]
            assert called_actions[1].commands[0].parameters == [0]


# ---------------------------------------------------------------------------
# Device URL edge cases (subsystem IDs)
# ---------------------------------------------------------------------------


class TestDeviceUrlEdgeCases:
    """RTS devices with subsystem IDs (e.g., rts://gateway/addr#2)."""

    @pytest.mark.asyncio
    async def test_rts_device_with_subsystem_id(self, client_rts_0):
        """RTS device with subsystem ID (#2) gets injection."""
        device = _rts_device(device_url="rts://1234-5678-9012/1#2")
        client_rts_0.devices = [device]

        action = Action(
            device_url="rts://1234-5678-9012/1#2",
            commands=[Command(name="close")],
        )

        with patch.object(
            client_rts_0, "_execute_action_group_direct", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "exec-123"
            await client_rts_0.execute_action_group([action])

            called_actions = mock_exec.call_args[0][0]
            assert called_actions[0].commands[0].parameters == [0]

    @pytest.mark.asyncio
    async def test_mismatched_subsystem_id_not_found(self, client_rts_0):
        """Action URL rts://...#2 but devices only has rts://...#1 => not found, skip."""
        device = _rts_device(device_url="rts://1234-5678-9012/1#1")
        client_rts_0.devices = [device]

        action = Action(
            device_url="rts://1234-5678-9012/1#2",
            commands=[Command(name="close")],
        )

        with patch.object(
            client_rts_0, "_execute_action_group_direct", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "exec-123"
            await client_rts_0.execute_action_group([action])

            called_actions = mock_exec.call_args[0][0]
            assert called_actions[0].commands[0].parameters is None


# ---------------------------------------------------------------------------
# Graceful degradation / robustness
# ---------------------------------------------------------------------------


class TestRobustness:
    """Edge cases and error scenarios that must not crash."""

    @pytest.mark.asyncio
    async def test_device_not_in_devices_list(self, client_rts_0):
        """Action for unknown device URL passes through without crashing."""
        client_rts_0.devices = []

        action = Action(
            device_url="rts://1234-5678-9012/1",
            commands=[Command(name="close")],
        )

        with patch.object(
            client_rts_0, "_execute_action_group_direct", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "exec-123"
            await client_rts_0.execute_action_group([action])

            called_actions = mock_exec.call_args[0][0]
            assert called_actions[0].commands[0].parameters is None

    @pytest.mark.asyncio
    async def test_command_not_in_definitions(self, client_rts_0):
        """RTS device exists but command not in its definitions — skip injection."""
        device = _rts_device(
            commands=[CommandDefinition(command_name="close", nparams=1)]
        )
        client_rts_0.devices = [device]

        action = Action(
            device_url="rts://1234-5678-9012/1",
            commands=[Command(name="unknownCommand")],
        )

        with patch.object(
            client_rts_0, "_execute_action_group_direct", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "exec-123"
            await client_rts_0.execute_action_group([action])

            called_actions = mock_exec.call_args[0][0]
            assert called_actions[0].commands[0].parameters is None

    @pytest.mark.asyncio
    async def test_empty_command_definitions(self, client_rts_0):
        """RTS device with no command definitions at all — skip gracefully."""
        device = Device(
            attributes=States(),
            available=True,
            enabled=True,
            label="RTS No Defs",
            device_url="rts://1234-5678-9012/1",
            controllable_name="rts:blind",
            definition=Definition(widget_name="SomeWidget", ui_class="RollerShutter"),
            type=ProductType.ACTUATOR,
        )
        client_rts_0.devices = [device]

        action = Action(
            device_url="rts://1234-5678-9012/1",
            commands=[Command(name="close")],
        )

        with patch.object(
            client_rts_0, "_execute_action_group_direct", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "exec-123"
            await client_rts_0.execute_action_group([action])

            called_actions = mock_exec.call_args[0][0]
            assert called_actions[0].commands[0].parameters is None

    @pytest.mark.asyncio
    async def test_empty_actions_list(self, client_rts_0):
        """Empty actions list does not crash."""
        client_rts_0.devices = [_rts_device()]

        with patch.object(
            client_rts_0, "_execute_action_group_direct", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "exec-123"
            await client_rts_0.execute_action_group([])

            called_actions = mock_exec.call_args[0][0]
            assert called_actions == []

    @pytest.mark.asyncio
    async def test_action_with_empty_commands_list(self, client_rts_0):
        """Action with no commands passes through without crash."""
        client_rts_0.devices = [_rts_device()]

        action = Action(
            device_url="rts://1234-5678-9012/1",
            commands=[],
        )

        with patch.object(
            client_rts_0, "_execute_action_group_direct", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "exec-123"
            await client_rts_0.execute_action_group([action])

            called_actions = mock_exec.call_args[0][0]
            assert called_actions[0].commands == []


# ---------------------------------------------------------------------------
# Immutability / side-effect tests
# ---------------------------------------------------------------------------


class TestImmutability:
    """Verify that injection does not mutate original objects."""

    @pytest.mark.asyncio
    async def test_original_command_not_mutated(self, client_rts_0):
        """Injection creates new Command; original Command is untouched."""
        client_rts_0.devices = [_rts_device()]

        original_cmd = Command(name="close")
        action = Action(
            device_url="rts://1234-5678-9012/1",
            commands=[original_cmd],
        )

        with patch.object(
            client_rts_0, "_execute_action_group_direct", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "exec-123"
            await client_rts_0.execute_action_group([action])

        assert original_cmd.parameters is None

    @pytest.mark.asyncio
    async def test_original_action_not_mutated(self, client_rts_0):
        """Original action list is not modified in place."""
        client_rts_0.devices = [_rts_device()]

        cmd = Command(name="close")
        action = Action(
            device_url="rts://1234-5678-9012/1",
            commands=[cmd],
        )
        original_actions = [action]

        with patch.object(
            client_rts_0, "_execute_action_group_direct", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "exec-123"
            await client_rts_0.execute_action_group(original_actions)

        assert original_actions[0].commands[0].parameters is None

    @pytest.mark.asyncio
    async def test_original_parameters_list_not_mutated(self, client_rts_0):
        """If command had existing empty params list, original list is not modified."""
        client_rts_0.devices = [_rts_device()]

        original_params: list[int] = []
        cmd = Command(name="close", parameters=original_params)
        action = Action(
            device_url="rts://1234-5678-9012/1",
            commands=[cmd],
        )

        with patch.object(
            client_rts_0, "_execute_action_group_direct", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "exec-123"
            await client_rts_0.execute_action_group([action])

            called_actions = mock_exec.call_args[0][0]
            assert called_actions[0].commands[0].parameters == [0]

        # Original list must still be empty
        assert original_params == []
        assert cmd.parameters == []


# ---------------------------------------------------------------------------
# Behavioral equivalence with old COMMANDS_WITHOUT_DELAY approach
# ---------------------------------------------------------------------------


class TestEquivalenceWithOldApproach:
    """Verify the nparams=1 rule produces correct results for real RTS devices.

    Based on actual Overkiz API fixture data (cloud_somfy_connexoon_rts_asia.json):
    - Movement commands (close, open, up, down, stop, my, rest): nparams=1 -> GET duration
    - Utility commands (identify, test): nparams=0 -> no injection
    - Tilt/move commands (tiltPositive, tiltNegative, moveOf): nparams=2 -> no injection
    - Some venetian blind devices have open/close/stop at nparams=0 -> no injection

    The old COMMANDS_WITHOUT_DELAY blocklist (identify, off, on, onWithTimer,
    test, tiltPositive, tiltNegative) is no longer needed because:
    - identify, test: nparams=0 — naturally excluded
    - tiltPositive, tiltNegative: nparams=2 — excluded by nparams==1 rule
    - off, on, onWithTimer: don't exist on real RTS devices in the fixtures
    """

    @pytest.mark.asyncio
    async def test_movement_commands_injected(self, client_rts_0):
        """All movement commands with nparams=1 get duration injected."""
        client_rts_0.devices = [_rts_device()]

        for cmd_name in ("close", "open", "up", "down", "stop", "my", "rest"):
            action = Action(
                device_url="rts://1234-5678-9012/1",
                commands=[Command(name=cmd_name)],
            )

            with patch.object(
                client_rts_0, "_execute_action_group_direct", new_callable=AsyncMock
            ) as mock_exec:
                mock_exec.return_value = "exec-123"
                await client_rts_0.execute_action_group([action])

                called_actions = mock_exec.call_args[0][0]
                assert called_actions[0].commands[0].parameters == [0], (
                    f"'{cmd_name}' (nparams=1) must get duration=0"
                )

    @pytest.mark.asyncio
    async def test_tilt_commands_not_injected(self, client_rts_0):
        """tiltPositive/tiltNegative have nparams=2 (position, speed) — not duration."""
        client_rts_0.devices = [_rts_device()]

        for cmd_name in ("tiltPositive", "tiltNegative", "moveOf"):
            action = Action(
                device_url="rts://1234-5678-9012/1",
                commands=[Command(name=cmd_name)],
            )

            with patch.object(
                client_rts_0, "_execute_action_group_direct", new_callable=AsyncMock
            ) as mock_exec:
                mock_exec.return_value = "exec-123"
                await client_rts_0.execute_action_group([action])

                called_actions = mock_exec.call_args[0][0]
                assert called_actions[0].commands[0].parameters is None, (
                    f"'{cmd_name}' (nparams=2) must NOT get duration"
                )

    @pytest.mark.asyncio
    async def test_venetian_blind_zero_nparams_device(self, client_rts_0):
        """Some RTS venetian blinds have open/close/stop at nparams=0 — no injection."""
        device = _rts_device(
            commands=[
                CommandDefinition(command_name="open", nparams=0),
                CommandDefinition(command_name="close", nparams=0),
                CommandDefinition(command_name="stop", nparams=0),
                CommandDefinition(command_name="my", nparams=1),
                CommandDefinition(command_name="tiltPositive", nparams=2),
                CommandDefinition(command_name="tiltNegative", nparams=2),
                CommandDefinition(command_name="identify", nparams=0),
            ]
        )
        client_rts_0.devices = [device]

        for cmd_name, expect_injection in [
            ("open", False),
            ("close", False),
            ("stop", False),
            ("my", True),
            ("tiltPositive", False),
            ("identify", False),
        ]:
            action = Action(
                device_url="rts://1234-5678-9012/1",
                commands=[Command(name=cmd_name)],
            )

            with patch.object(
                client_rts_0, "_execute_action_group_direct", new_callable=AsyncMock
            ) as mock_exec:
                mock_exec.return_value = "exec-123"
                await client_rts_0.execute_action_group([action])

                called_actions = mock_exec.call_args[0][0]
                params = called_actions[0].commands[0].parameters
                if expect_injection:
                    assert params == [0], f"'{cmd_name}' should get duration"
                else:
                    assert params is None, f"'{cmd_name}' should NOT get duration"


# ---------------------------------------------------------------------------
# Unit test for _apply_rts_duration directly (fast, no mock overhead)
# ---------------------------------------------------------------------------


class TestApplyRtsDurationDirect:
    """Direct unit tests on _apply_rts_duration without execute_action_group overhead."""

    def test_returns_same_list_when_setting_none(self, client_no_rts):
        """Early return when rts_command_duration is None."""
        client_no_rts.devices = [_rts_device()]
        actions = [
            Action(
                device_url="rts://1234-5678-9012/1",
                commands=[Command(name="close")],
            )
        ]

        result = client_no_rts._apply_rts_duration(actions)
        assert result is actions  # Same object, not a copy

    def test_rts_injection_basic(self, client_rts_0):
        """Direct call: RTS close with nparams=1 and no params."""
        client_rts_0.devices = [_rts_device()]
        actions = [
            Action(
                device_url="rts://1234-5678-9012/1",
                commands=[Command(name="close")],
            )
        ]

        result = client_rts_0._apply_rts_duration(actions)
        assert result[0].commands[0].parameters == [0]

    def test_preserves_command_type(self, client_rts_0):
        """The type field on a Command is preserved through injection."""
        client_rts_0.devices = [_rts_device()]
        actions = [
            Action(
                device_url="rts://1234-5678-9012/1",
                commands=[Command(name="close", type=1)],
            )
        ]

        result = client_rts_0._apply_rts_duration(actions)
        assert result[0].commands[0].type == 1
        assert result[0].commands[0].parameters == [0]

    def test_multiple_devices_in_single_batch(self, client_rts_0):
        """Batch with two RTS devices and one IO."""
        rts1 = _rts_device(device_url="rts://1234-5678-9012/1")
        rts2 = _rts_device(device_url="rts://1234-5678-9012/5")
        io = _io_device()
        client_rts_0.devices = [rts1, rts2, io]

        actions = [
            Action(
                device_url="rts://1234-5678-9012/1", commands=[Command(name="close")]
            ),
            Action(
                device_url="io://1234-5678-9012/2", commands=[Command(name="close")]
            ),
            Action(
                device_url="rts://1234-5678-9012/5", commands=[Command(name="open")]
            ),
        ]

        result = client_rts_0._apply_rts_duration(actions)
        assert result[0].commands[0].parameters == [0]
        assert result[1].commands[0].parameters is None
        assert result[2].commands[0].parameters == [0]
