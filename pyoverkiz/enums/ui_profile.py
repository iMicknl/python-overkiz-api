"""UI Profile enums describe device capabilities through commands and states.

THIS FILE IS AUTO-GENERATED. DO NOT EDIT MANUALLY.
Run `uv run utils/generate_enums.py` to regenerate.
"""

from enum import StrEnum, unique

from pyoverkiz.enums.base import UnknownEnumMixin


@unique
class UIProfile(UnknownEnumMixin, StrEnum):
    """UI Profiles define device capabilities through commands and states.

    Each profile describes what a device can do (commands) and what information
    it provides (states). Form factor indicates if the profile is tied to a
    specific physical device type.
    """

    UNKNOWN = "Unknown"

    #
    # AirFan
    #
    # Commands:
    #   - setFanSpeedLevel(int 0-100): Set the device fan speed level (%)
    AIR_FAN = "AirFan"

    #
    # AirFanMode
    #
    # Commands:
    #   - setFanSpeedMode(string values: 'low', 'high'): Set the device fan speed mode
    AIR_FAN_MODE = "AirFanMode"

    #
    # AirOutputLevelSensor
    #
    # States:
    #   - core:AirOutputLevelState (int 0-100): Air output level (%)
    AIR_OUTPUT_LEVEL_SENSOR = "AirOutputLevelSensor"

    #
    # AirQuality
    #
    # States:
    #   - core:GlobalAirQualityState (string values: 'bad', 'error', 'excellent', 'fair', 'good', 'poor'): Air quality status
    AIR_QUALITY = "AirQuality"

    #
    # Alarm
    #
    # Commands:
    #   - arm(): Arm the system
    #   - disarm(): Disarm the system
    ALARM = "Alarm"

    #
    # AmbientNoiseSensor
    #
    # States:
    #   - core:AmbientNoiseState (float >= 0.0): Ambient noise in dB(A)
    AMBIENT_NOISE_SENSOR = "AmbientNoiseSensor"

    #
    # BasicCloseable
    #
    # Commands:
    #   - setClosure(int 0-100): Closure level (100%=fully close, 0%=open)
    BASIC_CLOSEABLE = "BasicCloseable"

    #
    # BasicOpenClose
    #
    # Commands:
    #   - close(): Fully close the device
    #   - open(): Fully open the device
    BASIC_OPEN_CLOSE = "BasicOpenClose"

    #
    # BasicUpDown
    #
    # Commands:
    #   - down(): Move the device completely down
    #   - up(): Move the device completely up
    BASIC_UP_DOWN = "BasicUpDown"

    #
    # BatteryStatus
    #
    # States:
    #   - core:BatteryState (string values: 'verylow', 'low', 'normal', 'full'): Device battery status
    BATTERY_STATUS = "BatteryStatus"

    #
    # CO2Concentration
    #
    # States:
    #   - core:CO2ConcentrationState (float >= 0.0): Current carbon dioxide concentration (ppm)
    CO2_CONCENTRATION = "CO2Concentration"

    #
    # COConcentration
    #
    # States:
    #   - core:COConcentrationState (float >= 0.0): Current carbon monoxide concentration (ppm)
    CO_CONCENTRATION = "COConcentration"

    #
    # CODetection
    #
    # States:
    #   - core:CODetectionState (string values: 'detected', 'notDetected'): Indicate if carbon monoxide level is too high
    CO_DETECTION = "CODetection"

    #
    # CardReader
    #
    # States:
    #   - core:CardPositionState (string values: 'inserted', 'removed'): Indicate if a security card or device was inserted or detected
    CARD_READER = "CardReader"

    #
    # Closeable
    #
    # Commands:
    #   - setClosure(int 0-100): Closure level (100%=fully close, 0%=open)
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    CLOSEABLE = "Closeable"

    #
    # CloseableBlind
    #
    # Commands:
    #   - setClosure(int 0-100): Closure level (100%=fully close, 0%=open)
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # Form factor specific: Yes
    CLOSEABLE_BLIND = "CloseableBlind"

    #
    # CloseableCurtain
    #
    # Commands:
    #   - setClosure(int 0-100): Closure level (100%=fully close, 0%=open)
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # Form factor specific: Yes
    CLOSEABLE_CURTAIN = "CloseableCurtain"

    #
    # CloseableScreen
    #
    # Commands:
    #   - setClosure(int 0-100): Closure level (100%=fully close, 0%=open)
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # Form factor specific: Yes
    CLOSEABLE_SCREEN = "CloseableScreen"

    #
    # CloseableShutter
    #
    # Commands:
    #   - setClosure(int 0-100): Closure level (100%=fully close, 0%=open)
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # Form factor specific: Yes
    CLOSEABLE_SHUTTER = "CloseableShutter"

    #
    # CloseableWindow
    #
    # Commands:
    #   - setClosure(int 0-100): Closure level (100%=fully close, 0%=open)
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # Form factor specific: Yes
    CLOSEABLE_WINDOW = "CloseableWindow"

    #
    # ContactAndVibrationDetector
    #
    # States:
    #   - core:ContactState (string values: 'open', 'closed'): Contact sensor is open or closed
    #   - core:VibrationState (string values: 'detected', 'notDetected'): Indicate if strong vibrations are detected or not
    CONTACT_AND_VIBRATION_DETECTOR = "ContactAndVibrationDetector"

    #
    # ContactDetector
    #
    # States:
    #   - core:ContactState (string values: 'open', 'closed'): Contact sensor is open or closed
    CONTACT_DETECTOR = "ContactDetector"

    #
    # CoolingThermostat
    #
    # Commands:
    #   - setCoolingTargetTemperature(float 7.0-35.0): Set the cooling target temperature (manual set point)
    COOLING_THERMOSTAT = "CoolingThermostat"

    #
    # Cyclic
    #
    # Commands:
    #   - cycle(): Do a cycle of supported motion kinematics or modes
    CYCLIC = "Cyclic"

    #
    # CyclicGarageOpener
    #
    # Commands:
    #   - cycle(): Do a cycle of supported motion kinematics or modes
    #
    # Form factor specific: Yes
    CYCLIC_GARAGE_OPENER = "CyclicGarageOpener"

    #
    # CyclicGateOpener
    #
    # Commands:
    #   - cycle(): Do a cycle of supported motion kinematics or modes
    #
    # Form factor specific: Yes
    CYCLIC_GATE_OPENER = "CyclicGateOpener"

    #
    # DHWTemperature
    #
    # States:
    #   - core:DHWTemperatureState (float -100.0-100.0): Current water temperature (°C)
    DHW_TEMPERATURE = "DHWTemperature"

    #
    # DHWThermostat
    #
    # Commands:
    #   - setTargetDHWTemperature(float 38.0-60.0): Set the new water temperature to reach for a Domestic Hot Water system
    DHW_THERMOSTAT = "DHWThermostat"

    #
    # DHWThermostatTargetReader
    #
    # States:
    #   - core:TargetDHWTemperatureState (float 38.0-60.0): Domestic hot water target temperature (°C)
    DHW_THERMOSTAT_TARGET_READER = "DHWThermostatTargetReader"

    #
    # DeployUndeploy
    #
    # Commands:
    #   - deploy(): Fully deploy the device
    #   - undeploy(): Fully undeploy the device
    DEPLOY_UNDEPLOY = "DeployUndeploy"

    #
    # DeployUndeployAwning
    #
    # Commands:
    #   - deploy(): Fully deploy the device
    #   - undeploy(): Fully undeploy the device
    #
    # Form factor specific: Yes
    DEPLOY_UNDEPLOY_AWNING = "DeployUndeployAwning"

    #
    # Deployable
    #
    # Commands:
    #   - setDeployment(int 0-100): Device deployment level (100%=fully deployed, 0%=fully undeployed)
    DEPLOYABLE = "Deployable"

    #
    # DeployableAwning
    #
    # Commands:
    #   - setDeployment(int 0-100): Device deployment level (100%=fully deployed, 0%=fully undeployed)
    #
    # Form factor specific: Yes
    DEPLOYABLE_AWNING = "DeployableAwning"

    #
    # DeployableVerticalAwning
    #
    # Commands:
    #   - setDeployment(int 0-100): Device deployment level (100%=fully deployed, 0%=fully undeployed)
    #
    # Form factor specific: Yes
    DEPLOYABLE_VERTICAL_AWNING = "DeployableVerticalAwning"

    #
    # Dimmable
    #
    # Commands:
    #   - setIntensity(int 0-100): Light intensity level (100%=maximum intensity, 0%=off)
    DIMMABLE = "Dimmable"

    #
    # DoorContactSensor
    #
    # States:
    #   - core:ContactState (string values: 'open', 'closed'): Contact sensor is open or closed
    #
    # Form factor specific: Yes
    DOOR_CONTACT_SENSOR = "DoorContactSensor"

    #
    # DoorOpeningStatus
    #
    # States:
    #   - core:OpenClosedState (string values: 'open', 'closed'): Indicate if the device is open or closed
    #
    # Form factor specific: Yes
    DOOR_OPENING_STATUS = "DoorOpeningStatus"

    #
    # DualThermostat
    #
    # Commands:
    #   - setCoolingTargetTemperature(float 7.0-35.0): Set the cooling target temperature (manual set point)
    #   - setHeatingTargetTemperature(float 7.0-35.0): Set the heating target temperature (manual set point)
    DUAL_THERMOSTAT = "DualThermostat"

    #
    # ElectricCurrentMeter
    #
    # States:
    #   - core:ElectricCurrentState (float >= 0.0): Current electric current intensity (Amp)
    ELECTRIC_CURRENT_METER = "ElectricCurrentMeter"

    #
    # ElectricEnergyAndPower
    #
    # States:
    #   - core:ElectricEnergyConsumptionState (int >= 0): Electric energy consumption index (Wh)
    #   - core:ElectricPowerConsumptionState (float >= 0.0): Current electric power (W)
    ELECTRIC_ENERGY_AND_POWER = "ElectricEnergyAndPower"

    #
    # ElectricEnergyConsumption
    #
    # States:
    #   - core:ElectricEnergyConsumptionState (int >= 0): Electric energy consumption index (Wh)
    ELECTRIC_ENERGY_CONSUMPTION = "ElectricEnergyConsumption"

    #
    # ElectricPowerMeter
    #
    # States:
    #   - core:ElectricPowerConsumptionState (float >= 0.0): Current electric power (W)
    ELECTRIC_POWER_METER = "ElectricPowerMeter"

    #
    # FossilEnergyConsumption
    #
    # States:
    #   - core:FossilEnergyConsumptionState (int >= 0): Fossil energy consumption index (Wh)
    FOSSIL_ENERGY_CONSUMPTION = "FossilEnergyConsumption"

    #
    # GasConsumption
    #
    # States:
    #   - core:GasConsumptionState (float >= 0.0): Gas consumption index (m^3)
    GAS_CONSUMPTION = "GasConsumption"

    #
    # GasDetector
    #
    # States:
    #   - core:GasDetectionState (string values: 'detected', 'notDetected'): Indicate if a gas leak is detected or not
    GAS_DETECTOR = "GasDetector"

    # Generic (details unavailable)
    GENERIC = "Generic"

    #
    # HeatingLevel
    #
    # Commands:
    #   - setHeatingLevel(string values: 'comfort', 'eco'): Sets the device heating level mode
    HEATING_LEVEL = "HeatingLevel"

    #
    # IntrusionDetector
    #
    # States:
    #   - core:IntrusionState (string values: 'detected', 'notDetected'): Indicate if an intrusion was detected or not
    INTRUSION_DETECTOR = "IntrusionDetector"

    #
    # IntrusionEventDetector
    #
    # States:
    #   - core:IntrusionDetectedState (boolean): Indicate each time an intrusion was detected
    INTRUSION_EVENT_DETECTOR = "IntrusionEventDetector"

    #
    # LevelControl
    #
    # Commands:
    #   - setLevel(int 0-100): Generic device working level (0-100%) Functional meaning depends on device
    LEVEL_CONTROL = "LevelControl"

    #
    # LightDimmer
    #
    # Commands:
    #   - setIntensity(int 0-100): Light intensity level (100%=maximum intensity, 0%=off)
    #
    # Form factor specific: Yes
    LIGHT_DIMMER = "LightDimmer"

    #
    # Lock
    #
    # Commands:
    #   - lock(): Lock the device
    #   - unlock(): Unlock the device
    LOCK = "Lock"

    #
    # LockStatus
    #
    # States:
    #   - core:LockedUnlockedState (string values: 'locked', 'unlocked'): Indicate if the device is locked or unlocked
    LOCK_STATUS = "LockStatus"

    #
    # LockableOpeningStatus
    #
    # States:
    #   - core:LockedUnlockedState (string values: 'locked', 'unlocked'): Indicate if the device is locked or unlocked
    #   - core:OpenClosedState (string values: 'open', 'closed'): Indicate if the device is open or closed
    LOCKABLE_OPENING_STATUS = "LockableOpeningStatus"

    #
    # LockableTiltableOpeningStatus
    #
    # States:
    #   - core:LockedUnlockedState (string values: 'locked', 'unlocked'): Indicate if the device is locked or unlocked
    #   - core:OpenClosedState (string values: 'open', 'closed'): Indicate if the device is open or closed
    #   - core:TiltedState (boolean): Indicate if a device is titled or straight
    LOCKABLE_TILTABLE_OPENING_STATUS = "LockableTiltableOpeningStatus"

    #
    # LockableTiltableWindowOpeningStatus
    #
    # States:
    #   - core:LockedUnlockedState (string values: 'locked', 'unlocked'): Indicate if the device is locked or unlocked
    #   - core:OpenClosedState (string values: 'open', 'closed'): Indicate if the device is open or closed
    #   - core:TiltedState (boolean): Indicate if a device is titled or straight
    #
    # Form factor specific: Yes
    LOCKABLE_TILTABLE_WINDOW_OPENING_STATUS = "LockableTiltableWindowOpeningStatus"

    #
    # Luminance
    #
    # States:
    #   - core:LuminanceState (int >= 0): Current illuminance value (Lux)
    LUMINANCE = "Luminance"

    #
    # MusicPlayer
    #
    # Commands:
    #   - pause(): Pause current action
    #   - play(): Play media
    #   - setVolume(int 0-100): Set the device output volume
    MUSIC_PLAYER = "MusicPlayer"

    #
    # OccupancyDetector
    #
    # States:
    #   - core:OccupancyState (string values: 'personInside', 'noPersonInside'): Indicate if a person or motion was detected or not
    OCCUPANCY_DETECTOR = "OccupancyDetector"

    #
    # OnOffButton
    #
    # States:
    #   - core:OnOffButtonState (string values: 'on', 'off'): Position of an on/off switch
    ON_OFF_BUTTON = "OnOffButton"

    #
    # OnOffStatus
    #
    # States:
    #   - core:OnOffState (string values: 'on', 'off'): Device on/off status
    ON_OFF_STATUS = "OnOffStatus"

    #
    # OpenClose
    #
    # Commands:
    #   - close(): Fully close the device
    #   - open(): Fully open the device
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    OPEN_CLOSE = "OpenClose"

    #
    # OpenCloseBlind
    #
    # Commands:
    #   - close(): Fully close the device
    #   - open(): Fully open the device
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # Form factor specific: Yes
    OPEN_CLOSE_BLIND = "OpenCloseBlind"

    #
    # OpenCloseCameraShutter
    #
    # Commands:
    #   - close(): Fully close the device
    #   - open(): Fully open the device
    #
    # Form factor specific: Yes
    OPEN_CLOSE_CAMERA_SHUTTER = "OpenCloseCameraShutter"

    #
    # OpenCloseCurtain
    #
    # Commands:
    #   - close(): Fully close the device
    #   - open(): Fully open the device
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # Form factor specific: Yes
    OPEN_CLOSE_CURTAIN = "OpenCloseCurtain"

    #
    # OpenCloseGarageOpener
    #
    # Commands:
    #   - close(): Fully close the device
    #   - open(): Fully open the device
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # Form factor specific: Yes
    OPEN_CLOSE_GARAGE_OPENER = "OpenCloseGarageOpener"

    #
    # OpenCloseGateOpener
    #
    # Commands:
    #   - close(): Fully close the device
    #   - open(): Fully open the device
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # Form factor specific: Yes
    OPEN_CLOSE_GATE_OPENER = "OpenCloseGateOpener"

    #
    # OpenCloseScreen
    #
    # Commands:
    #   - close(): Fully close the device
    #   - open(): Fully open the device
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # Form factor specific: Yes
    OPEN_CLOSE_SCREEN = "OpenCloseScreen"

    #
    # OpenCloseShutter
    #
    # Commands:
    #   - close(): Fully close the device
    #   - open(): Fully open the device
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # Form factor specific: Yes
    OPEN_CLOSE_SHUTTER = "OpenCloseShutter"

    #
    # OpenCloseShutterSwitch
    #
    # Commands:
    #   - close(): Fully close the device
    #   - open(): Fully open the device
    #
    # Form factor specific: Yes
    OPEN_CLOSE_SHUTTER_SWITCH = "OpenCloseShutterSwitch"

    #
    # OpenCloseSlidingGateOpener
    #
    # Commands:
    #   - close(): Fully close the device
    #   - open(): Fully open the device
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # Form factor specific: Yes
    OPEN_CLOSE_SLIDING_GATE_OPENER = "OpenCloseSlidingGateOpener"

    #
    # OpenCloseSwingingShutter
    #
    # Commands:
    #   - close(): Fully close the device
    #   - open(): Fully open the device
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # Form factor specific: Yes
    OPEN_CLOSE_SWINGING_SHUTTER = "OpenCloseSwingingShutter"

    #
    # OpenCloseWindow
    #
    # Commands:
    #   - close(): Fully close the device
    #   - open(): Fully open the device
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # Form factor specific: Yes
    OPEN_CLOSE_WINDOW = "OpenCloseWindow"

    #
    # OpeningStatus
    #
    # States:
    #   - core:OpenClosedState (string values: 'open', 'closed'): Indicate if the device is open or closed
    OPENING_STATUS = "OpeningStatus"

    #
    # OperatingModeHeating
    #
    # Commands:
    #   - setOperatingMode(any): Set an operating mode
    OPERATING_MODE_HEATING = "OperatingModeHeating"

    #
    # OrientableAndCloseable
    #
    # Commands:
    #   - setClosureAndOrientation(int 0-100, int 0-100): Set both the closure level (0-100%) and relative slats orientation (0-100%) of the device
    ORIENTABLE_AND_CLOSEABLE = "OrientableAndCloseable"

    #
    # OrientableOrCloseable
    #
    # Commands:
    #   - setClosureOrOrientation(int 0-100, int 0-100): Set device closure level (0-100%), or put the device in rocking position ('rocker') and set the relative slats orientation (0-100%)
    ORIENTABLE_OR_CLOSEABLE = "OrientableOrCloseable"

    #
    # OrientablePlusCloseable
    #
    # Commands:
    #   - setClosure(int 0-100): Closure level (100%=fully close, 0%=open)
    #   - setOrientation(int 0-100): Set the relative orientation (0-100%) of the device slats
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    ORIENTABLE_PLUS_CLOSEABLE = "OrientablePlusCloseable"

    #
    # OrientableSlats
    #
    # Commands:
    #   - setOrientation(int 0-100): Set the relative orientation (0-100%) of the device slats
    ORIENTABLE_SLATS = "OrientableSlats"

    #
    # PictureCamera
    #
    # Commands:
    #   - takePicture(): Take a still picture
    PICTURE_CAMERA = "PictureCamera"

    #
    # PowerCutDetector
    #
    # States:
    #   - core:PowerCutDetectionState (string values: 'detected', 'notDetected'): Indicate if a main power cut was detected or not
    POWER_CUT_DETECTOR = "PowerCutDetector"

    #
    # PushButtonSensor
    #
    # States:
    #   - core:ButtonState (string values: 'pressed', 'released', 'shortPressed'): Indicate if a button is pressed or released
    PUSH_BUTTON_SENSOR = "PushButtonSensor"

    #
    # RainDetector
    #
    # States:
    #   - core:RainState (string values: 'detected', 'notDetected'): Indicate if rain is detected or not
    RAIN_DETECTOR = "RainDetector"

    #
    # RelativeHumidity
    #
    # States:
    #   - core:RelativeHumidityState (float 0.0-100.0): Air relative humidity (0%=totally dry, 100%=fully saturated)
    RELATIVE_HUMIDITY = "RelativeHumidity"

    #
    # RockerSwitch
    #
    # States:
    #   - core:RockerSwitchPushWayState (string values: 'heldDown', 'pressed', 'pressedX2', 'pressedX3', 'pressedX4', 'pressedX5', 'released'): Indicate when a rocker switch is pressed or released
    ROCKER_SWITCH = "RockerSwitch"

    #
    # ScenarioTrigger
    #
    # States:
    #   - core:LaunchStatusState (string values: 'launched', 'standby'): Indicates if the scene is launched or standby. "launched" value indicates that the launch conditions have been met (ex button pressed on a remote controller). "standby" value matches with an intermediate status, typically between two launch actions (ex button released on a remote controller). "launched" value should be used during a very short time and not persist across different launch events, whereas "standby" is a more stable value.
    SCENARIO_TRIGGER = "ScenarioTrigger"

    #
    # Siren
    #
    # Commands:
    #   - ring(): Ask the device to start ringing
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    SIREN = "Siren"

    #
    # SlidingPergola
    #
    # Commands:
    #   - setDeployment(int 0-100): Device deployment level (100%=fully deployed, 0%=fully undeployed)
    #
    # Form factor specific: Yes
    SLIDING_PERGOLA = "SlidingPergola"

    #
    # SmokeDetector
    #
    # States:
    #   - core:SmokeState (string values: 'detected', 'notDetected'): Indicate if smoke is detected or not
    SMOKE_DETECTOR = "SmokeDetector"

    # Specific (details unavailable)
    SPECIFIC = "Specific"

    #
    # StartStop
    #
    # Commands:
    #   - start(): Start the default actuator behavior (movement, sound or timer)
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    START_STOP = "StartStop"

    #
    # StatefulAirFan
    #
    # Commands:
    #   - setFanSpeedLevel(int 0-100): Set the device fan speed level (%)
    #
    # States:
    #   - core:FanSpeedLevelState (int 0-100): Fan speed level (%)
    STATEFUL_AIR_FAN = "StatefulAirFan"

    #
    # StatefulAlarm
    #
    # Commands:
    #   - arm(): Arm the system
    #   - disarm(): Disarm the system
    #
    # States:
    #   - core:ArmedState (boolean): Indicate if the security device is armed (true=armed)
    STATEFUL_ALARM = "StatefulAlarm"

    #
    # StatefulBasicCloseable
    #
    # Commands:
    #   - setClosure(int 0-100): Closure level (100%=fully close, 0%=open)
    #
    # States:
    #   - core:ClosureState (int 0-100): Device closure percentage (0%=fully open, 100%=fully closed)
    STATEFUL_BASIC_CLOSEABLE = "StatefulBasicCloseable"

    #
    # StatefulBasicOpenClose
    #
    # Commands:
    #   - close(): Fully close the device
    #   - open(): Fully open the device
    #
    # States:
    #   - core:OpenClosedState (string values: 'open', 'closed'): Indicate if the device is open or closed
    STATEFUL_BASIC_OPEN_CLOSE = "StatefulBasicOpenClose"

    #
    # StatefulBioClimaticPergola
    #
    # Commands:
    #   - setOrientation(int 0-100): Set the relative orientation (0-100%) of the device slats
    #
    # States:
    #   - core:SlateOrientationState (int 0-100): Slats orientation percentage (0%=not tilted,100%=maximum tilt)
    #
    # Form factor specific: Yes
    STATEFUL_BIO_CLIMATIC_PERGOLA = "StatefulBioClimaticPergola"

    #
    # StatefulCarLockWithOpeningStatus
    #
    # Commands:
    #   - lock(): Lock the device
    #   - unlock(): Unlock the device
    #
    # States:
    #   - core:LockedUnlockedState (string values: 'locked', 'unlocked'): Indicate if the device is locked or unlocked
    #   - core:OpenClosedState (string values: 'open', 'closed'): Indicate if the device is open or closed
    #
    # Form factor specific: Yes
    STATEFUL_CAR_LOCK_WITH_OPENING_STATUS = "StatefulCarLockWithOpeningStatus"

    #
    # StatefulCloseable
    #
    # Commands:
    #   - setClosure(int 0-100): Closure level (100%=fully close, 0%=open)
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # States:
    #   - core:ClosureState (int 0-100): Device closure percentage (0%=fully open, 100%=fully closed)
    STATEFUL_CLOSEABLE = "StatefulCloseable"

    #
    # StatefulCloseableAirVent
    #
    # Commands:
    #   - setClosure(int 0-100): Closure level (100%=fully close, 0%=open)
    #
    # States:
    #   - core:ClosureState (int 0-100): Device closure percentage (0%=fully open, 100%=fully closed)
    #
    # Form factor specific: Yes
    STATEFUL_CLOSEABLE_AIR_VENT = "StatefulCloseableAirVent"

    #
    # StatefulCloseableBlind
    #
    # Commands:
    #   - setClosure(int 0-100): Closure level (100%=fully close, 0%=open)
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # States:
    #   - core:ClosureState (int 0-100): Device closure percentage (0%=fully open, 100%=fully closed)
    #
    # Form factor specific: Yes
    STATEFUL_CLOSEABLE_BLIND = "StatefulCloseableBlind"

    #
    # StatefulCloseableCurtain
    #
    # Commands:
    #   - setClosure(int 0-100): Closure level (100%=fully close, 0%=open)
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # States:
    #   - core:ClosureState (int 0-100): Device closure percentage (0%=fully open, 100%=fully closed)
    #
    # Form factor specific: Yes
    STATEFUL_CLOSEABLE_CURTAIN = "StatefulCloseableCurtain"

    #
    # StatefulCloseableGarageOpener
    #
    # Commands:
    #   - setClosure(int 0-100): Closure level (100%=fully close, 0%=open)
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # States:
    #   - core:ClosureState (int 0-100): Device closure percentage (0%=fully open, 100%=fully closed)
    #
    # Form factor specific: Yes
    STATEFUL_CLOSEABLE_GARAGE_OPENER = "StatefulCloseableGarageOpener"

    #
    # StatefulCloseableGateOpener
    #
    # Commands:
    #   - setClosure(int 0-100): Closure level (100%=fully close, 0%=open)
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # States:
    #   - core:ClosureState (int 0-100): Device closure percentage (0%=fully open, 100%=fully closed)
    #
    # Form factor specific: Yes
    STATEFUL_CLOSEABLE_GATE_OPENER = "StatefulCloseableGateOpener"

    #
    # StatefulCloseableScreen
    #
    # Commands:
    #   - setClosure(int 0-100): Closure level (100%=fully close, 0%=open)
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # States:
    #   - core:ClosureState (int 0-100): Device closure percentage (0%=fully open, 100%=fully closed)
    #
    # Form factor specific: Yes
    STATEFUL_CLOSEABLE_SCREEN = "StatefulCloseableScreen"

    #
    # StatefulCloseableShutter
    #
    # Commands:
    #   - setClosure(int 0-100): Closure level (100%=fully close, 0%=open)
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # States:
    #   - core:ClosureState (int 0-100): Device closure percentage (0%=fully open, 100%=fully closed)
    #
    # Form factor specific: Yes
    STATEFUL_CLOSEABLE_SHUTTER = "StatefulCloseableShutter"

    #
    # StatefulCloseableSlidingDoor
    #
    # Commands:
    #   - setClosure(int 0-100): Closure level (100%=fully close, 0%=open)
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # States:
    #   - core:ClosureState (int 0-100): Device closure percentage (0%=fully open, 100%=fully closed)
    #
    # Form factor specific: Yes
    STATEFUL_CLOSEABLE_SLIDING_DOOR = "StatefulCloseableSlidingDoor"

    #
    # StatefulCloseableSlidingWindow
    #
    # Commands:
    #   - setClosure(int 0-100): Closure level (100%=fully close, 0%=open)
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # States:
    #   - core:ClosureState (int 0-100): Device closure percentage (0%=fully open, 100%=fully closed)
    #
    # Form factor specific: Yes
    STATEFUL_CLOSEABLE_SLIDING_WINDOW = "StatefulCloseableSlidingWindow"

    #
    # StatefulCloseableSwingingShutter
    #
    # Commands:
    #   - setClosure(int 0-100): Closure level (100%=fully close, 0%=open)
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # States:
    #   - core:ClosureState (int 0-100): Device closure percentage (0%=fully open, 100%=fully closed)
    #
    # Form factor specific: Yes
    STATEFUL_CLOSEABLE_SWINGING_SHUTTER = "StatefulCloseableSwingingShutter"

    #
    # StatefulCloseableValve
    #
    # Commands:
    #   - setClosure(int 0-100): Closure level (100%=fully close, 0%=open)
    #
    # States:
    #   - core:ClosureState (int 0-100): Device closure percentage (0%=fully open, 100%=fully closed)
    #
    # Form factor specific: Yes
    STATEFUL_CLOSEABLE_VALVE = "StatefulCloseableValve"

    #
    # StatefulCloseableWindow
    #
    # Commands:
    #   - setClosure(int 0-100): Closure level (100%=fully close, 0%=open)
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # States:
    #   - core:ClosureState (int 0-100): Device closure percentage (0%=fully open, 100%=fully closed)
    #
    # Form factor specific: Yes
    STATEFUL_CLOSEABLE_WINDOW = "StatefulCloseableWindow"

    #
    # StatefulCoolingThermostat
    #
    # Commands:
    #   - setCoolingTargetTemperature(float 7.0-35.0): Set the cooling target temperature (manual set point)
    #
    # States:
    #   - core:CoolingTargetTemperatureState (float 12.0-30.0): Room target temperature (°C) for dual heating/cooling system
    STATEFUL_COOLING_THERMOSTAT = "StatefulCoolingThermostat"

    #
    # StatefulCoolingThermostatWithSensor
    #
    # Commands:
    #   - setCoolingTargetTemperature(float 7.0-35.0): Set the cooling target temperature (manual set point)
    #
    # States:
    #   - core:CoolingTargetTemperatureState (float 12.0-30.0): Room target temperature (°C) for dual heating/cooling system
    #   - core:TemperatureState (float -100.0-100.0): Current room temperature (°C)
    STATEFUL_COOLING_THERMOSTAT_WITH_SENSOR = "StatefulCoolingThermostatWithSensor"

    #
    # StatefulDHWThermostat
    #
    # Commands:
    #   - setTargetDHWTemperature(float 38.0-60.0): Set the new water temperature to reach for a Domestic Hot Water system
    #
    # States:
    #   - core:TargetDHWTemperatureState (float 38.0-60.0): Domestic hot water target temperature (°C)
    STATEFUL_DHW_THERMOSTAT = "StatefulDHWThermostat"

    #
    # StatefulDeployUndeploy
    #
    # Commands:
    #   - deploy(): Fully deploy the device
    #   - undeploy(): Fully undeploy the device
    #
    # States:
    #   - core:DeployedUndeployedState (string values: 'deployed', 'undeployed'): Indicate if the device is deployed or not
    STATEFUL_DEPLOY_UNDEPLOY = "StatefulDeployUndeploy"

    #
    # StatefulDeployUndeployAwning
    #
    # Commands:
    #   - deploy(): Fully deploy the device
    #   - undeploy(): Fully undeploy the device
    #
    # States:
    #   - core:DeployedUndeployedState (string values: 'deployed', 'undeployed'): Indicate if the device is deployed or not
    #
    # Form factor specific: Yes
    STATEFUL_DEPLOY_UNDEPLOY_AWNING = "StatefulDeployUndeployAwning"

    #
    # StatefulDeployable
    #
    # Commands:
    #   - setDeployment(int 0-100): Device deployment level (100%=fully deployed, 0%=fully undeployed)
    #
    # States:
    #   - core:DeploymentState (int 0-100): Device deployment percentage (0%=fully retracted, 100%=fully deployed)
    STATEFUL_DEPLOYABLE = "StatefulDeployable"

    #
    # StatefulDeployableAwning
    #
    # Commands:
    #   - setDeployment(int 0-100): Device deployment level (100%=fully deployed, 0%=fully undeployed)
    #
    # States:
    #   - core:DeploymentState (int 0-100): Device deployment percentage (0%=fully retracted, 100%=fully deployed)
    #
    # Form factor specific: Yes
    STATEFUL_DEPLOYABLE_AWNING = "StatefulDeployableAwning"

    #
    # StatefulDeployableVerticalAwning
    #
    # Commands:
    #   - setDeployment(int 0-100): Device deployment level (100%=fully deployed, 0%=fully undeployed)
    #
    # States:
    #   - core:DeploymentState (int 0-100): Device deployment percentage (0%=fully retracted, 100%=fully deployed)
    #
    # Form factor specific: Yes
    STATEFUL_DEPLOYABLE_VERTICAL_AWNING = "StatefulDeployableVerticalAwning"

    #
    # StatefulDimmable
    #
    # Commands:
    #   - setIntensity(int 0-100): Light intensity level (100%=maximum intensity, 0%=off)
    #
    # States:
    #   - core:LightIntensityState (int 0-100): Light intensity percentage (0%=min intensity,100%=maximum intensity)
    STATEFUL_DIMMABLE = "StatefulDimmable"

    #
    # StatefulDoorLock
    #
    # Commands:
    #   - lock(): Lock the device
    #   - unlock(): Unlock the device
    #
    # States:
    #   - core:LockedUnlockedState (string values: 'locked', 'unlocked'): Indicate if the device is locked or unlocked
    #
    # Form factor specific: Yes
    STATEFUL_DOOR_LOCK = "StatefulDoorLock"

    #
    # StatefulDoorLockWithOpeningStatus
    #
    # Commands:
    #   - lock(): Lock the device
    #   - unlock(): Unlock the device
    #
    # States:
    #   - core:LockedUnlockedState (string values: 'locked', 'unlocked'): Indicate if the device is locked or unlocked
    #   - core:OpenClosedState (string values: 'open', 'closed'): Indicate if the device is open or closed
    #
    # Form factor specific: Yes
    STATEFUL_DOOR_LOCK_WITH_OPENING_STATUS = "StatefulDoorLockWithOpeningStatus"

    #
    # StatefulDualThermostat
    #
    # Commands:
    #   - setCoolingTargetTemperature(float 7.0-35.0): Set the cooling target temperature (manual set point)
    #   - setHeatingTargetTemperature(float 7.0-35.0): Set the heating target temperature (manual set point)
    #
    # States:
    #   - core:CoolingTargetTemperatureState (float 12.0-30.0): Room target temperature (°C) for dual heating/cooling system
    #   - core:HeatingTargetTemperatureState (float 12.0-30.0): Room target temperature (°C) for dual heating/cooling system
    STATEFUL_DUAL_THERMOSTAT = "StatefulDualThermostat"

    #
    # StatefulDualThermostatWithSensor
    #
    # Commands:
    #   - setCoolingTargetTemperature(float 7.0-35.0): Set the cooling target temperature (manual set point)
    #   - setHeatingTargetTemperature(float 7.0-35.0): Set the heating target temperature (manual set point)
    #
    # States:
    #   - core:CoolingTargetTemperatureState (float 12.0-30.0): Room target temperature (°C) for dual heating/cooling system
    #   - core:HeatingTargetTemperatureState (float 12.0-30.0): Room target temperature (°C) for dual heating/cooling system
    #   - core:TemperatureState (float -100.0-100.0): Current room temperature (°C)
    STATEFUL_DUAL_THERMOSTAT_WITH_SENSOR = "StatefulDualThermostatWithSensor"

    #
    # StatefulHeatingLevel
    #
    # Commands:
    #   - setHeatingLevel(string values: 'comfort', 'eco'): Sets the device heating level mode
    #
    # States:
    #   - core:TargetHeatingLevelState (string values: 'comfort', 'eco'): Current heating level
    STATEFUL_HEATING_LEVEL = "StatefulHeatingLevel"

    #
    # StatefulLevelControl
    #
    # Commands:
    #   - setLevel(int 0-100): Generic device working level (0-100%) Functional meaning depends on device
    #
    # States:
    #   - core:LevelState (int 0-100): Device working level percentage (0%=min level, 100%=maximum level)
    STATEFUL_LEVEL_CONTROL = "StatefulLevelControl"

    #
    # StatefulLevelControlHeating
    #
    # Commands:
    #   - setLevel(int 0-100): Generic device working level (0-100%) Functional meaning depends on device
    #
    # States:
    #   - core:LevelState (int 0-100): Device working level percentage (0%=min level, 100%=maximum level)
    #
    # Form factor specific: Yes
    STATEFUL_LEVEL_CONTROL_HEATING = "StatefulLevelControlHeating"

    #
    # StatefulLightDimmer
    #
    # Commands:
    #   - setIntensity(int 0-100): Light intensity level (100%=maximum intensity, 0%=off)
    #
    # States:
    #   - core:LightIntensityState (int 0-100): Light intensity percentage (0%=min intensity,100%=maximum intensity)
    #
    # Form factor specific: Yes
    STATEFUL_LIGHT_DIMMER = "StatefulLightDimmer"

    #
    # StatefulLock
    #
    # Commands:
    #   - lock(): Lock the device
    #   - unlock(): Unlock the device
    #
    # States:
    #   - core:LockedUnlockedState (string values: 'locked', 'unlocked'): Indicate if the device is locked or unlocked
    STATEFUL_LOCK = "StatefulLock"

    #
    # StatefulLockWithOpeningStatus
    #
    # Commands:
    #   - lock(): Lock the device
    #   - unlock(): Unlock the device
    #
    # States:
    #   - core:LockedUnlockedState (string values: 'locked', 'unlocked'): Indicate if the device is locked or unlocked
    #   - core:OpenClosedState (string values: 'open', 'closed'): Indicate if the device is open or closed
    STATEFUL_LOCK_WITH_OPENING_STATUS = "StatefulLockWithOpeningStatus"

    #
    # StatefulOpenClose
    #
    # Commands:
    #   - close(): Fully close the device
    #   - open(): Fully open the device
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # States:
    #   - core:OpenClosedState (string values: 'open', 'closed'): Indicate if the device is open or closed
    STATEFUL_OPEN_CLOSE = "StatefulOpenClose"

    #
    # StatefulOpenCloseGateOpener
    #
    # Commands:
    #   - close(): Fully close the device
    #   - open(): Fully open the device
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # States:
    #   - core:OpenClosedState (string values: 'open', 'closed'): Indicate if the device is open or closed
    #
    # Form factor specific: Yes
    STATEFUL_OPEN_CLOSE_GATE_OPENER = "StatefulOpenCloseGateOpener"

    #
    # StatefulOpenCloseShutter
    #
    # Commands:
    #   - close(): Fully close the device
    #   - open(): Fully open the device
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # States:
    #   - core:OpenClosedState (string values: 'open', 'closed'): Indicate if the device is open or closed
    #
    # Form factor specific: Yes
    STATEFUL_OPEN_CLOSE_SHUTTER = "StatefulOpenCloseShutter"

    #
    # StatefulOpenCloseSwingingShutter
    #
    # Commands:
    #   - close(): Fully close the device
    #   - open(): Fully open the device
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # States:
    #   - core:OpenClosedState (string values: 'open', 'closed'): Indicate if the device is open or closed
    #
    # Form factor specific: Yes
    STATEFUL_OPEN_CLOSE_SWINGING_SHUTTER = "StatefulOpenCloseSwingingShutter"

    #
    # StatefulOpenCloseValve
    #
    # Commands:
    #   - close(): Fully close the device
    #   - open(): Fully open the device
    #
    # States:
    #   - core:OpenClosedState (string values: 'open', 'closed'): Indicate if the device is open or closed
    #
    # Form factor specific: Yes
    STATEFUL_OPEN_CLOSE_VALVE = "StatefulOpenCloseValve"

    #
    # StatefulOperatingModeHeating
    #
    # Commands:
    #   - setOperatingMode(any): Set an operating mode
    #
    # States:
    #   - core:OperatingModeState (string values: 'antifreeze', 'auto', 'away', 'eco', 'frostprotection', 'manual', 'max', 'normal', 'off', 'on', 'prog', 'program', 'boost'): Current operating mode
    STATEFUL_OPERATING_MODE_HEATING = "StatefulOperatingModeHeating"

    #
    # StatefulOrientableAndCloseable
    #
    # Commands:
    #   - setClosureAndOrientation(int 0-100, int 0-100): Set both the closure level (0-100%) and relative slats orientation (0-100%) of the device
    #
    # States:
    #   - core:ClosureState (int 0-100): Device closure percentage (0%=fully open, 100%=fully closed)
    #   - core:SlateOrientationState (int 0-100): Slats orientation percentage (0%=not tilted,100%=maximum tilt)
    STATEFUL_ORIENTABLE_AND_CLOSEABLE = "StatefulOrientableAndCloseable"

    #
    # StatefulOrientableAndCloseableShutter
    #
    # Commands:
    #   - setClosureAndOrientation(int 0-100, int 0-100): Set both the closure level (0-100%) and relative slats orientation (0-100%) of the device
    #
    # States:
    #   - core:ClosureState (int 0-100): Device closure percentage (0%=fully open, 100%=fully closed)
    #   - core:SlateOrientationState (int 0-100): Slats orientation percentage (0%=not tilted,100%=maximum tilt)
    #
    # Form factor specific: Yes
    STATEFUL_ORIENTABLE_AND_CLOSEABLE_SHUTTER = "StatefulOrientableAndCloseableShutter"

    #
    # StatefulOrientableOrCloseable
    #
    # Commands:
    #   - setClosureOrOrientation(int 0-100, int 0-100): Set device closure level (0-100%), or put the device in rocking position ('rocker') and set the relative slats orientation (0-100%)
    #
    # States:
    #   - core:ClosureState (int 0-100): Device closure percentage (0%=fully open, 100%=fully closed)
    #   - core:SlateOrientationState (int 0-100): Slats orientation percentage (0%=not tilted,100%=maximum tilt)
    STATEFUL_ORIENTABLE_OR_CLOSEABLE = "StatefulOrientableOrCloseable"

    #
    # StatefulOrientablePlusCloseable
    #
    # Commands:
    #   - setClosure(int 0-100): Closure level (100%=fully close, 0%=open)
    #   - setOrientation(int 0-100): Set the relative orientation (0-100%) of the device slats
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # States:
    #   - core:ClosureState (int 0-100): Device closure percentage (0%=fully open, 100%=fully closed)
    #   - core:SlateOrientationState (int 0-100): Slats orientation percentage (0%=not tilted,100%=maximum tilt)
    STATEFUL_ORIENTABLE_PLUS_CLOSEABLE = "StatefulOrientablePlusCloseable"

    #
    # StatefulOrientablePlusCloseablePergola
    #
    # Commands:
    #   - setClosure(int 0-100): Closure level (100%=fully close, 0%=open)
    #   - setOrientation(int 0-100): Set the relative orientation (0-100%) of the device slats
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # States:
    #   - core:ClosureState (int 0-100): Device closure percentage (0%=fully open, 100%=fully closed)
    #   - core:SlateOrientationState (int 0-100): Slats orientation percentage (0%=not tilted,100%=maximum tilt)
    #
    # Form factor specific: Yes
    STATEFUL_ORIENTABLE_PLUS_CLOSEABLE_PERGOLA = (
        "StatefulOrientablePlusCloseablePergola"
    )

    #
    # StatefulOrientableShutter
    #
    # Commands:
    #   - setClosure(int 0-100): Closure level (100%=fully close, 0%=open)
    #   - setOrientation(int 0-100): Set the relative orientation (0-100%) of the device slats
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # States:
    #   - core:ClosureState (int 0-100): Device closure percentage (0%=fully open, 100%=fully closed)
    #   - core:SlateOrientationState (int 0-100): Slats orientation percentage (0%=not tilted,100%=maximum tilt)
    #
    # Form factor specific: Yes
    STATEFUL_ORIENTABLE_SHUTTER = "StatefulOrientableShutter"

    #
    # StatefulOrientableSlats
    #
    # Commands:
    #   - setOrientation(int 0-100): Set the relative orientation (0-100%) of the device slats
    #
    # States:
    #   - core:SlateOrientationState (int 0-100): Slats orientation percentage (0%=not tilted,100%=maximum tilt)
    STATEFUL_ORIENTABLE_SLATS = "StatefulOrientableSlats"

    #
    # StatefulRockingShutter
    #
    # Commands:
    #   - setClosureOrOrientation(int 0-100, int 0-100): Set device closure level (0-100%), or put the device in rocking position ('rocker') and set the relative slats orientation (0-100%)
    #
    # States:
    #   - core:ClosureState (int 0-100): Device closure percentage (0%=fully open, 100%=fully closed)
    #   - core:SlateOrientationState (int 0-100): Slats orientation percentage (0%=not tilted,100%=maximum tilt)
    #
    # Form factor specific: Yes
    STATEFUL_ROCKING_SHUTTER = "StatefulRockingShutter"

    #
    # StatefulSiren
    #
    # Commands:
    #   - ring(): Ask the device to start ringing
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # States:
    #   - core:OnOffState (string values: 'on', 'off'): Device on/off status
    STATEFUL_SIREN = "StatefulSiren"

    #
    # StatefulSlidingPergola
    #
    # Commands:
    #   - setDeployment(int 0-100): Device deployment level (100%=fully deployed, 0%=fully undeployed)
    #
    # States:
    #   - core:DeploymentState (int 0-100): Device deployment percentage (0%=fully retracted, 100%=fully deployed)
    #
    # Form factor specific: Yes
    STATEFUL_SLIDING_PERGOLA = "StatefulSlidingPergola"

    #
    # StatefulStartStop
    #
    # Commands:
    #   - start(): Start the default actuator behavior (movement, sound or timer)
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # States:
    #   - core:StartedStoppedState (string values: 'started', 'stopped'): Indicate if the sequence if started or stopped
    STATEFUL_START_STOP = "StatefulStartStop"

    #
    # StatefulStartStopOven
    #
    # Commands:
    #   - start(): Start the default actuator behavior (movement, sound or timer)
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # States:
    #   - core:StartedStoppedState (string values: 'started', 'stopped'): Indicate if the sequence if started or stopped
    #
    # Form factor specific: Yes
    STATEFUL_START_STOP_OVEN = "StatefulStartStopOven"

    #
    # StatefulStartStopWashingMachine
    #
    # Commands:
    #   - start(): Start the default actuator behavior (movement, sound or timer)
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #
    # States:
    #   - core:StartedStoppedState (string values: 'started', 'stopped'): Indicate if the sequence if started or stopped
    #
    # Form factor specific: Yes
    STATEFUL_START_STOP_WASHING_MACHINE = "StatefulStartStopWashingMachine"

    #
    # StatefulSwitchable
    #
    # Commands:
    #   - off(): Turn off the device
    #   - on(): Turn on the device
    #
    # States:
    #   - core:OnOffState (string values: 'on', 'off'): Device on/off status
    STATEFUL_SWITCHABLE = "StatefulSwitchable"

    #
    # StatefulSwitchableHeating
    #
    # Commands:
    #   - off(): Turn off the device
    #   - on(): Turn on the device
    #
    # States:
    #   - core:OnOffState (string values: 'on', 'off'): Device on/off status
    #
    # Form factor specific: Yes
    STATEFUL_SWITCHABLE_HEATING = "StatefulSwitchableHeating"

    #
    # StatefulSwitchableLight
    #
    # Commands:
    #   - off(): Turn off the device
    #   - on(): Turn on the device
    #
    # States:
    #   - core:OnOffState (string values: 'on', 'off'): Device on/off status
    #
    # Form factor specific: Yes
    STATEFUL_SWITCHABLE_LIGHT = "StatefulSwitchableLight"

    #
    # StatefulSwitchablePlug
    #
    # Commands:
    #   - off(): Turn off the device
    #   - on(): Turn on the device
    #
    # States:
    #   - core:OnOffState (string values: 'on', 'off'): Device on/off status
    #
    # Form factor specific: Yes
    STATEFUL_SWITCHABLE_PLUG = "StatefulSwitchablePlug"

    #
    # StatefulSwitchableVentilation
    #
    # Commands:
    #   - off(): Turn off the device
    #   - on(): Turn on the device
    #
    # States:
    #   - core:OnOffState (string values: 'on', 'off'): Device on/off status
    #
    # Form factor specific: Yes
    STATEFUL_SWITCHABLE_VENTILATION = "StatefulSwitchableVentilation"

    #
    # StatefulThermostat
    #
    # Commands:
    #   - setTargetTemperature(float 12.0-30.0): Set the new air temperature to reach
    #
    # States:
    #   - core:TargetTemperatureState (float 12.0-30.0): Room target temperature (°C)
    STATEFUL_THERMOSTAT = "StatefulThermostat"

    #
    # StatefulThermostatWithSensor
    #
    # Commands:
    #   - setTargetTemperature(float 12.0-30.0): Set the new air temperature to reach
    #
    # States:
    #   - core:TargetTemperatureState (float 12.0-30.0): Room target temperature (°C)
    #   - core:TemperatureState (float -100.0-100.0): Current room temperature (°C)
    STATEFUL_THERMOSTAT_WITH_SENSOR = "StatefulThermostatWithSensor"

    #
    # StatefulVenetianBlind
    #
    # Commands:
    #   - setClosureAndOrientation(int 0-100, int 0-100): Set both the closure level (0-100%) and relative slats orientation (0-100%) of the device
    #
    # States:
    #   - core:ClosureState (int 0-100): Device closure percentage (0%=fully open, 100%=fully closed)
    #   - core:SlateOrientationState (int 0-100): Slats orientation percentage (0%=not tilted,100%=maximum tilt)
    #
    # Form factor specific: Yes
    STATEFUL_VENETIAN_BLIND = "StatefulVenetianBlind"

    #
    # StatefulVenetianSlats
    #
    # Commands:
    #   - setOrientation(int 0-100): Set the relative orientation (0-100%) of the device slats
    #
    # States:
    #   - core:SlateOrientationState (int 0-100): Slats orientation percentage (0%=not tilted,100%=maximum tilt)
    #
    # Form factor specific: Yes
    STATEFUL_VENETIAN_SLATS = "StatefulVenetianSlats"

    #
    # StatefulWindowLockWithOpeningStatus
    #
    # Commands:
    #   - lock(): Lock the device
    #   - unlock(): Unlock the device
    #
    # States:
    #   - core:LockedUnlockedState (string values: 'locked', 'unlocked'): Indicate if the device is locked or unlocked
    #   - core:OpenClosedState (string values: 'open', 'closed'): Indicate if the device is open or closed
    #
    # Form factor specific: Yes
    STATEFUL_WINDOW_LOCK_WITH_OPENING_STATUS = "StatefulWindowLockWithOpeningStatus"

    #
    # StoppableMusicPlayer
    #
    # Commands:
    #   - pause(): Pause current action
    #   - play(): Play media
    #   - setVolume(int 0-100): Set the device output volume
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    STOPPABLE_MUSIC_PLAYER = "StoppableMusicPlayer"

    #
    # Switch
    #
    # States:
    #   - core:ActionState (string): Contains the id of current active button action (stateful information). Example, physical position of a switch.
    #   - core:AvailableActionsState (array): List of action ids available
    SWITCH = "Switch"

    #
    # SwitchEvent
    #
    # States:
    #   - core:AvailableActionsState (array): List of action ids available
    #   - core:ButtonActionsEventState (string): Contains the id of triggered button action (stateless information, makes sense only punctually at a certain time, does not indicate a stable or continuous status).
    SWITCH_EVENT = "SwitchEvent"

    #
    # Switchable
    #
    # Commands:
    #   - off(): Turn off the device
    #   - on(): Turn on the device
    SWITCHABLE = "Switchable"

    #
    # SwitchableHeating
    #
    # Commands:
    #   - off(): Turn off the device
    #   - on(): Turn on the device
    #
    # Form factor specific: Yes
    SWITCHABLE_HEATING = "SwitchableHeating"

    #
    # SwitchableHeatingStatus
    #
    # States:
    #   - core:OnOffState (string values: 'on', 'off'): Device on/off status
    #
    # Form factor specific: Yes
    SWITCHABLE_HEATING_STATUS = "SwitchableHeatingStatus"

    #
    # SwitchableLight
    #
    # Commands:
    #   - off(): Turn off the device
    #   - on(): Turn on the device
    #
    # Form factor specific: Yes
    SWITCHABLE_LIGHT = "SwitchableLight"

    #
    # SwitchablePlug
    #
    # Commands:
    #   - off(): Turn off the device
    #   - on(): Turn on the device
    #
    # Form factor specific: Yes
    SWITCHABLE_PLUG = "SwitchablePlug"

    #
    # SwitchableVentilation
    #
    # Commands:
    #   - off(): Turn off the device
    #   - on(): Turn on the device
    #
    # Form factor specific: Yes
    SWITCHABLE_VENTILATION = "SwitchableVentilation"

    #
    # Temperature
    #
    # States:
    #   - core:TemperatureState (float -100.0-100.0): Current room temperature (°C)
    TEMPERATURE = "Temperature"

    #
    # ThermalEnergyConsumption
    #
    # States:
    #   - core:ThermalEnergyConsumptionState (int >= 0): Thermal energy consumption index (Wh)
    THERMAL_ENERGY_CONSUMPTION = "ThermalEnergyConsumption"

    #
    # Thermostat
    #
    # Commands:
    #   - setTargetTemperature(float 12.0-30.0): Set the new air temperature to reach
    THERMOSTAT = "Thermostat"

    #
    # ThermostatOffsetReader
    #
    # States:
    #   - core:ThermostatOffsetState (int -5-5): Thermostat offset (°C)
    THERMOSTAT_OFFSET_READER = "ThermostatOffsetReader"

    #
    # ThermostatTargetReader
    #
    # States:
    #   - core:TargetTemperatureState (float 12.0-30.0): Room target temperature (°C)
    THERMOSTAT_TARGET_READER = "ThermostatTargetReader"

    #
    # TiltableOpeningStatus
    #
    # States:
    #   - core:OpenClosedState (string values: 'open', 'closed'): Indicate if the device is open or closed
    #   - core:TiltedState (boolean): Indicate if a device is titled or straight
    TILTABLE_OPENING_STATUS = "TiltableOpeningStatus"

    #
    # TiltableWindowOpeningStatus
    #
    # States:
    #   - core:OpenClosedState (string values: 'open', 'closed'): Indicate if the device is open or closed
    #   - core:TiltedState (boolean): Indicate if a device is titled or straight
    #
    # Form factor specific: Yes
    TILTABLE_WINDOW_OPENING_STATUS = "TiltableWindowOpeningStatus"

    #
    # TiltedStatus
    #
    # States:
    #   - core:TiltedState (boolean): Indicate if a device is titled or straight
    TILTED_STATUS = "TiltedStatus"

    #
    # UpDown
    #
    # Commands:
    #   - down(): Move the device completely down
    #   - stop(): Stop the current actuator behavior (movement, sound or timer)
    #   - up(): Move the device completely up
    UP_DOWN = "UpDown"

    #
    # UpdatableComponent
    #
    # Commands:
    #   - update(): Update the gateway software. The update may have to be downloaded first, which can take a while.
    UPDATABLE_COMPONENT = "UpdatableComponent"

    #
    # VOCConcentration
    #
    # States:
    #   - core:VOCConcentrationState (float >= 0.0): Current volatile organic compounds concentration (ppm)
    VOC_CONCENTRATION = "VOCConcentration"

    #
    # VenetianBlind
    #
    # Commands:
    #   - setClosureAndOrientation(int 0-100, int 0-100): Set both the closure level (0-100%) and relative slats orientation (0-100%) of the device
    #
    # Form factor specific: Yes
    VENETIAN_BLIND = "VenetianBlind"

    #
    # VenetianSlats
    #
    # Commands:
    #   - setOrientation(int 0-100): Set the relative orientation (0-100%) of the device slats
    #
    # Form factor specific: Yes
    VENETIAN_SLATS = "VenetianSlats"

    #
    # VibrationDetector
    #
    # States:
    #   - core:VibrationState (string values: 'detected', 'notDetected'): Indicate if strong vibrations are detected or not
    VIBRATION_DETECTOR = "VibrationDetector"

    #
    # VolumeControl
    #
    # Commands:
    #   - setVolume(int 0-100): Set the device output volume
    VOLUME_CONTROL = "VolumeControl"

    #
    # WaterConsumption
    #
    # States:
    #   - core:WaterConsumptionState (float >= 0.0): Water consumption index (m^3)
    WATER_CONSUMPTION = "WaterConsumption"

    #
    # WaterDetector
    #
    # States:
    #   - core:WaterDetectionState (string values: 'detected', 'notDetected'): Indicate if a water leak is detected or not
    WATER_DETECTOR = "WaterDetector"

    #
    # WindDirection
    #
    # States:
    #   - core:WindDirectionState (int 0-360): Wind direction (0°=North, clockwise)
    WIND_DIRECTION = "WindDirection"

    #
    # WindSpeed
    #
    # States:
    #   - core:WindSpeedState (float >= 0.0): Wind speed (km/h)
    WIND_SPEED = "WindSpeed"

    #
    # WindSpeedAndDirection
    #
    # States:
    #   - core:WindDirectionState (int 0-360): Wind direction (0°=North, clockwise)
    #   - core:WindSpeedState (float >= 0.0): Wind speed (km/h)
    WIND_SPEED_AND_DIRECTION = "WindSpeedAndDirection"

    #
    # WindowContactAndVibrationSensor
    #
    # States:
    #   - core:ContactState (string values: 'open', 'closed'): Contact sensor is open or closed
    #   - core:VibrationState (string values: 'detected', 'notDetected'): Indicate if strong vibrations are detected or not
    #
    # Form factor specific: Yes
    WINDOW_CONTACT_AND_VIBRATION_SENSOR = "WindowContactAndVibrationSensor"

    #
    # WindowOpeningStatus
    #
    # States:
    #   - core:OpenClosedState (string values: 'open', 'closed'): Indicate if the device is open or closed
    #
    # Form factor specific: Yes
    WINDOW_OPENING_STATUS = "WindowOpeningStatus"
