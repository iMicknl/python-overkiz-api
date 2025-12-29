"""Unit tests for models (Device, State and States helpers)."""

# ruff: noqa: S101
# Tests use assert statements

from __future__ import annotations

import humps
import pytest

from pyoverkiz.enums import DataType, Protocol
from pyoverkiz.models import Device, State, States

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
            # Wrong device urls:
            (
                "foo://whatever-blah/12",
                Protocol.UNKNOWN,
                "whatever-blah",
                "12",
                None,
                False,
            ),
            (
                "foo://whatever",
                None,
                None,
                None,
                None,
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
        test_device = {
            **RAW_DEVICES,
            **{"deviceURL": device_url},
        }
        hump_device = humps.decamelize(test_device)
        device = Device(**hump_device)

        assert device.protocol == protocol
        assert device.gateway_id == gateway_id
        assert device.device_address == device_address
        assert device.subsystem_id == subsystem_id
        assert device.is_sub_device == is_sub_device

    def test_none_states(self):
        """Devices without a `states` field should provide an empty States object."""
        hump_device = humps.decamelize(RAW_DEVICES)
        del hump_device["states"]
        device = Device(**hump_device)
        assert not device.states.get(STATE)


class TestStates:
    """Tests for the States container behaviour and getter semantics."""

    def test_empty_states(self):
        """An empty list yields an empty States object with no state found."""
        states = States([])
        assert not states
        assert not states.get(STATE)

    def test_none_states(self):
        """A None value for states should behave as empty."""
        states = States(None)
        assert not states
        assert not states.get(STATE)

    def test_getter(self):
        """Retrieve a known state and validate its properties."""
        states = States(RAW_STATES)
        state = states.get(STATE)
        assert state
        assert state.name == STATE
        assert state.type == DataType.STRING
        assert state.value == "alarm name"

    def test_getter_missing(self):
        """Requesting a missing state returns falsy (None)."""
        states = States(RAW_STATES)
        state = states.get("FooState")
        assert not state


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
    action = Action("rts://2025-8464-6867/16756006", [cmd])

    payload = action.to_payload()

    assert payload["device_url"] == "rts://2025-8464-6867/16756006"
    assert payload["commands"][0]["name"] == "setLevel"
    assert payload["commands"][0]["type"] == 1
    # parameters should be converted to primitives (enum -> str)
    assert payload["commands"][0]["parameters"] == [10, "A"]
