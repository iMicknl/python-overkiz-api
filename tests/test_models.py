"""Unit tests for models (Device, State and States helpers)."""

from __future__ import annotations

import json
from pathlib import Path

import cattrs.errors
import pytest

from pyoverkiz._case import decamelize
from pyoverkiz.converter import converter
from pyoverkiz.enums import DataType, Protocol
from pyoverkiz.models import (
    CommandDefinitions,
    Definition,
    Device,
    EventState,
    Setup,
    State,
    StateDefinition,
    States,
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
    return converter.structure(decamelize(raw or RAW_DEVICES), Device)


class TestSetup:
    """Tests for setup-level ID parsing and redaction behavior."""

    def test_id_is_raw_but_repr_is_redacted_when_present(self):
        """When API provides `id`, keep raw value but redact it in repr output."""
        raw_setup = json.loads(
            (FIXTURES_DIR / "setup_tahoma_1.json").read_text(encoding="utf-8")
        )
        setup = converter.structure(decamelize(raw_setup), Setup)
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
        setup = converter.structure(decamelize(raw_setup), Setup)

        assert setup.id is None

    def test_id_is_none_without_input_id(self):
        """Constructing setup without an id keeps setup.id as None."""
        setup = Setup(gateways=[], devices=[])

        assert setup.id is None


class TestDevice:
    """Tests for Device model parsing and property extraction."""

    @pytest.mark.parametrize(
        "device_url, protocol, gateway_id, device_address, subsystem_id, is_sub_device",
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
        assert not device.states.get(STATE)

    def test_select_first_command(self):
        """Device.select_first_command() returns first supported command from list."""
        device = _make_device()
        assert device.select_first_command(["nonexistent", "open", "close"]) == "open"
        assert device.select_first_command(["nonexistent"]) is None

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

    def test_get_state_value(self):
        """Device.get_state_value() returns value of a single state."""
        device = _make_device()
        value = device.get_state_value("core:ClosureState")
        assert value == 100
        assert device.get_state_value("nonexistent") is None

    def test_select_first_state_value(self):
        """Device.select_first_state_value() returns value of first matching state from list."""
        device = _make_device()
        value = device.select_first_state_value(["nonexistent", "core:ClosureState"])
        assert value == 100

    def test_has_state_value(self):
        """Device.has_state_value() checks if a single state exists with non-None value."""
        device = _make_device()
        assert device.has_state_value("core:ClosureState")
        assert not device.has_state_value("nonexistent")

    def test_has_any_state_value(self):
        """Device.has_any_state_value() checks if any state exists with non-None value."""
        device = _make_device()
        assert device.has_any_state_value(["nonexistent", "core:ClosureState"])
        assert not device.has_any_state_value(["nonexistent"])

    def test_get_state_definition(self):
        """Device.get_state_definition() returns StateDefinition for a single state."""
        device = _make_device()
        state_def = device.get_state_definition("core:ClosureState")
        assert state_def is not None
        assert state_def.qualified_name == "core:ClosureState"
        assert device.get_state_definition("nonexistent") is None

    def test_select_first_state_definition(self):
        """Device.select_first_state_definition() returns first matching StateDefinition from list."""
        device = _make_device()
        state_def = device.select_first_state_definition(
            ["nonexistent", "core:ClosureState"]
        )
        assert state_def is not None
        assert state_def.qualified_name == "core:ClosureState"

    def test_get_attribute_value(self):
        """Device.get_attribute_value() returns value of a single attribute."""
        device = _make_device(
            {
                **RAW_DEVICES,
                "attributes": [
                    {"name": "core:Manufacturer", "type": 3, "value": "VELUX"},
                    {"name": "core:Model", "type": 3, "value": "WINDOW 100"},
                ],
            }
        )
        value = device.get_attribute_value("core:Model")
        assert value == "WINDOW 100"
        assert device.get_attribute_value("nonexistent") is None

    def test_select_first_attribute_value_returns_first_match(self):
        """Device.select_first_attribute_value() returns value of first matching attribute from list."""
        device = _make_device(
            {
                **RAW_DEVICES,
                "attributes": [
                    {"name": "core:Manufacturer", "type": 3, "value": "VELUX"},
                    {"name": "core:Model", "type": 3, "value": "WINDOW 100"},
                ],
            }
        )
        value = device.select_first_attribute_value(
            ["nonexistent", "core:Model", "core:Manufacturer"]
        )
        assert value == "WINDOW 100"

    def test_select_first_attribute_value_returns_none_when_no_match(self):
        """Device.select_first_attribute_value() returns None when no attribute matches."""
        device = _make_device()
        value = device.select_first_attribute_value(["nonexistent", "also_nonexistent"])
        assert value is None

    def test_select_first_attribute_value_empty_attributes(self):
        """Device.select_first_attribute_value() returns None for devices with no attributes."""
        device = _make_device({**RAW_DEVICES, "attributes": []})
        value = device.select_first_attribute_value(["core:Manufacturer"])
        assert value is None

    def test_select_first_attribute_value_with_none_values(self):
        """Device.select_first_attribute_value() skips attributes with None values."""
        device = _make_device(
            {
                **RAW_DEVICES,
                "attributes": [
                    {"name": "core:Model", "type": 3, "value": None},
                    {"name": "core:Manufacturer", "type": 3, "value": "VELUX"},
                ],
            }
        )
        value = device.select_first_attribute_value(["core:Model", "core:Manufacturer"])
        assert value == "VELUX"


class TestStates:
    """Tests for the States container behaviour and getter semantics."""

    def _make_states(self, raw: list[dict] | None = None) -> States:
        return converter.structure(raw, States)

    def test_empty_states(self):
        """An empty list yields an empty States object with no state found."""
        states = self._make_states([])
        assert not states
        assert not states.get(STATE)

    def test_none_states(self):
        """A None value for states should behave as empty."""
        states = self._make_states(None)
        assert not states
        assert not states.get(STATE)

    def test_getter(self):
        """Retrieve a known state and validate its properties."""
        states = self._make_states(RAW_STATES)
        state = states.get(STATE)
        assert state
        assert state.name == STATE
        assert state.type == DataType.STRING
        assert state.value == "alarm name"

    def test_getter_missing(self):
        """Requesting a missing state returns falsy (None)."""
        states = self._make_states(RAW_STATES)
        state = states.get("FooState")
        assert not state

    def test_select_returns_first_match(self):
        """select() returns the first state with a non-None value."""
        states = self._make_states(RAW_STATES)
        state = states.select(
            ["nonexistent", "core:NameState", "internal:AlarmDelayState"]
        )
        assert state is not None
        assert state.name == "core:NameState"

    def test_select_returns_none_when_no_match(self):
        """select() returns None when no state matches."""
        states = self._make_states(RAW_STATES)
        assert states.select(["nonexistent", "also_nonexistent"]) is None

    def test_select_value_returns_first_value(self):
        """select_value() returns the value of the first matching state."""
        states = self._make_states(RAW_STATES)
        value = states.select_value(["nonexistent", "core:NameState"])
        assert value == "alarm name"

    def test_select_value_returns_none_when_no_match(self):
        """select_value() returns None when no state matches."""
        states = self._make_states(RAW_STATES)
        assert states.select_value(["nonexistent"]) is None

    def test_has_any_true(self):
        """has_any() returns True when at least one state exists."""
        states = self._make_states(RAW_STATES)
        assert states.has_any(["nonexistent", "core:NameState"])

    def test_has_any_false(self):
        """has_any() returns False when no state exists."""
        states = self._make_states(RAW_STATES)
        assert not states.has_any(["nonexistent", "also_nonexistent"])

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

    def test_select_returns_first_match(self):
        """select() returns the first command name that exists."""
        cmds = self._make_cmds(
            [
                {"command_name": "close", "nparams": 0},
                {"command_name": "open", "nparams": 0},
                {"command_name": "setPosition", "nparams": 1},
            ]
        )
        assert cmds.select(["nonexistent", "open", "close"]) == "open"

    def test_select_returns_none_when_no_match(self):
        """select() returns None when no command matches."""
        cmds = self._make_cmds([{"command_name": "close", "nparams": 0}])
        assert cmds.select(["nonexistent", "also_nonexistent"]) is None

    def test_has_any_true(self):
        """has_any() returns True when at least one command exists."""
        cmds = self._make_cmds([{"command_name": "close", "nparams": 0}])
        assert cmds.has_any(["nonexistent", "close"])

    def test_has_any_false(self):
        """has_any() returns False when no command matches."""
        cmds = self._make_cmds([{"command_name": "close", "nparams": 0}])
        assert not cmds.has_any(["nonexistent", "also_nonexistent"])

    def test_getitem_raises_keyerror_on_missing(self):
        """Subscript access raises KeyError for missing commands."""
        cmds = self._make_cmds([{"command_name": "close", "nparams": 0}])
        with pytest.raises(KeyError, match="nonexistent"):
            cmds["nonexistent"]

    def test_getitem_returns_command_on_hit(self):
        """Subscript access returns the CommandDefinition for a known command."""
        cmds = self._make_cmds([{"command_name": "close", "nparams": 0}])
        cmd = cmds["close"]
        assert cmd.command_name == "close"

    def test_get_returns_none_on_missing(self):
        """get() returns None for missing commands."""
        cmds = self._make_cmds([{"command_name": "close", "nparams": 0}])
        assert cmds.get("nonexistent") is None

    def test_contains_existing(self):
        """'in' operator returns True for existing command names."""
        cmds = self._make_cmds([{"command_name": "close", "nparams": 0}])
        assert "close" in cmds

    def test_contains_missing(self):
        """'in' operator returns False for missing command names."""
        cmds = self._make_cmds([{"command_name": "close", "nparams": 0}])
        assert "nonexistent" not in cmds


class TestDefinition:
    """Tests for Definition model and its helper methods."""

    def test_get_state_definition_returns_first_match(self):
        """get_state_definition() returns the first StateDefinition in definition.states."""
        definition = Definition(
            commands=CommandDefinitions(),
            states=[
                StateDefinition(
                    qualified_name="core:ClosureState", type="ContinuousState"
                ),
                StateDefinition(
                    qualified_name="core:TargetClosureState", type="ContinuousState"
                ),
            ],
        )
        state_def = definition.get_state_definition(
            ["core:TargetClosureState", "core:ClosureState"]
        )
        assert state_def is not None
        assert state_def.qualified_name == "core:ClosureState"

        state_def2 = definition.get_state_definition(["core:TargetClosureState"])
        assert state_def2 is not None
        assert state_def2.qualified_name == "core:TargetClosureState"

    def test_get_state_definition_returns_none_when_no_match(self):
        """get_state_definition() returns None when no state definition matches."""
        definition = Definition(commands=CommandDefinitions(), states=[])
        assert definition.get_state_definition(["nonexistent"]) is None

    def test_has_state_definition_returns_true(self):
        """has_state_definition() returns True when a state definition matches."""
        definition = Definition(
            commands=CommandDefinitions(),
            states=[
                StateDefinition(
                    qualified_name="core:ClosureState", type="ContinuousState"
                ),
                StateDefinition(
                    qualified_name="core:TargetClosureState", type="ContinuousState"
                ),
            ],
        )
        assert definition.has_state_definition(["core:ClosureState"])
        assert definition.has_state_definition(
            ["nonexistent", "core:TargetClosureState"]
        )

    def test_has_state_definition_returns_false(self):
        """has_state_definition() returns False when no state definition matches."""
        definition = Definition(
            commands=CommandDefinitions(),
            states=[
                StateDefinition(
                    qualified_name="core:ClosureState", type="ContinuousState"
                ),
            ],
        )
        assert not definition.has_state_definition(["nonexistent", "also_nonexistent"])

    def test_has_state_definition_empty_states(self):
        """has_state_definition() returns False for definitions with no states."""
        definition = Definition(commands=CommandDefinitions(), states=[])
        assert not definition.has_state_definition(["core:ClosureState"])


class TestStateDefinition:
    """Tests for StateDefinition initialization behavior."""

    def test_requires_name_or_qualified_name(self):
        """StateDefinition should reject payloads with neither identifier field."""
        with pytest.raises(
            ValueError,
            match=r"StateDefinition requires either `name` or `qualified_name`\.",
        ):
            StateDefinition()


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
            assert state.value_as_int

    def test_float_value(self):
        """Float typed state returns proper float accessor."""
        state = State(name="state", type=DataType.FLOAT, value=1.0)
        assert state.value_as_float == 1.0

    def test_bad_float_value(self):
        """Accessor raises TypeError if the state type mismatches expected float."""
        state = State(name="state", type=DataType.BOOLEAN, value=False)
        with pytest.raises(TypeError):
            assert state.value_as_float

    def test_bool_value(self):
        """Boolean typed state returns proper boolean accessor."""
        state = State(name="state", type=DataType.BOOLEAN, value=True)
        assert state.value_as_bool

    def test_bad_bool_value(self):
        """Accessor raises TypeError if the state type mismatches expected bool."""
        state = State(name="state", type=DataType.INTEGER, value=1)
        with pytest.raises(TypeError):
            assert state.value_as_bool

    def test_str_value(self):
        """String typed state returns proper string accessor."""
        state = State(name="state", type=DataType.STRING, value="foo")
        assert state.value_as_str == "foo"

    def test_bad_str_value(self):
        """Accessor raises TypeError if the state type mismatches expected string."""
        state = State(name="state", type=DataType.BOOLEAN, value=False)
        with pytest.raises(TypeError):
            assert state.value_as_str

    def test_dict_value(self):
        """JSON object typed state returns proper dict accessor."""
        state = State(name="state", type=DataType.JSON_OBJECT, value={"foo": "bar"})
        assert state.value_as_dict == {"foo": "bar"}

    def test_bad_dict_value(self):
        """Accessor raises TypeError if the state type mismatches expected dict."""
        state = State(name="state", type=DataType.BOOLEAN, value=False)
        with pytest.raises(TypeError):
            assert state.value_as_dict

    def test_list_value(self):
        """JSON array typed state returns proper list accessor."""
        state = State(name="state", type=DataType.JSON_ARRAY, value=[1, 2])
        assert state.value_as_list == [1, 2]

    def test_bad_list_value(self):
        """Accessor raises TypeError if the state type mismatches expected list."""
        state = State(name="state", type=DataType.BOOLEAN, value=False)
        with pytest.raises(TypeError):
            assert state.value_as_list


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


def test_command_to_payload_omits_none():
    """Command.to_payload omits None fields from the resulting payload."""
    from pyoverkiz.enums.command import OverkizCommand
    from pyoverkiz.models import Command

    cmd = Command(name=OverkizCommand.CLOSE, parameters=None, type=None)
    payload = cmd.to_payload()

    assert payload == {"name": "close"}


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
