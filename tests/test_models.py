import humps

from pyhoma.enums import DataType
from pyhoma.models import Device, States

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
    def test_none_states(self):
        hump_device = humps.decamelize(RAW_DEVICES)
        del hump_device["states"]
        device = Device(**hump_device)
        assert not device.states.get(STATE)


class TestStates:
    def test_empty_states(self):
        states = States([])
        assert not states
        assert not states.get(STATE)

    def test_none_states(self):
        states = States(None)
        assert not states
        assert not states.get(STATE)

    def test_getter(self):
        states = States(RAW_STATES)
        state = states.get(STATE)
        assert state
        assert state.name == STATE
        assert state.type == DataType.STRING
        assert state.value == "alarm name"

    def test_getter_missing(self):
        states = States(RAW_STATES)
        state = states.get("FooState")
        assert not state
