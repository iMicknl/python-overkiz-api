"""Tests for UIProfileDefinition models."""

from pyoverkiz.models import (
    CommandParameter,
    UIProfileCommand,
    UIProfileDefinition,
    UIProfileState,
    ValuePrototype,
)


def test_value_prototype_with_range():
    """Test ValuePrototype with min/max range."""
    vp = ValuePrototype(type="INT", min_value=0, max_value=100)
    assert vp.type == "INT"
    assert vp.min_value == 0
    assert vp.max_value == 100
    assert vp.enum_values is None


def test_value_prototype_with_enum():
    """Test ValuePrototype with enum values."""
    vp = ValuePrototype(
        type="STRING", enum_values=["low", "high"], description="Fan speed mode"
    )
    assert vp.type == "STRING"
    assert vp.enum_values == ["low", "high"]
    assert vp.description == "Fan speed mode"


def test_command_parameter():
    """Test CommandParameter with value prototypes."""
    param = CommandParameter(
        optional=False,
        sensitive=False,
        value_prototypes=[{"type": "INT", "min_value": 0, "max_value": 100}],
    )
    assert param.optional is False
    assert param.sensitive is False
    assert len(param.value_prototypes) == 1
    assert param.value_prototypes[0].type == "INT"


def test_ui_profile_command():
    """Test UIProfileCommand with prototype."""
    cmd = UIProfileCommand(
        name="setFanSpeedLevel",
        prototype={
            "parameters": [
                {
                    "optional": False,
                    "sensitive": False,
                    "value_prototypes": [
                        {"type": "INT", "min_value": 0, "max_value": 100}
                    ],
                }
            ]
        },
        description="Set the device fan speed level",
    )
    assert cmd.name == "setFanSpeedLevel"
    assert cmd.description == "Set the device fan speed level"
    assert cmd.prototype is not None
    assert len(cmd.prototype.parameters) == 1


def test_ui_profile_state():
    """Test UIProfileState with prototype."""
    state = UIProfileState(
        name="core:TemperatureState",
        prototype={
            "value_prototypes": [
                {"type": "FLOAT", "min_value": -100.0, "max_value": 100.0}
            ]
        },
        description="Current room temperature",
    )
    assert state.name == "core:TemperatureState"
    assert state.description == "Current room temperature"
    assert state.prototype is not None
    assert len(state.prototype.value_prototypes) == 1


def test_ui_profile_definition():
    """Test complete UIProfileDefinition."""
    profile = UIProfileDefinition(
        name="AirFan",
        commands=[
            {
                "name": "setFanSpeedLevel",
                "prototype": {
                    "parameters": [
                        {
                            "optional": False,
                            "sensitive": False,
                            "value_prototypes": [
                                {"type": "INT", "min_value": 0, "max_value": 100}
                            ],
                        }
                    ]
                },
                "description": "Set fan speed",
            }
        ],
        states=[
            {
                "name": "core:FanSpeedState",
                "prototype": {
                    "value_prototypes": [
                        {"type": "INT", "min_value": 0, "max_value": 100}
                    ]
                },
                "description": "Current fan speed",
            }
        ],
        form_factor=False,
    )

    assert profile.name == "AirFan"
    assert len(profile.commands) == 1
    assert len(profile.states) == 1
    assert profile.form_factor is False

    # Verify command structure
    cmd = profile.commands[0]
    assert cmd.name == "setFanSpeedLevel"
    assert cmd.description == "Set fan speed"
    assert cmd.prototype is not None
    assert len(cmd.prototype.parameters) == 1

    # Verify state structure
    state = profile.states[0]
    assert state.name == "core:FanSpeedState"
    assert state.description == "Current fan speed"
    assert state.prototype is not None
    assert len(state.prototype.value_prototypes) == 1


def test_ui_profile_definition_minimal():
    """Test UIProfileDefinition with minimal data."""
    profile = UIProfileDefinition(name="MinimalProfile")

    assert profile.name == "MinimalProfile"
    assert profile.commands == []
    assert profile.states == []
    assert profile.form_factor is False
