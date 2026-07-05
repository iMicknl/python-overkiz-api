"""Unit tests for models (Device, State and States helpers)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import cattrs.errors
import pytest

from pyoverkiz.converter import converter
from pyoverkiz.enums import (
    DataType,
    EventName,
    ExecutionState,
    FailureType,
    GatewaySubType,
    Protocol,
    StateDefinitionType,
    UIClassifier,
    UIProfile,
)
from pyoverkiz.enums.command import OverkizCommand
from pyoverkiz.enums.state import OverkizAttribute, OverkizState
from pyoverkiz.models import (
    Action,
    ActionGroup,
    Command,
    CommandDefinitions,
    Definition,
    Device,
    DeviceAvailableEvent,
    DeviceCreatedEvent,
    DeviceDisabledEvent,
    DeviceRemovedEvent,
    DeviceStateChangedEvent,
    DeviceUnavailableEvent,
    DeviceUpdatedEvent,
    Event,
    EventState,
    ExecutionRegisteredEvent,
    ExecutionStateChangedEvent,
    FailureEvent,
    Gateway,
    GatewayFunctionChangedEvent,
    GatewaySynchronizationEndedEvent,
    PersistedActionGroup,
    Setup,
    State,
    StateDefinition,
    StateDefinitions,
    States,
    ZoneCreatedEvent,
    ZoneDeletedEvent,
    ZoneUpdatedEvent,
)
from pyoverkiz.obfuscate import obfuscate_id

RAW_STATES = [
    {"name": "core:NameState", "type": 3, "value": "alarm name"},
    {"name": "internal:CurrentAlarmModeState", "type": 3, "value": "off"},
    {"name": "internal:AlarmDelayState", "type": 1, "value": 60},
]

RAW_DEVICES = {
    "creationTime": 1495389504000,
    "lastUpdateTime": 1495389504000,
    "label": "roller shutter 1",
    "deviceURL": "io://1234-5678-9012/10077486",
    "shortcut": False,
    "controllableName": "io:RollerShutterGenericIOComponent",
    "definition": {
        "commands": [
            {"commandName": "close", "nparams": 0},
            {"commandName": "open", "nparams": 0},
        ],
        "states": [
            {"type": "ContinuousState", "qualifiedName": "core:ClosureState"},
            {
                "type": "DiscreteState",
                "values": ["good", "low", "normal", "verylow"],
                "qualifiedName": "core:DiscreteRSSILevelState",
            },
            {
                "type": "ContinuousState",
                "qualifiedName": "core:Memorized1PositionState",
            },
        ],
        "dataProperties": [{"value": "500", "qualifiedName": "core:identifyInterval"}],
        "widgetName": "PositionableRollerShutter",
        "uiProfiles": [
            "StatefulCloseableShutter",
            "Closeable",
        ],
        "uiClassifiers": [
            "heatingSystem",
            "emitter",
        ],
        "uiClass": "RollerShutter",
        "qualifiedName": "io:RollerShutterGenericIOComponent",
        "type": "ACTUATOR",
    },
    "states": [
        {"name": "core:StatusState", "type": 3, "value": "available"},
        {"name": "core:DiscreteRSSILevelState", "type": 3, "value": "good"},
        {"name": "core:ClosureState", "type": 1, "value": 100},
    ],
    "available": True,
    "enabled": True,
    "placeOID": "28750a0f-79c0-4815-8c52-fac9de92a0e1",
    "widget": "PositionableRollerShutter",
    "type": 1,
    "oid": "ebca1376-5a33-4d2b-85b6-df73220687a2",
    "uiClass": "RollerShutter",
}

STATE = "core:NameState"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "setup"


def _make_device(raw: dict | None = None) -> Device:
    """Create a Device from raw camelCase dict via the converter."""
    return converter.structure(raw or RAW_DEVICES, Device)


class TestSetup:
    """Tests for setup-level ID parsing and redaction behavior."""

    def test_id_is_raw_but_repr_is_redacted_when_present(self):
        """When API provides `id`, keep raw value but redact it in repr output."""
        raw_setup = json.loads(
            (FIXTURES_DIR / "setup_tahoma_1.json").read_text(encoding="utf-8")
        )
        setup = converter.structure(raw_setup, Setup)
        raw_id = "SETUP-1234-1234-8044"
        redacted_id = obfuscate_id(raw_id)

        assert setup.id == raw_id
        assert redacted_id in repr(setup)
        assert raw_id not in repr(setup)

    def test_id_is_none_when_missing(self):
        """When API omits `id`, setup.id should stay None."""
        raw_setup = json.loads(
            (FIXTURES_DIR / "setup_local.json").read_text(encoding="utf-8")
        )
        setup = converter.structure(raw_setup, Setup)

        assert setup.id is None

    def test_id_is_none_without_input_id(self):
        """Constructing setup without an id keeps setup.id as None."""
        setup = Setup(gateways=[], devices=[])

        assert setup.id is None

    def test_setup_drops_devices_missing_required_fields(self, caplog):
        """Devices missing required fields are dropped, not fatal."""
        raw_setup = json.loads(
            (FIXTURES_DIR / "setup_local_tahoma_sonos.json").read_text(encoding="utf-8")
        )

        with caplog.at_level(logging.WARNING):
            setup = converter.structure(raw_setup, Setup)

        assert len(setup.devices) == 13
        assert sum("incomplete data from hub" in r.message for r in caplog.records) == 3


class TestGateway:
    """Tests for Gateway model parsing, focused on sub_type handling."""

    @staticmethod
    def _structure(sub_type: int | None) -> Gateway:
        raw: dict = {
            "gatewayId": "1234-5678-9012",
            "connectivity": {"status": "OK", "protocolVersion": "1"},
        }
        if sub_type is not None:
            raw["subType"] = sub_type
        return converter.structure(raw, Gateway)

    def test_sub_type_zero_is_none(self):
        """A subType of 0 means 'no specific sub-type' and structures as None."""
        assert self._structure(0).sub_type is None

    def test_sub_type_zero_in_fixture_is_none(self):
        """The Rexel gateway reports subType 0, which should surface as None."""
        raw_setup = json.loads(
            (FIXTURES_DIR / "setup_rexel.json").read_text(encoding="utf-8")
        )
        setup = converter.structure(raw_setup, Setup)

        assert setup.gateways[0].sub_type is None

    def test_known_sub_type_is_preserved(self):
        """A known non-zero subType still maps to its enum member."""
        assert self._structure(1).sub_type is GatewaySubType.TAHOMA_BASIC

    def test_unknown_non_zero_sub_type_falls_back_to_unknown(self):
        """An unrecognised non-zero subType stays UNKNOWN, not None."""
        assert self._structure(99).sub_type is GatewaySubType.UNKNOWN

    def test_missing_sub_type_is_none(self):
        """When subType is absent, sub_type defaults to None."""
        assert self._structure(None).sub_type is None

    def test_bare_enum_zero_is_unaffected(self):
        """Bare GatewaySubType structuring is unaffected by the 0 -> None scoping.

        The special-case lives on GatewaySubType | None, so structuring a plain
        GatewaySubType still uses the generic enum hook (0 -> UNKNOWN).
        """
        assert converter.structure(0, GatewaySubType) is GatewaySubType.UNKNOWN


class TestDevice:
    """Tests for Device model parsing and property extraction."""

    @pytest.mark.parametrize(
        (
            "device_url",
            "protocol",
            "gateway_id",
            "device_address",
            "subsystem_id",
            "is_sub_device",
        ),
        [
            (
                "io://1234-5678-9012/10077486",
                Protocol.IO,
                "1234-5678-9012",
                "10077486",
                None,
                False,
            ),
            (
                "io://1234-5678-9012/10077486#8",
                Protocol.IO,
                "1234-5678-9012",
                "10077486",
                8,
                True,
            ),
            (
                "hue://1234-1234-4411/001788676dde/lights/10",
                Protocol.HUE,
                "1234-1234-4411",
                "001788676dde/lights/10",
                None,
                False,
            ),
            (
                "hue://1234-1234-4411/001788676dde/lights/10#5",
                Protocol.HUE,
                "1234-1234-4411",
                "001788676dde/lights/10",
                5,
                True,
            ),
            (
                "upnpcontrol://1234-1234-4411/uuid:RINCON_000E586B571601400",
                Protocol.UPNP_CONTROL,
                "1234-1234-4411",
                "uuid:RINCON_000E586B571601400",
                None,
                False,
            ),
            (
                "upnpcontrol://1234-1234-4411/uuid:RINCON_000E586B571601400#7",
                Protocol.UPNP_CONTROL,
                "1234-1234-4411",
                "uuid:RINCON_000E586B571601400",
                7,
                True,
            ),
            (
                "zigbee://1234-1234-1234/9876/1",
                Protocol.ZIGBEE,
                "1234-1234-1234",
                "9876/1",
                None,
                False,
            ),
            (
                "zigbee://1234-1234-1234/9876/1#2",
                Protocol.ZIGBEE,
                "1234-1234-1234",
                "9876/1",
                2,
                True,
            ),
            (
                "eliot://ELIOT-000000000000000000000000000ABCDE/00000000000000000000000000125abc",
                Protocol.ELIOT,
                "ELIOT-000000000000000000000000000ABCDE",
                "00000000000000000000000000125abc",
                None,
                False,
            ),
            (
                "eliot://ELIOT-000000000000000000000000000ABCDE/00000000000000000000000000125abc#1",
                Protocol.ELIOT,
                "ELIOT-000000000000000000000000000ABCDE",
                "00000000000000000000000000125abc",
                1,
                False,
            ),
        ],
    )
    def test_base_url_parsing(
        self,
        device_url: str,
        protocol: Protocol,
        gateway_id: str,
        device_address: str,
        subsystem_id: int | None,
        is_sub_device: bool,
    ):
        """Ensure device URL parsing extracts protocol, gateway and address correctly."""
        device = _make_device({**RAW_DEVICES, "deviceURL": device_url})

        assert device.identifier.protocol == protocol
        assert device.identifier.gateway_id == gateway_id
        assert device.identifier.device_address == device_address
        assert device.identifier.subsystem_id == subsystem_id
        assert device.identifier.is_sub_device == is_sub_device

    @pytest.mark.parametrize(
        "device_url",
        [
            "foo://whatever",
            "io://1234-5678-9012/10077486#8 trailing",
        ],
    )
    def test_invalid_device_url_raises(self, device_url: str):
        """Invalid device URLs should raise during identifier parsing."""
        with pytest.raises(cattrs.errors.ClassValidationError):
            _make_device({**RAW_DEVICES, "deviceURL": device_url})

    def test_none_states(self):
        """Devices without a `states` field should provide an empty States object."""
        raw = dict(RAW_DEVICES)
        del raw["states"]
        device = _make_device(raw)
        assert device.states.get(STATE) is None

    def test_first_command(self):
        """Device.first_command() returns first supported command from list."""
        device = _make_device()
        assert device.first_command(["nonexistent", "open", "close"]) == "open"
        assert device.first_command(["nonexistent"]) is None

    def test_supports_command(self):
        """Device.supports_command() checks if device supports a single command."""
        device = _make_device()
        assert device.supports_command("open")
        assert not device.supports_command("nonexistent")

    def test_supports_any_command(self):
        """Device.supports_any_command() checks if device supports any command."""
        device = _make_device()
        assert device.supports_any_command(["nonexistent", "open"])
        assert not device.supports_any_command(["nonexistent"])

    def test_states_get_value(self):
        """device.states.get_value() returns value of a single state."""
        device = _make_device()
        assert device.states.get_value("core:ClosureState") == 100
        assert device.states.get_value("nonexistent") is None

    def test_states_first_value(self):
        """device.states.first_value() returns value of first matching state from list."""
        device = _make_device()
        value = device.states.first_value(["nonexistent", "core:ClosureState"])
        assert value == 100

    def test_states_has_value(self):
        """device.states.has_value() checks if a single state exists with non-None value."""
        device = _make_device()
        assert device.states.has_value("core:ClosureState")
        assert not device.states.has_value("nonexistent")

    def test_states_has_any_value(self):
        """device.states.has_any_value() checks if any state exists with non-None value."""
        device = _make_device()
        assert device.states.has_any_value(["nonexistent", "core:ClosureState"])
        assert not device.states.has_any_value(["nonexistent"])

    def test_states_accept_enum_keys(self):
        """States accessors accept OverkizState enums, not just plain strings."""
        device = _make_device()
        assert OverkizState.CORE_CLOSURE in device.states
        assert device.states.has_value(OverkizState.CORE_CLOSURE)
        assert device.states.get_value(OverkizState.CORE_CLOSURE) == 100
        assert device.states.first([OverkizState.CORE_CLOSURE]) is not None
        assert device.states.has_any_value([OverkizState.CORE_CLOSURE])

    def test_attributes_accept_enum_keys(self):
        """Attribute accessors accept OverkizAttribute enums, not just plain strings."""
        device = _make_device(
            {
                **RAW_DEVICES,
                "attributes": [
                    {"name": "core:Manufacturer", "type": 3, "value": "VELUX"},
                ],
            }
        )
        assert OverkizAttribute.CORE_MANUFACTURER in device.attributes
        assert device.attributes.has_value(OverkizAttribute.CORE_MANUFACTURER)
        assert (
            device.attributes.get_value(OverkizAttribute.CORE_MANUFACTURER) == "VELUX"
        )
        assert device.attributes.first([OverkizAttribute.CORE_MANUFACTURER]) is not None
        assert device.attributes.has_any_value([OverkizAttribute.CORE_MANUFACTURER])

    def test_definition_states_get(self):
        """device.definition.states.get() returns StateDefinition for a single state."""
        device = _make_device()
        state_def = device.definition.states.get("core:ClosureState")
        assert state_def is not None
        assert state_def.qualified_name == "core:ClosureState"
        assert device.definition.states.get("nonexistent") is None

    def test_definition_states_first(self):
        """device.definition.states.first() returns first matching StateDefinition from list."""
        device = _make_device()
        state_def = device.definition.states.first(["nonexistent", "core:ClosureState"])
        assert state_def is not None
        assert state_def.qualified_name == "core:ClosureState"

    def test_attributes_get_value(self):
        """device.attributes.get_value() returns value of a single attribute."""
        device = _make_device(
            {
                **RAW_DEVICES,
                "attributes": [
                    {"name": "core:Manufacturer", "type": 3, "value": "VELUX"},
                    {"name": "core:Model", "type": 3, "value": "WINDOW 100"},
                ],
            }
        )
        assert device.attributes.get_value("core:Model") == "WINDOW 100"
        assert device.attributes.get_value("nonexistent") is None

    def test_attributes_first_value_returns_first_match(self):
        """device.attributes.first_value() returns value of first matching attribute from list."""
        device = _make_device(
            {
                **RAW_DEVICES,
                "attributes": [
                    {"name": "core:Manufacturer", "type": 3, "value": "VELUX"},
                    {"name": "core:Model", "type": 3, "value": "WINDOW 100"},
                ],
            }
        )
        value = device.attributes.first_value(
            ["nonexistent", "core:Model", "core:Manufacturer"]
        )
        assert value == "WINDOW 100"

    def test_attributes_first_value_returns_none_when_no_match(self):
        """device.attributes.first_value() returns None when no attribute matches."""
        device = _make_device()
        assert (
            device.attributes.first_value(["nonexistent", "also_nonexistent"]) is None
        )

    def test_attributes_first_value_empty_attributes(self):
        """device.attributes.first_value() returns None for devices with no attributes."""
        device = _make_device({**RAW_DEVICES, "attributes": []})
        assert device.attributes.first_value(["core:Manufacturer"]) is None

    def test_attributes_first_value_with_none_values(self):
        """device.attributes.first_value() skips attributes with None values."""
        device = _make_device(
            {
                **RAW_DEVICES,
                "attributes": [
                    {"name": "core:Model", "type": 3, "value": None},
                    {"name": "core:Manufacturer", "type": 3, "value": "VELUX"},
                ],
            }
        )
        value = device.attributes.first_value(["core:Model", "core:Manufacturer"])
        assert value == "VELUX"


class TestStates:
    """Tests for the States container behaviour and getter semantics."""

    def _make_states(self, raw: list[dict] | None = None) -> States:
        return converter.structure(raw, States)

    def test_empty_states(self):
        """An empty list yields an empty States object with no state found."""
        states = self._make_states([])
        assert not states
        assert states.get(STATE) is None

    def test_none_states(self):
        """A None value for states should behave as empty."""
        states = self._make_states(None)
        assert not states
        assert states.get(STATE) is None

    def test_getter(self):
        """Retrieve a known state and validate its properties."""
        states = self._make_states(RAW_STATES)
        state = states.get(STATE)
        assert state is not None
        assert state.name == STATE
        assert state.type == DataType.STRING
        assert state.value == "alarm name"

    def test_getter_missing(self):
        """Requesting a missing state returns falsy (None)."""
        states = self._make_states(RAW_STATES)
        state = states.get("FooState")
        assert state is None

    def test_get_value_returns_value(self):
        """get_value() returns the value of a state by name."""
        states = self._make_states(RAW_STATES)
        assert states.get_value("core:NameState") == "alarm name"

    def test_get_value_returns_none_when_missing(self):
        """get_value() returns None for a missing state."""
        states = self._make_states(RAW_STATES)
        assert states.get_value("nonexistent") is None

    def test_first_returns_first_match(self):
        """first() returns the first state with a non-None value."""
        states = self._make_states(RAW_STATES)
        state = states.first(
            ["nonexistent", "core:NameState", "internal:AlarmDelayState"]
        )
        assert state is not None
        assert state.name == "core:NameState"

    def test_first_returns_none_when_no_match(self):
        """first() returns None when no state matches."""
        states = self._make_states(RAW_STATES)
        assert states.first(["nonexistent", "also_nonexistent"]) is None

    def test_first_value_returns_first_value(self):
        """first_value() returns the value of the first matching state."""
        states = self._make_states(RAW_STATES)
        value = states.first_value(["nonexistent", "core:NameState"])
        assert value == "alarm name"

    def test_first_value_returns_none_when_no_match(self):
        """first_value() returns None when no state matches."""
        states = self._make_states(RAW_STATES)
        assert states.first_value(["nonexistent"]) is None

    def test_has_value_returns_true(self):
        """has_value() returns True when the state exists with a non-None value."""
        states = self._make_states(RAW_STATES)
        assert states.has_value("core:NameState")

    def test_has_value_returns_false(self):
        """has_value() returns False when the state does not exist."""
        states = self._make_states(RAW_STATES)
        assert not states.has_value("nonexistent")

    def test_has_any_value_true(self):
        """has_any_value() returns True when at least one state exists."""
        states = self._make_states(RAW_STATES)
        assert states.has_any_value(["nonexistent", "core:NameState"])

    def test_has_any_value_false(self):
        """has_any_value() returns False when no state exists."""
        states = self._make_states(RAW_STATES)
        assert not states.has_any_value(["nonexistent", "also_nonexistent"])

    def test_getitem_raises_keyerror_on_missing(self):
        """Subscript access raises KeyError for missing states."""
        states = self._make_states(RAW_STATES)
        with pytest.raises(KeyError, match="nonexistent"):
            states["nonexistent"]

    def test_getitem_returns_state_on_hit(self):
        """Subscript access returns the State for a known name."""
        states = self._make_states(RAW_STATES)
        state = states[STATE]
        assert state.name == STATE

    def test_contains_existing(self):
        """'in' operator returns True for existing state names."""
        states = self._make_states(RAW_STATES)
        assert STATE in states

    def test_contains_missing(self):
        """'in' operator returns False for missing state names."""
        states = self._make_states(RAW_STATES)
        assert "nonexistent" not in states

    def test_setitem_replaces_existing(self):
        """Setting an existing state replaces it."""
        states = self._make_states(RAW_STATES)
        new_state = State(name=STATE, type=DataType.INTEGER, value=42)
        states[STATE] = new_state
        assert states.get(STATE).value == 42

    def test_setitem_appends_new(self):
        """Setting a new state appends it."""
        states = self._make_states(RAW_STATES)
        initial_len = len(states)
        new_state = State(name="new:State", type=DataType.INTEGER, value=1)
        states["new:State"] = new_state
        assert len(states) == initial_len + 1
        assert states.get("new:State").value == 1


class TestCommandDefinitions:
    """Tests for CommandDefinitions container and helper methods."""

    def _make_cmds(self, raw: list[dict]) -> CommandDefinitions:
        return converter.structure(raw, CommandDefinitions)

    def test_first_returns_first_match(self):
        """first() returns the first command name that exists."""
        cmds = self._make_cmds(
            [
                {"commandName": "close", "nparams": 0},
                {"commandName": "open", "nparams": 0},
                {"commandName": "setPosition", "nparams": 1},
            ]
        )
        assert cmds.first(["nonexistent", "open", "close"]) == "open"

    def test_first_returns_none_when_no_match(self):
        """first() returns None when no command matches."""
        cmds = self._make_cmds([{"commandName": "close", "nparams": 0}])
        assert cmds.first(["nonexistent", "also_nonexistent"]) is None

    def test_has_any_true(self):
        """has_any() returns True when at least one command exists."""
        cmds = self._make_cmds([{"commandName": "close", "nparams": 0}])
        assert cmds.has_any(["nonexistent", "close"])

    def test_has_any_false(self):
        """has_any() returns False when no command matches."""
        cmds = self._make_cmds([{"commandName": "close", "nparams": 0}])
        assert not cmds.has_any(["nonexistent", "also_nonexistent"])

    def test_contains_supports_overkiz_command_enum(self):
        """__contains__ supports OverkizCommand enum values."""
        cmds = self._make_cmds([{"commandName": "open", "nparams": 0}])
        assert OverkizCommand.OPEN in cmds
        assert OverkizCommand.CLOSE not in cmds

    def test_getitem_raises_keyerror_on_missing(self):
        """Subscript access raises KeyError for missing commands."""
        cmds = self._make_cmds([{"commandName": "close", "nparams": 0}])
        with pytest.raises(KeyError, match="nonexistent"):
            cmds["nonexistent"]

    def test_getitem_returns_command_on_hit(self):
        """Subscript access returns the CommandDefinition for a known command."""
        cmds = self._make_cmds([{"commandName": "close", "nparams": 0}])
        cmd = cmds["close"]
        assert cmd.command_name == "close"

    def test_get_returns_none_on_missing(self):
        """get() returns None for missing commands."""
        cmds = self._make_cmds([{"commandName": "close", "nparams": 0}])
        assert cmds.get("nonexistent") is None

    def test_contains_existing(self):
        """'in' operator returns True for existing command names."""
        cmds = self._make_cmds([{"commandName": "close", "nparams": 0}])
        assert "close" in cmds

    def test_contains_missing(self):
        """'in' operator returns False for missing command names."""
        cmds = self._make_cmds([{"commandName": "close", "nparams": 0}])
        assert "nonexistent" not in cmds


class TestStateDefinitions:
    """Tests for the StateDefinitions container."""

    def _make_state_defs(self) -> StateDefinitions:
        return StateDefinitions(
            [
                StateDefinition(
                    qualified_name="core:ClosureState", type="ContinuousState"
                ),
                StateDefinition(
                    qualified_name="core:TargetClosureState", type="ContinuousState"
                ),
            ]
        )

    def test_get_returns_match(self):
        """get() returns the StateDefinition by qualified name."""
        state_defs = self._make_state_defs()
        state_def = state_defs.get("core:ClosureState")
        assert state_def is not None
        assert state_def.qualified_name == "core:ClosureState"

    def test_get_returns_none_when_missing(self):
        """get() returns None when no state definition matches."""
        state_defs = StateDefinitions()
        assert state_defs.get("nonexistent") is None

    def test_getitem_returns_match(self):
        """[] returns the StateDefinition by qualified name."""
        state_defs = self._make_state_defs()
        assert state_defs["core:ClosureState"].qualified_name == "core:ClosureState"

    def test_getitem_raises_keyerror(self):
        """[] raises KeyError for missing state definitions."""
        state_defs = self._make_state_defs()
        with pytest.raises(KeyError, match="nonexistent"):
            state_defs["nonexistent"]

    def test_contains(self):
        """'in' operator works for state definitions."""
        state_defs = self._make_state_defs()
        assert "core:ClosureState" in state_defs
        assert "nonexistent" not in state_defs

    def test_first_respects_caller_priority(self):
        """first() returns based on names order, not definition order."""
        state_defs = self._make_state_defs()
        state_def = state_defs.first(["core:TargetClosureState", "core:ClosureState"])
        assert state_def is not None
        assert state_def.qualified_name == "core:TargetClosureState"

    def test_first_returns_none_when_no_match(self):
        """first() returns None when no state definition matches."""
        state_defs = self._make_state_defs()
        assert state_defs.first(["nonexistent"]) is None

    def test_has_any_returns_true(self):
        """has_any() returns True when any state definition matches."""
        state_defs = self._make_state_defs()
        assert state_defs.has_any(["nonexistent", "core:TargetClosureState"])

    def test_has_any_returns_false(self):
        """has_any() returns False when no state definition matches."""
        state_defs = self._make_state_defs()
        assert not state_defs.has_any(["nonexistent", "also_nonexistent"])

    def test_iteration(self):
        """Iteration yields qualified names."""
        state_defs = self._make_state_defs()
        assert list(state_defs) == ["core:ClosureState", "core:TargetClosureState"]

    def test_len(self):
        """len() returns number of state definitions."""
        state_defs = self._make_state_defs()
        assert len(state_defs) == 2
        assert len(StateDefinitions()) == 0

    def test_ui_profiles_parsed_as_enum(self):
        """ui_profiles should be structured as list[UIProfile]."""
        device = _make_device()
        assert UIProfile.CLOSEABLE in device.definition.ui_profiles
        assert UIProfile.STATEFUL_CLOSEABLE_SHUTTER in device.definition.ui_profiles
        assert UIProfile.DIMMABLE not in device.definition.ui_profiles

    def test_ui_classifiers_parsed_as_enum(self):
        """ui_classifiers should be structured as list[UIClassifier]."""
        device = _make_device()
        assert UIClassifier.HEATING_SYSTEM in device.definition.ui_classifiers
        assert UIClassifier.EMITTER in device.definition.ui_classifiers
        assert UIClassifier.SENSOR not in device.definition.ui_classifiers

    def test_ui_profiles_default_to_empty_list(self):
        """Omitted ui_profiles/ui_classifiers default to empty lists."""
        d1 = converter.structure({"commands": [], "states": []}, Definition)
        assert d1.ui_profiles == []
        assert d1.ui_classifiers == []


class TestStateDefinition:
    """Tests for StateDefinition initialization behavior."""

    def test_requires_name_or_qualified_name(self):
        """StateDefinition should reject payloads with neither identifier field."""
        with pytest.raises(
            ValueError,
            match=r"StateDefinition requires either `name` or `qualified_name`\.",
        ):
            StateDefinition()

    def test_continuous_type(self):
        """ContinuousState should be parsed as StateDefinitionType.CONTINUOUS."""
        sd = converter.structure(
            {"qualifiedName": "core:ClosureState", "type": "ContinuousState"},
            StateDefinition,
        )
        assert sd.type == StateDefinitionType.CONTINUOUS

    def test_discrete_type(self):
        """DiscreteState should be parsed as StateDefinitionType.DISCRETE."""
        sd = converter.structure(
            {
                "qualifiedName": "core:OnOffState",
                "type": "DiscreteState",
                "values": ["on", "off"],
            },
            StateDefinition,
        )
        assert sd.type == StateDefinitionType.DISCRETE
        assert sd.values == ["on", "off"]

    def test_data_type(self):
        """DataState should be parsed as StateDefinitionType.DATA."""
        sd = converter.structure(
            {"qualifiedName": "core:SomeDataState", "type": "DataState"},
            StateDefinition,
        )
        assert sd.type == StateDefinitionType.DATA

    def test_none_type(self):
        """Missing type should result in None."""
        sd = converter.structure(
            {"qualifiedName": "core:SomeState"},
            StateDefinition,
        )
        assert sd.type is None

    def test_unknown_type(self):
        """Unknown type strings should fallback to UNKNOWN."""
        sd = converter.structure(
            {"qualifiedName": "core:SomeState", "type": "FutureState"},
            StateDefinition,
        )
        assert sd.type == StateDefinitionType.UNKNOWN


class TestState:
    """Unit tests for State value accessors and type validation."""

    def test_int_value(self):
        """Integer typed state returns proper integer accessor."""
        state = State(name="state", type=DataType.INTEGER, value=1)
        assert state.value_as_int == 1

    def test_bad_int_value(self):
        """Accessor raises TypeError if the state type mismatches expected int."""
        state = State(name="state", type=DataType.BOOLEAN, value=False)
        with pytest.raises(TypeError):
            _ = state.value_as_int

    def test_float_value(self):
        """Float typed state returns proper float accessor."""
        state = State(name="state", type=DataType.FLOAT, value=1.0)
        assert state.value_as_float == 1.0

    def test_bad_float_value(self):
        """Accessor raises TypeError if the state type mismatches expected float."""
        state = State(name="state", type=DataType.BOOLEAN, value=False)
        with pytest.raises(TypeError):
            _ = state.value_as_float

    def test_bool_value(self):
        """Boolean typed state returns proper boolean accessor."""
        state = State(name="state", type=DataType.BOOLEAN, value=True)
        assert state.value_as_bool

    def test_bad_bool_value(self):
        """Accessor raises TypeError if the state type mismatches expected bool."""
        state = State(name="state", type=DataType.INTEGER, value=1)
        with pytest.raises(TypeError):
            _ = state.value_as_bool

    def test_str_value(self):
        """String typed state returns proper string accessor."""
        state = State(name="state", type=DataType.STRING, value="foo")
        assert state.value_as_str == "foo"

    def test_bad_str_value(self):
        """Accessor raises TypeError if the state type mismatches expected string."""
        state = State(name="state", type=DataType.BOOLEAN, value=False)
        with pytest.raises(TypeError):
            _ = state.value_as_str

    def test_dict_value(self):
        """JSON object typed state returns proper dict accessor."""
        state = State(name="state", type=DataType.JSON_OBJECT, value={"foo": "bar"})
        assert state.value_as_dict == {"foo": "bar"}

    def test_bad_dict_value(self):
        """Accessor raises TypeError if the state type mismatches expected dict."""
        state = State(name="state", type=DataType.BOOLEAN, value=False)
        with pytest.raises(TypeError):
            _ = state.value_as_dict

    def test_list_value(self):
        """JSON array typed state returns proper list accessor."""
        state = State(name="state", type=DataType.JSON_ARRAY, value=[1, 2])
        assert state.value_as_list == [1, 2]

    def test_bad_list_value(self):
        """Accessor raises TypeError if the state type mismatches expected list."""
        state = State(name="state", type=DataType.BOOLEAN, value=False)
        with pytest.raises(TypeError):
            _ = state.value_as_list


class TestEventState:
    """Unit tests for EventState cloud payload casting behavior."""

    def test_json_string_is_parsed(self):
        """Valid JSON payload strings are cast to typed Python values."""
        state = EventState(name="state", type=DataType.JSON_OBJECT, value='{"foo": 1}')

        assert state.value == {"foo": 1}

    def test_invalid_json_string_raises(self):
        """Malformed JSON payload strings raise ValueError."""
        with pytest.raises(ValueError, match="Invalid JSON for event state"):
            EventState(
                name="state",
                type=DataType.JSON_ARRAY,
                value="[not-valid-json",
            )

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
            ("", False),
            ("yes", False),
            ("no", False),
        ],
    )
    def test_boolean_string_casting(self, raw: str, expected: bool):
        """Cloud API returns booleans as strings; only 'true'/'1' are truthy."""
        state = EventState(name="state", type=DataType.BOOLEAN, value=raw)

        assert state.value is expected

    def test_boolean_native_passthrough(self):
        """Local API returns native booleans; they must not be re-cast."""
        true_state = EventState(name="state", type=DataType.BOOLEAN, value=True)
        false_state = EventState(name="state", type=DataType.BOOLEAN, value=False)

        assert true_state.value is True
        assert false_state.value is False

    @pytest.mark.parametrize(
        ("raw", "data_type", "expected"),
        [
            ("42", DataType.INTEGER, 42),
            ("-1", DataType.INTEGER, -1),
            ("0", DataType.INTEGER, 0),
            ("3.14", DataType.FLOAT, pytest.approx(3.14)),
            ("-1.5", DataType.FLOAT, pytest.approx(-1.5)),
            ("0.0", DataType.FLOAT, pytest.approx(0.0)),
            ("0", DataType.FLOAT, pytest.approx(0.0)),
            ("12345", DataType.DATE, 12345),
            ("0", DataType.DATE, 0),
            ("[1, 2]", DataType.JSON_ARRAY, [1, 2]),
            ("[]", DataType.JSON_ARRAY, []),
            ('{"foo": 1}', DataType.JSON_OBJECT, {"foo": 1}),
            ("{}", DataType.JSON_OBJECT, {}),
        ],
    )
    def test_other_type_casting(self, raw: str, data_type: DataType, expected):
        """Non-boolean string values are cast correctly."""
        state = EventState(name="state", type=data_type, value=raw)

        assert state.value == expected

    @pytest.mark.parametrize(
        ("raw", "data_type"),
        [
            ("abc", DataType.INTEGER),
            ("abc", DataType.FLOAT),
        ],
    )
    def test_invalid_numeric_string_raises(self, raw: str, data_type: DataType):
        """Non-numeric strings raise ValueError for numeric types."""
        with pytest.raises(ValueError, match="abc"):
            EventState(name="state", type=data_type, value=raw)

    def test_string_type_not_cast(self):
        """STRING type values are left as-is, not passed through any caster."""
        state = EventState(name="state", type=DataType.STRING, value="hello")

        assert state.value == "hello"

    def test_empty_string_type_not_cast(self):
        """Empty STRING type values are preserved."""
        state = EventState(name="state", type=DataType.STRING, value="")

        assert state.value == ""

    @pytest.mark.parametrize(
        ("value", "data_type"),
        [
            (42, DataType.INTEGER),
            (0, DataType.INTEGER),
            (3.14, DataType.FLOAT),
            (0.0, DataType.FLOAT),
            ({"foo": 1}, DataType.JSON_OBJECT),
            ([1, 2], DataType.JSON_ARRAY),
        ],
    )
    def test_native_value_not_cast(self, value: object, data_type: DataType):
        """Already-typed values (from local API) skip casting entirely."""
        state = EventState(name="state", type=data_type, value=value)

        assert state.value == value
        assert type(state.value) is type(value)


def test_command_to_payload_omits_none():
    """Command.to_payload omits None fields from the resulting payload."""
    from pyoverkiz.enums.command import OverkizCommand
    from pyoverkiz.models import Command

    cmd = Command(name=OverkizCommand.CLOSE, parameters=None, type=None)
    payload = cmd.to_payload()

    assert payload == {"name": "close"}


def test_command_to_payload_preserves_dict_parameter():
    """Command.to_payload passes dict/list parameters through untouched.

    Several Atlantic/Thermor commands (e.g. setAbsenceStartDate,
    setCurrentOperatingMode) take a dict parameter that must reach the API as a
    JSON object, not a stringified repr.
    """
    from pyoverkiz.models import Command

    date = {
        "year": 2026,
        "month": 5,
        "day": 28,
        "hour": 12,
        "minute": 0,
        "second": 0,
        "weekday": 3,
    }
    cmd = Command(name="setAbsenceStartDate", parameters=[date])

    payload = cmd.to_payload()

    assert payload["parameters"] == [date]


def test_command_to_payload_preserves_list_parameter():
    """Command.to_payload passes a nested list parameter through untouched."""
    from pyoverkiz.models import Command

    schedule = [[0, 1, 2], [3, 4, 5]]
    cmd = Command(name="setSchedule", parameters=[schedule])

    payload = cmd.to_payload()

    assert payload["parameters"] == [schedule]


def test_action_to_payload_and_parameters_conversion():
    """Action.to_payload converts nested Command enums to primitives."""
    from pyoverkiz.enums.command import OverkizCommand, OverkizCommandParam
    from pyoverkiz.models import Action, Command

    cmd = Command(
        name=OverkizCommand.SET_LEVEL, parameters=[10, OverkizCommandParam.A], type=1
    )
    action = Action(device_url="rts://2025-8464-6867/16756006", commands=[cmd])

    payload = action.to_payload()

    assert payload["device_url"] == "rts://2025-8464-6867/16756006"
    assert payload["commands"][0]["name"] == "setLevel"
    assert payload["commands"][0]["type"] == 1
    assert payload["commands"][0]["parameters"] == [10, "A"]


class TestEvent:
    """Tests for Event structuring via the cattrs converter."""

    def test_execution_state_changed_event(self):
        """Optional[Enum] fields (old_state, new_state) are structured into enums."""
        event = converter.structure(
            {
                "timestamp": 1631130760744,
                "setupOID": "741bc89f-a47b-4ad6-894d-a785c06956c2",
                "execId": "c6f83624-ac10-3e01-653e-2b025fee956d",
                "newState": "IN_PROGRESS",
                "ownerKey": "741bc89f-a47b-4ad6-894d-a785c06956c2",
                "type": 1,
                "subType": 1,
                "oldState": "TRANSMITTED",
                "timeToNextState": 0,
                "name": "ExecutionStateChangedEvent",
            },
            Event,
        )

        assert isinstance(event, ExecutionStateChangedEvent)
        assert event.name == EventName.EXECUTION_STATE_CHANGED
        assert event.old_state is ExecutionState.TRANSMITTED
        assert event.new_state is ExecutionState.IN_PROGRESS
        assert event.setup_oid == "741bc89f-a47b-4ad6-894d-a785c06956c2"

    def test_failure_type_code_structured_as_enum(self):
        """FailureType | None field is structured into an enum instance."""
        event = converter.structure(
            {
                "name": "ExecutionStateChangedEvent",
                "timestamp": 123,
                "execId": "c6f83624-ac10-3e01-653e-2b025fee956d",
                "newState": "FAILED",
                "oldState": "IN_PROGRESS",
                "failureTypeCode": 0,
            },
            Event,
        )

        assert isinstance(event, ExecutionStateChangedEvent)
        assert isinstance(event.failure_type_code, FailureType)
        assert event.failure_type_code is FailureType.NO_FAILURE

    def test_optional_enum_fields_none_when_absent(self):
        """Base events do not expose subtype-only enum fields."""
        event = converter.structure(
            {
                "name": "CommandExecutionStateChangedEvent",
                "timestamp": 1631130645998,
            },
            Event,
        )

        assert type(event) is Event
        assert not hasattr(event, "old_state")
        assert not hasattr(event, "new_state")
        assert not hasattr(event, "failure_type_code")

    def test_device_state_changed_event_with_states(self):
        """DeviceStateChangedEvent payload structures device_states as EventState."""
        event = converter.structure(
            {
                "timestamp": 1631130646544,
                "setupOID": "741bc89f-a47b-4ad6-894d-a785c06956c2",
                "deviceURL": "io://9876-1234-8767/4468654#1",
                "deviceStates": [
                    {
                        "name": "core:ElectricEnergyConsumptionState",
                        "type": 1,
                        "value": "23247220",
                    }
                ],
                "name": "DeviceStateChangedEvent",
            },
            Event,
        )

        assert isinstance(event, DeviceStateChangedEvent)
        assert event.name == EventName.DEVICE_STATE_CHANGED
        assert len(event.device_states) == 1
        assert isinstance(event.device_states[0], EventState)

    def test_event_fixture_structures_all_events(self):
        """All events in the cloud fixture file structure without errors."""
        raw_events = json.loads((Path("tests/fixtures/event/events.json")).read_text())
        events = [converter.structure(e, Event) for e in raw_events]

        assert len(events) == len(raw_events)
        state_changed = [e for e in events if isinstance(e, ExecutionStateChangedEvent)]
        assert state_changed  # fixture contains ExecutionStateChangedEvent entries
        for e in state_changed:
            assert isinstance(e.old_state, ExecutionState)
            assert isinstance(e.new_state, ExecutionState)

    def test_base_event_has_universal_fields_only(self):
        """Base Event keeps universal fields incl. new owning_partners; no subtype fields."""
        event = converter.structure(
            {
                "name": "CommandExecutionStateChangedEvent",
                "timestamp": 1631130645998,
                "setupOID": "741bc89f-a47b-4ad6-894d-a785c06956c2",
                "owningPartners": ["partner-a"],
            },
            Event,
        )

        assert type(event) is Event
        assert event.name == EventName.COMMAND_EXECUTION_STATE_CHANGE
        assert event.timestamp == 1631130645998
        assert event.setup_oid == "741bc89f-a47b-4ad6-894d-a785c06956c2"
        assert event.owning_partners == ["partner-a"]
        assert not hasattr(event, "device_states")
        assert not hasattr(event, "new_state")

    def test_device_state_changed_event_subtype(self):
        """DeviceStateChangedEvent has required device_url and device_states."""
        event = DeviceStateChangedEvent(
            name=EventName.DEVICE_STATE_CHANGED,
            device_url="io://1234-5678-9012/4468654#1",
            device_states=[
                EventState(
                    name="core:ElectricEnergyConsumptionState",
                    type=DataType.INTEGER,
                    value=23247220,
                )
            ],
        )

        assert isinstance(event, Event)
        assert event.device_url == "io://1234-5678-9012/4468654#1"
        assert len(event.device_states) == 1

    def test_execution_state_changed_event_subtype(self):
        """ExecutionStateChangedEvent carries execution transition fields."""
        event = ExecutionStateChangedEvent(
            name=EventName.EXECUTION_STATE_CHANGED,
            exec_id="c6f83624-ac10-3e01-653e-2b025fee956d",
            new_state=ExecutionState.IN_PROGRESS,
            old_state=ExecutionState.TRANSMITTED,
        )
        assert isinstance(event, Event)
        assert event.new_state is ExecutionState.IN_PROGRESS
        assert event.old_state is ExecutionState.TRANSMITTED

    def test_execution_registered_event_subtype(self):
        """ExecutionRegisteredEvent carries actions and exec metadata."""
        event = ExecutionRegisteredEvent(
            name=EventName.EXECUTION_REGISTERED,
            exec_id="c6f83624-ac10-3e01-653e-2b025fee956d",
            label="Volet salon",
            actions=[
                Action(
                    device_url="io://1234-5678-9012/11212197",
                    commands=[Command(name="setClosure")],
                )
            ],
        )
        assert isinstance(event, Event)
        assert event.exec_id == "c6f83624-ac10-3e01-653e-2b025fee956d"
        assert len(event.actions) == 1

    def test_failure_event_subtype(self):
        """FailureEvent carries failure_type plus the operation's scope id."""
        event = FailureEvent(
            name=EventName.GATEWAY_SYNCHRONIZATION_FAILED,
            failure_type="some failure",
            gateway_id="9876-1234-8767",
        )
        assert isinstance(event, Event)
        assert event.failure_type == "some failure"
        assert event.gateway_id == "9876-1234-8767"
        # failureTypeCode is never sent on *FailedEvent; it is not modeled here.
        assert not hasattr(event, "failure_type_code")

    def test_device_lifecycle_subtypes(self):
        """Device lifecycle events carry device_url; created/updated/removed add controllable_name."""
        created = DeviceCreatedEvent(
            name=EventName.DEVICE_CREATED,
            device_url="io://1234-5678-9012/4468654",
            controllable_name="io:RollerShutterGenericIOComponent",
        )
        assert created.device_url == "io://1234-5678-9012/4468654"
        assert created.controllable_name == "io:RollerShutterGenericIOComponent"

        updated = DeviceUpdatedEvent(
            name=EventName.DEVICE_UPDATED,
            device_url="io://1234-5678-9012/4468654",
            controllable_name="io:RollerShutterGenericIOComponent",
        )
        assert updated.controllable_name == "io:RollerShutterGenericIOComponent"

        removed = DeviceRemovedEvent(
            name=EventName.DEVICE_REMOVED,
            device_url="io://1234-5678-9012/4468654",
            controllable_name="io:RollerShutterGenericIOComponent",
        )
        assert removed.controllable_name == "io:RollerShutterGenericIOComponent"

        # Available / Unavailable / Disabled carry only device_url (no controllable_name).
        for cls, event_name in (
            (DeviceAvailableEvent, EventName.DEVICE_AVAILABLE),
            (DeviceUnavailableEvent, EventName.DEVICE_UNAVAILABLE),
            (DeviceDisabledEvent, EventName.DEVICE_DISABLED),
        ):
            event = cls(name=event_name, device_url="io://1234-5678-9012/4468654")
            assert isinstance(event, Event)
            assert event.device_url == "io://1234-5678-9012/4468654"
            assert not hasattr(event, "controllable_name")

    def test_zone_event_subtypes(self):
        """Zone events carry zone_oid; create/update add device_urls and place_oids."""
        created = ZoneCreatedEvent(
            name=EventName.ZONE_CREATED,
            zone_oid="zone-1",
            device_urls=["io://1234-5678-9012/1"],
            place_oids=["place-1"],
        )
        assert created.zone_oid == "zone-1"
        assert created.device_urls == ["io://1234-5678-9012/1"]
        assert created.place_oids == ["place-1"]

        updated = ZoneUpdatedEvent(
            name=EventName.ZONE_UPDATED,
            zone_oid="zone-1",
            device_urls=["io://1234-5678-9012/1"],
            place_oids=["place-1"],
        )
        assert updated.zone_oid == "zone-1"
        assert updated.device_urls == ["io://1234-5678-9012/1"]

        deleted = ZoneDeletedEvent(name=EventName.ZONE_DELETED, zone_oid="zone-1")
        assert isinstance(deleted, Event)
        assert deleted.zone_oid == "zone-1"
        assert not hasattr(deleted, "device_urls")

    def test_converter_dispatches_zone_created_with_api_casing(self):
        """Zone payload keys (zoneOID/deviceURLs/placeOIDs) map to snake_case fields."""
        event = converter.structure(
            {
                "name": "ZoneCreatedEvent",
                "zoneOID": "zone-1",
                "type": 1,
                "deviceURLs": ["io://1234-5678-9012/1"],
                "placeOIDs": ["place-1"],
            },
            Event,
        )
        assert isinstance(event, ZoneCreatedEvent)
        assert event.zone_oid == "zone-1"
        assert event.device_urls == ["io://1234-5678-9012/1"]
        assert event.place_oids == ["place-1"]

    def test_converter_dispatches_device_state_changed(self):
        """Structuring a DeviceStateChangedEvent payload yields the subtype."""
        event = converter.structure(
            {
                "name": "DeviceStateChangedEvent",
                "timestamp": 1631130646544,
                "deviceURL": "io://1234-5678-9012/4468654#1",
                "deviceStates": [
                    {
                        "name": "core:ElectricEnergyConsumptionState",
                        "type": 1,
                        "value": "23247220",
                    }
                ],
            },
            Event,
        )
        assert isinstance(event, DeviceStateChangedEvent)
        assert event.device_url == "io://1234-5678-9012/4468654#1"
        assert event.device_states[0].value == 23247220  # cast by EventState

    def test_converter_dispatches_execution_state_changed(self):
        """Structuring an ExecutionStateChangedEvent payload yields the subtype."""
        event = converter.structure(
            {
                "name": "ExecutionStateChangedEvent",
                "newState": "IN_PROGRESS",
                "oldState": "TRANSMITTED",
                "execId": "abc",
            },
            Event,
        )
        assert isinstance(event, ExecutionStateChangedEvent)
        assert event.new_state is ExecutionState.IN_PROGRESS

    def test_converter_dispatches_gateway_event(self):
        """A Gateway* event structures into its own per-name class with gateway_id."""
        event = converter.structure(
            {
                "name": "GatewaySynchronizationEndedEvent",
                "timestamp": 1631130645998,
                "gatewayId": "9876-1234-8767",
            },
            Event,
        )
        assert isinstance(event, GatewaySynchronizationEndedEvent)
        assert event.name == EventName.GATEWAY_SYNCHRONIZATION_ENDED
        assert event.gateway_id == "9876-1234-8767"

    def test_converter_dispatches_gateway_event_with_extra_fields(self):
        """A gateway event with documented extra payload exposes it on its subtype."""
        event = converter.structure(
            {
                "name": "GatewayFunctionChangedEvent",
                "gatewayId": "9876-1234-8767",
                "functionType": 1,
                "enabled": False,
            },
            Event,
        )
        assert isinstance(event, GatewayFunctionChangedEvent)
        assert event.function_type == 1
        assert event.enabled is False

    def test_converter_falls_back_to_base_event(self):
        """Unmodeled, non-gateway, non-failure event names structure into base Event."""
        event = converter.structure(
            {"name": "CommandExecutionStateChangedEvent", "timestamp": 1},
            Event,
        )
        assert type(event) is Event
        assert event.name == EventName.COMMAND_EXECUTION_STATE_CHANGE

    def test_converter_unknown_event_name_falls_back_to_base(self):
        """Genuinely unknown event names use UnknownEnumMixin and base Event."""
        event = converter.structure(
            {"name": "SomeBrandNewEvent", "timestamp": 1},
            Event,
        )
        assert type(event) is Event
        assert event.name == EventName.UNKNOWN

    def test_converter_dispatches_failed_event_to_failure_event(self):
        """A gateway *FailedEvent structures into FailureEvent and keeps gateway_id."""
        event = converter.structure(
            {
                "name": "GatewaySynchronizationFailedEvent",
                "timestamp": 1,
                "failureType": "some failure",
                "gatewayId": "9876-1234-8767",
            },
            Event,
        )
        assert isinstance(event, FailureEvent)
        assert event.failure_type == "some failure"
        assert event.gateway_id == "9876-1234-8767"

    def test_converter_dispatches_device_failed_event_keeps_device_url(self):
        """A device-scoped *FailedEvent keeps its deviceURL via FailureEvent."""
        event = converter.structure(
            {
                "name": "DeviceFirmwareUpdateFailedEvent",
                "timestamp": 1,
                "failureType": "some failure",
                "deviceURL": "io://1234-5678-9012/4468654",
            },
            Event,
        )
        assert isinstance(event, FailureEvent)
        assert event.device_url == "io://1234-5678-9012/4468654"

    def test_converter_dispatches_failed_event_keeps_protocol_type(self):
        """A discovery/refresh *FailedEvent keeps its protocolType via FailureEvent."""
        event = converter.structure(
            {
                "name": "RefreshAllDevicesStatesFailedEvent",
                "timestamp": 1,
                "failureType": "some failure",
                "gatewayId": "9876-1234-8767",
                "protocolType": 8,
            },
            Event,
        )
        assert isinstance(event, FailureEvent)
        assert event.gateway_id == "9876-1234-8767"
        assert event.protocol_type == 8

    def test_subtype_missing_required_field_degrades_to_base_event(self, caplog):
        """A subtype payload missing a required field degrades to base Event, with a warning."""
        with caplog.at_level(logging.WARNING, logger="pyoverkiz.converter"):
            event = converter.structure(
                # DeviceStateChangedEvent without the required deviceURL.
                {"name": "DeviceStateChangedEvent", "deviceStates": []},
                Event,
            )

        assert type(event) is Event
        assert event.name == EventName.DEVICE_STATE_CHANGED
        assert "falling back to base Event" in caplog.text

    def test_one_malformed_event_does_not_fail_the_batch(self, caplog):
        """A malformed event in a list degrades alone; the rest structure normally."""
        raw_events = [
            {
                "name": "DeviceStateChangedEvent",
                "deviceURL": "io://1234-5678-9012/1",
                "deviceStates": [],
            },
            # Missing the required deviceURL -> degrades to base Event.
            {"name": "DeviceStateChangedEvent", "deviceStates": []},
            {
                "name": "GatewaySynchronizationEndedEvent",
                "gatewayId": "9876-1234-8767",
            },
        ]
        with caplog.at_level(logging.WARNING, logger="pyoverkiz.converter"):
            events = converter.structure(raw_events, list[Event])

        assert len(events) == 3
        assert isinstance(events[0], DeviceStateChangedEvent)
        assert type(events[1]) is Event  # degraded
        assert isinstance(events[2], GatewaySynchronizationEndedEvent)

    def test_unstructurable_event_is_dropped_from_the_batch(self, caplog):
        """Events that cannot be built at all (no name, not a dict) are dropped, not raised."""
        raw_events = [
            {
                "name": "DeviceStateChangedEvent",
                "deviceURL": "io://1234-5678-9012/1",
                "deviceStates": [],
            },
            {"deviceURL": "io://1234-5678-9012/2"},  # no "name" -> unstructurable
            "garbage",  # not a dict -> unstructurable
            {
                "name": "GatewaySynchronizationEndedEvent",
                "gatewayId": "9876-1234-8767",
            },
        ]
        with caplog.at_level(logging.WARNING, logger="pyoverkiz.converter"):
            events = converter.structure(raw_events, list[Event])

        assert len(events) == 2  # the two unstructurable entries are dropped
        assert isinstance(events[0], DeviceStateChangedEvent)
        assert isinstance(events[1], GatewaySynchronizationEndedEvent)
        assert "Dropping unstructurable event" in caplog.text

    def test_local_event_fixture_structures_all_events(self):
        """All events in the local-API fixture structure into DeviceStateChangedEvent."""
        raw_events = json.loads(
            (Path("tests/fixtures/event/local_events.json")).read_text()
        )
        events = [converter.structure(e, Event) for e in raw_events]

        assert len(events) == len(raw_events)
        for e in events:
            assert isinstance(e, DeviceStateChangedEvent)
            assert e.device_url  # non-empty
            assert e.device_states  # non-empty

        # Local API returns already-typed values; nested object value is preserved.
        manufacturer = events[0].device_states[0]
        assert manufacturer.name == "core:ManufacturerSettingsState"
        assert manufacturer.value == {"current_position": 0}


class TestActionGroup:
    """Tests for ActionGroup and PersistedActionGroup model split."""

    def test_action_group_minimal_construction(self):
        """ActionGroup can be constructed with just actions."""
        action = Action(
            device_url="io://1234-5678-9012/12345678",
            commands=[Command(name="open")],
        )
        group = ActionGroup(actions=[action])
        assert len(group.actions) == 1
        assert group.label is None
        assert not hasattr(group, "oid")

    def test_action_group_with_label(self):
        """ActionGroup accepts an optional label."""
        group = ActionGroup(actions=[], label="my scene")
        assert group.label == "my scene"

    def test_action_group_no_oid_attribute(self):
        """ActionGroup does not have an oid attribute."""
        group = ActionGroup(actions=[])
        assert not hasattr(group, "oid")
        assert not hasattr(group, "creation_time")
        assert not hasattr(group, "last_update_time")

    def test_persisted_action_group_inherits_action_group(self):
        """PersistedActionGroup is a subclass of ActionGroup."""
        assert issubclass(PersistedActionGroup, ActionGroup)

    def test_persisted_action_group_construction(self):
        """PersistedActionGroup requires oid and has timestamp defaults."""
        group = PersistedActionGroup(
            oid="abc-123",
            actions=[],
            label="my scene",
        )
        assert group.oid == "abc-123"
        assert group.id == "abc-123"
        assert group.label == "my scene"
        assert group.creation_time == 0
        assert group.last_update_time == 0
        assert isinstance(group, ActionGroup)

    def test_persisted_action_group_isinstance_action_group(self):
        """PersistedActionGroup instances pass isinstance check for ActionGroup."""
        group = PersistedActionGroup(oid="abc-123", actions=[])
        assert isinstance(group, ActionGroup)
        assert isinstance(group, PersistedActionGroup)

    def test_persisted_action_group_id_property_returns_str(self):
        """The id property returns a str, not str | None."""
        group = PersistedActionGroup(oid="abc-123", actions=[])
        result = group.id
        assert isinstance(result, str)
        assert result == "abc-123"


def test_get_command_definition_found():
    """Device.get_command_definition() returns CommandDefinition when command exists."""
    from pyoverkiz.models import CommandDefinition

    device = _make_device(
        {
            **RAW_DEVICES,
            "definition": {
                **RAW_DEVICES["definition"],
                "commands": [{"commandName": "open", "nparams": 0}],
            },
        }
    )
    cd = device.get_command_definition("open")
    assert cd is not None
    assert isinstance(cd, CommandDefinition)
    assert cd.nparams == 0


def test_get_command_definition_not_found():
    """Device.get_command_definition() returns None when command doesn't exist."""
    device = _make_device(
        {
            **RAW_DEVICES,
            "definition": {
                **RAW_DEVICES["definition"],
                "commands": [],
            },
        }
    )
    assert device.get_command_definition("open") is None


def test_get_command_definition_empty_definition():
    """Device.get_command_definition() returns None when command is not in definition."""
    from pyoverkiz.enums import ProductType
    from pyoverkiz.models import States

    device = Device(
        attributes=States(),
        available=True,
        enabled=True,
        label="Test",
        device_url="io://1234-5678-9012/1",
        controllable_name="test",
        definition=Definition(widget_name="SomeWidget", ui_class="RollerShutter"),
        type=ProductType.ACTUATOR,
    )
    assert device.get_command_definition("open") is None
