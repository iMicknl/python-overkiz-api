---
hide:
  - toc
---

# UI Profiles

UI profiles describe device capabilities through the commands they accept and the states they expose. Each device has one or more profiles that define what it can do.

!!! note
    This page is auto-generated. Run `uv run utils/generate_enums.py` to regenerate.

**192 profiles** documented below.

## AirFan

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setFanSpeedLevel` | `int` (0–100) | Set the device fan speed level (%) |

## AirFanMode

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setFanSpeedMode` | `string` — `low`, `high` | Set the device fan speed mode |

## AirOutputLevelSensor

### States

| State | Type | Description |
|-------|------|-------------|
| `core:AirOutputLevelState` | `int` (0–100) | Air output level (%) |

## AirQuality

### States

| State | Type | Description |
|-------|------|-------------|
| `core:GlobalAirQualityState` | `string` — `bad`, `error`, `excellent`, `fair`, `good`, `poor` | Air quality status |

## Alarm

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `arm` |  | Arm the system |
| `disarm` |  | Disarm the system |

## AmbientNoiseSensor

### States

| State | Type | Description |
|-------|------|-------------|
| `core:AmbientNoiseState` | `float` (≥ 0.0) | Ambient noise in dB(A) |

## BasicCloseable

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosure` | `int` (0–100) | Closure level (100%=fully close, 0%=open) |

## BasicOpenClose

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `close` |  | Fully close the device |
| `open` |  | Fully open the device |

## BasicUpDown

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `down` |  | Move the device completely down |
| `up` |  | Move the device completely up |

## BatteryStatus

### States

| State | Type | Description |
|-------|------|-------------|
| `core:BatteryState` | `string` — `verylow`, `low`, `normal`, `full` | Device battery status |

## CO2Concentration

### States

| State | Type | Description |
|-------|------|-------------|
| `core:CO2ConcentrationState` | `float` (≥ 0.0) | Current carbon dioxide concentration (ppm) |

## COConcentration

### States

| State | Type | Description |
|-------|------|-------------|
| `core:COConcentrationState` | `float` (≥ 0.0) | Current carbon monoxide concentration (ppm) |

## CODetection

### States

| State | Type | Description |
|-------|------|-------------|
| `core:CODetectionState` | `string` — `detected`, `notDetected` | Indicate if carbon monoxide level is too high |

## CardReader

### States

| State | Type | Description |
|-------|------|-------------|
| `core:CardPositionState` | `string` — `inserted`, `removed` | Indicate if a security card or device was inserted or detected |

## Closeable

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosure` | `int` (0–100) | Closure level (100%=fully close, 0%=open) |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

## CloseableBlind

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosure` | `int` (0–100) | Closure level (100%=fully close, 0%=open) |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

## CloseableCurtain

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosure` | `int` (0–100) | Closure level (100%=fully close, 0%=open) |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

## CloseableScreen

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosure` | `int` (0–100) | Closure level (100%=fully close, 0%=open) |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

## CloseableShutter

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosure` | `int` (0–100) | Closure level (100%=fully close, 0%=open) |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

## CloseableWindow

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosure` | `int` (0–100) | Closure level (100%=fully close, 0%=open) |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

## ContactAndVibrationDetector

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ContactState` | `string` — `open`, `closed` | Contact sensor is open or closed |
| `core:VibrationState` | `string` — `detected`, `notDetected` | Indicate if strong vibrations are detected or not |

## ContactDetector

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ContactState` | `string` — `open`, `closed` | Contact sensor is open or closed |

## CoolingThermostat

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setCoolingTargetTemperature` | `float` (7.0–35.0) | Set the cooling target temperature (manual set point) |

## Cyclic

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `cycle` |  | Do a cycle of supported motion kinematics or modes |

## CyclicGarageOpener

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `cycle` |  | Do a cycle of supported motion kinematics or modes |

## CyclicGateOpener

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `cycle` |  | Do a cycle of supported motion kinematics or modes |

## DHWTemperature

### States

| State | Type | Description |
|-------|------|-------------|
| `core:DHWTemperatureState` | `float` (-100.0–100.0) | Current water temperature (°C) |

## DHWThermostat

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setTargetDHWTemperature` | `float` (38.0–60.0) | Set the new water temperature to reach for a Domestic Hot Water system |

## DHWThermostatTargetReader

### States

| State | Type | Description |
|-------|------|-------------|
| `core:TargetDHWTemperatureState` | `float` (38.0–60.0) | Domestic hot water target temperature (°C) |

## DeployUndeploy

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `deploy` |  | Fully deploy the device |
| `undeploy` |  | Fully undeploy the device |

## DeployUndeployAwning

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `deploy` |  | Fully deploy the device |
| `undeploy` |  | Fully undeploy the device |

## Deployable

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setDeployment` | `int` (0–100) | Device deployment level (100%=fully deployed, 0%=fully undeployed) |

## DeployableAwning

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setDeployment` | `int` (0–100) | Device deployment level (100%=fully deployed, 0%=fully undeployed) |

## DeployableVerticalAwning

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setDeployment` | `int` (0–100) | Device deployment level (100%=fully deployed, 0%=fully undeployed) |

## Dimmable

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setIntensity` | `int` (0–100) | Light intensity level (100%=maximum intensity, 0%=off) |

## DoorContactSensor

*Form factor specific* — tied to a specific physical device type.

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ContactState` | `string` — `open`, `closed` | Contact sensor is open or closed |

## DoorOpeningStatus

*Form factor specific* — tied to a specific physical device type.

### States

| State | Type | Description |
|-------|------|-------------|
| `core:OpenClosedState` | `string` — `open`, `closed` | Indicate if the device is open or closed |

## DualThermostat

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setCoolingTargetTemperature` | `float` (7.0–35.0) | Set the cooling target temperature (manual set point) |
| `setHeatingTargetTemperature` | `float` (7.0–35.0) | Set the heating target temperature (manual set point) |

## ElectricCurrentMeter

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ElectricCurrentState` | `float` (≥ 0.0) | Current electric current intensity (Amp) |

## ElectricEnergyAndPower

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ElectricEnergyConsumptionState` | `int` (≥ 0) | Electric energy consumption index (Wh) |
| `core:ElectricPowerConsumptionState` | `float` (≥ 0.0) | Current electric power (W) |

## ElectricEnergyConsumption

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ElectricEnergyConsumptionState` | `int` (≥ 0) | Electric energy consumption index (Wh) |

## ElectricPowerMeter

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ElectricPowerConsumptionState` | `float` (≥ 0.0) | Current electric power (W) |

## FossilEnergyConsumption

### States

| State | Type | Description |
|-------|------|-------------|
| `core:FossilEnergyConsumptionState` | `int` (≥ 0) | Fossil energy consumption index (Wh) |

## GasConsumption

### States

| State | Type | Description |
|-------|------|-------------|
| `core:GasConsumptionState` | `float` (≥ 0.0) | Gas consumption index (m^3) |

## GasDetector

### States

| State | Type | Description |
|-------|------|-------------|
| `core:GasDetectionState` | `string` — `detected`, `notDetected` | Indicate if a gas leak is detected or not |

## Generic

*Details unavailable.*

## HeatingLevel

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setHeatingLevel` | `string` — `comfort`, `eco` | Sets the device heating level mode |

## IntrusionDetector

### States

| State | Type | Description |
|-------|------|-------------|
| `core:IntrusionState` | `string` — `detected`, `notDetected` | Indicate if an intrusion was detected or not |

## IntrusionEventDetector

### States

| State | Type | Description |
|-------|------|-------------|
| `core:IntrusionDetectedState` | `boolean` | Indicate each time an intrusion was detected |

## LevelControl

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setLevel` | `int` (0–100) | Generic device working level (0-100%) Functional meaning depends on device |

## LightDimmer

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setIntensity` | `int` (0–100) | Light intensity level (100%=maximum intensity, 0%=off) |

## Lock

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `lock` |  | Lock the device |
| `unlock` |  | Unlock the device |

## LockStatus

### States

| State | Type | Description |
|-------|------|-------------|
| `core:LockedUnlockedState` | `string` — `locked`, `unlocked` | Indicate if the device is locked or unlocked |

## LockableOpeningStatus

### States

| State | Type | Description |
|-------|------|-------------|
| `core:LockedUnlockedState` | `string` — `locked`, `unlocked` | Indicate if the device is locked or unlocked |
| `core:OpenClosedState` | `string` — `open`, `closed` | Indicate if the device is open or closed |

## LockableTiltableOpeningStatus

### States

| State | Type | Description |
|-------|------|-------------|
| `core:LockedUnlockedState` | `string` — `locked`, `unlocked` | Indicate if the device is locked or unlocked |
| `core:OpenClosedState` | `string` — `open`, `closed` | Indicate if the device is open or closed |
| `core:TiltedState` | `boolean` | Indicate if a device is titled or straight |

## LockableTiltableWindowOpeningStatus

*Form factor specific* — tied to a specific physical device type.

### States

| State | Type | Description |
|-------|------|-------------|
| `core:LockedUnlockedState` | `string` — `locked`, `unlocked` | Indicate if the device is locked or unlocked |
| `core:OpenClosedState` | `string` — `open`, `closed` | Indicate if the device is open or closed |
| `core:TiltedState` | `boolean` | Indicate if a device is titled or straight |

## Luminance

### States

| State | Type | Description |
|-------|------|-------------|
| `core:LuminanceState` | `int` (≥ 0) | Current illuminance value (Lux) |

## MusicPlayer

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `pause` |  | Pause current action |
| `play` |  | Play media |
| `setVolume` | `int` (0–100) | Set the device output volume |

## OccupancyDetector

### States

| State | Type | Description |
|-------|------|-------------|
| `core:OccupancyState` | `string` — `personInside`, `noPersonInside` | Indicate if a person or motion was detected or not |

## OnOffButton

### States

| State | Type | Description |
|-------|------|-------------|
| `core:OnOffButtonState` | `string` — `on`, `off` | Position of an on/off switch |

## OnOffStatus

### States

| State | Type | Description |
|-------|------|-------------|
| `core:OnOffState` | `string` — `on`, `off` | Device on/off status |

## OpenClose

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `close` |  | Fully close the device |
| `open` |  | Fully open the device |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

## OpenCloseBlind

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `close` |  | Fully close the device |
| `open` |  | Fully open the device |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

## OpenCloseCameraShutter

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `close` |  | Fully close the device |
| `open` |  | Fully open the device |

## OpenCloseCurtain

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `close` |  | Fully close the device |
| `open` |  | Fully open the device |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

## OpenCloseGarageOpener

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `close` |  | Fully close the device |
| `open` |  | Fully open the device |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

## OpenCloseGateOpener

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `close` |  | Fully close the device |
| `open` |  | Fully open the device |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

## OpenCloseScreen

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `close` |  | Fully close the device |
| `open` |  | Fully open the device |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

## OpenCloseShutter

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `close` |  | Fully close the device |
| `open` |  | Fully open the device |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

## OpenCloseShutterSwitch

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `close` |  | Fully close the device |
| `open` |  | Fully open the device |

## OpenCloseSlidingGateOpener

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `close` |  | Fully close the device |
| `open` |  | Fully open the device |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

## OpenCloseSwingingShutter

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `close` |  | Fully close the device |
| `open` |  | Fully open the device |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

## OpenCloseWindow

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `close` |  | Fully close the device |
| `open` |  | Fully open the device |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

## OpeningStatus

### States

| State | Type | Description |
|-------|------|-------------|
| `core:OpenClosedState` | `string` — `open`, `closed` | Indicate if the device is open or closed |

## OperatingModeHeating

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setOperatingMode` | `any` | Set an operating mode |

## OrientableAndCloseable

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosureAndOrientation` | `int` (0–100), `int` (0–100) | Set both the closure level (0-100%) and relative slats orientation (0-100%) of the device |

## OrientableOrCloseable

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosureOrOrientation` | `int` (0–100), `int` (0–100) | Set device closure level (0-100%), or put the device in rocking position ('rocker') and set the relative slats orientation (0-100%) |

## OrientablePlusCloseable

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosure` | `int` (0–100) | Closure level (100%=fully close, 0%=open) |
| `setOrientation` | `int` (0–100) | Set the relative orientation (0-100%) of the device slats |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

## OrientableSlats

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setOrientation` | `int` (0–100) | Set the relative orientation (0-100%) of the device slats |

## PictureCamera

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `takePicture` |  | Take a still picture |

## PowerCutDetector

### States

| State | Type | Description |
|-------|------|-------------|
| `core:PowerCutDetectionState` | `string` — `detected`, `notDetected` | Indicate if a main power cut was detected or not |

## PushButtonSensor

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ButtonState` | `string` — `pressed`, `released`, `shortPressed` | Indicate if a button is pressed or released |

## RainDetector

### States

| State | Type | Description |
|-------|------|-------------|
| `core:RainState` | `string` — `detected`, `notDetected` | Indicate if rain is detected or not |

## RelativeHumidity

### States

| State | Type | Description |
|-------|------|-------------|
| `core:RelativeHumidityState` | `float` (0.0–100.0) | Air relative humidity (0%=totally dry, 100%=fully saturated) |

## RockerSwitch

### States

| State | Type | Description |
|-------|------|-------------|
| `core:RockerSwitchPushWayState` | `string` — `heldDown`, `pressed`, `pressedX2`, `pressedX3`, `pressedX4`, `pressedX5`, `released` | Indicate when a rocker switch is pressed or released |

## ScenarioTrigger

### States

| State | Type | Description |
|-------|------|-------------|
| `core:LaunchStatusState` | `string` — `launched`, `standby` | Indicates if the scene is launched or standby. "launched" value indicates that the launch conditions have been met (ex button pressed on a remote controller). "standby" value matches with an intermediate status, typically between two launch actions (ex button released on a remote controller). "launched" value should be used during a very short time and not persist across different launch events, whereas "standby" is a more stable value. |

## Siren

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `ring` |  | Ask the device to start ringing |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

## SlidingPergola

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setDeployment` | `int` (0–100) | Device deployment level (100%=fully deployed, 0%=fully undeployed) |

## SmokeDetector

### States

| State | Type | Description |
|-------|------|-------------|
| `core:SmokeState` | `string` — `detected`, `notDetected` | Indicate if smoke is detected or not |

## Specific

*Details unavailable.*

## StartStop

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `start` |  | Start the default actuator behavior (movement, sound or timer) |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

## Startable

*Details unavailable.*

## StatefulAirFan

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setFanSpeedLevel` | `int` (0–100) | Set the device fan speed level (%) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:FanSpeedLevelState` | `int` (0–100) | Fan speed level (%) |

## StatefulAlarm

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `arm` |  | Arm the system |
| `disarm` |  | Disarm the system |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ArmedState` | `boolean` | Indicate if the security device is armed (true=armed) |

## StatefulBasicCloseable

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosure` | `int` (0–100) | Closure level (100%=fully close, 0%=open) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ClosureState` | `int` (0–100) | Device closure percentage (0%=fully open, 100%=fully closed) |

## StatefulBasicOpenClose

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `close` |  | Fully close the device |
| `open` |  | Fully open the device |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:OpenClosedState` | `string` — `open`, `closed` | Indicate if the device is open or closed |

## StatefulBioClimaticPergola

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setOrientation` | `int` (0–100) | Set the relative orientation (0-100%) of the device slats |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:SlateOrientationState` | `int` (0–100) | Slats orientation percentage (0%=not tilted,100%=maximum tilt) |

## StatefulCarLockWithOpeningStatus

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `lock` |  | Lock the device |
| `unlock` |  | Unlock the device |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:LockedUnlockedState` | `string` — `locked`, `unlocked` | Indicate if the device is locked or unlocked |
| `core:OpenClosedState` | `string` — `open`, `closed` | Indicate if the device is open or closed |

## StatefulCloseable

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosure` | `int` (0–100) | Closure level (100%=fully close, 0%=open) |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ClosureState` | `int` (0–100) | Device closure percentage (0%=fully open, 100%=fully closed) |

## StatefulCloseableAirVent

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosure` | `int` (0–100) | Closure level (100%=fully close, 0%=open) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ClosureState` | `int` (0–100) | Device closure percentage (0%=fully open, 100%=fully closed) |

## StatefulCloseableBlind

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosure` | `int` (0–100) | Closure level (100%=fully close, 0%=open) |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ClosureState` | `int` (0–100) | Device closure percentage (0%=fully open, 100%=fully closed) |

## StatefulCloseableCurtain

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosure` | `int` (0–100) | Closure level (100%=fully close, 0%=open) |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ClosureState` | `int` (0–100) | Device closure percentage (0%=fully open, 100%=fully closed) |

## StatefulCloseableGarageOpener

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosure` | `int` (0–100) | Closure level (100%=fully close, 0%=open) |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ClosureState` | `int` (0–100) | Device closure percentage (0%=fully open, 100%=fully closed) |

## StatefulCloseableGateOpener

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosure` | `int` (0–100) | Closure level (100%=fully close, 0%=open) |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ClosureState` | `int` (0–100) | Device closure percentage (0%=fully open, 100%=fully closed) |

## StatefulCloseableScreen

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosure` | `int` (0–100) | Closure level (100%=fully close, 0%=open) |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ClosureState` | `int` (0–100) | Device closure percentage (0%=fully open, 100%=fully closed) |

## StatefulCloseableShutter

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosure` | `int` (0–100) | Closure level (100%=fully close, 0%=open) |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ClosureState` | `int` (0–100) | Device closure percentage (0%=fully open, 100%=fully closed) |

## StatefulCloseableSlidingDoor

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosure` | `int` (0–100) | Closure level (100%=fully close, 0%=open) |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ClosureState` | `int` (0–100) | Device closure percentage (0%=fully open, 100%=fully closed) |

## StatefulCloseableSlidingWindow

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosure` | `int` (0–100) | Closure level (100%=fully close, 0%=open) |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ClosureState` | `int` (0–100) | Device closure percentage (0%=fully open, 100%=fully closed) |

## StatefulCloseableSwingingShutter

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosure` | `int` (0–100) | Closure level (100%=fully close, 0%=open) |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ClosureState` | `int` (0–100) | Device closure percentage (0%=fully open, 100%=fully closed) |

## StatefulCloseableValve

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosure` | `int` (0–100) | Closure level (100%=fully close, 0%=open) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ClosureState` | `int` (0–100) | Device closure percentage (0%=fully open, 100%=fully closed) |

## StatefulCloseableWindow

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosure` | `int` (0–100) | Closure level (100%=fully close, 0%=open) |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ClosureState` | `int` (0–100) | Device closure percentage (0%=fully open, 100%=fully closed) |

## StatefulCoolingThermostat

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setCoolingTargetTemperature` | `float` (7.0–35.0) | Set the cooling target temperature (manual set point) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:CoolingTargetTemperatureState` | `float` (12.0–30.0) | Room target temperature (°C) for dual heating/cooling system |

## StatefulCoolingThermostatWithSensor

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setCoolingTargetTemperature` | `float` (7.0–35.0) | Set the cooling target temperature (manual set point) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:CoolingTargetTemperatureState` | `float` (12.0–30.0) | Room target temperature (°C) for dual heating/cooling system |
| `core:TemperatureState` | `float` (-100.0–100.0) | Current room temperature (°C) |

## StatefulDHWThermostat

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setTargetDHWTemperature` | `float` (38.0–60.0) | Set the new water temperature to reach for a Domestic Hot Water system |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:TargetDHWTemperatureState` | `float` (38.0–60.0) | Domestic hot water target temperature (°C) |

## StatefulDeployUndeploy

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `deploy` |  | Fully deploy the device |
| `undeploy` |  | Fully undeploy the device |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:DeployedUndeployedState` | `string` — `deployed`, `undeployed` | Indicate if the device is deployed or not |

## StatefulDeployUndeployAwning

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `deploy` |  | Fully deploy the device |
| `undeploy` |  | Fully undeploy the device |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:DeployedUndeployedState` | `string` — `deployed`, `undeployed` | Indicate if the device is deployed or not |

## StatefulDeployable

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setDeployment` | `int` (0–100) | Device deployment level (100%=fully deployed, 0%=fully undeployed) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:DeploymentState` | `int` (0–100) | Device deployment percentage (0%=fully retracted, 100%=fully deployed) |

## StatefulDeployableAwning

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setDeployment` | `int` (0–100) | Device deployment level (100%=fully deployed, 0%=fully undeployed) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:DeploymentState` | `int` (0–100) | Device deployment percentage (0%=fully retracted, 100%=fully deployed) |

## StatefulDeployableVerticalAwning

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setDeployment` | `int` (0–100) | Device deployment level (100%=fully deployed, 0%=fully undeployed) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:DeploymentState` | `int` (0–100) | Device deployment percentage (0%=fully retracted, 100%=fully deployed) |

## StatefulDimmable

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setIntensity` | `int` (0–100) | Light intensity level (100%=maximum intensity, 0%=off) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:LightIntensityState` | `int` (0–100) | Light intensity percentage (0%=min intensity,100%=maximum intensity) |

## StatefulDoorLock

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `lock` |  | Lock the device |
| `unlock` |  | Unlock the device |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:LockedUnlockedState` | `string` — `locked`, `unlocked` | Indicate if the device is locked or unlocked |

## StatefulDoorLockWithOpeningStatus

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `lock` |  | Lock the device |
| `unlock` |  | Unlock the device |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:LockedUnlockedState` | `string` — `locked`, `unlocked` | Indicate if the device is locked or unlocked |
| `core:OpenClosedState` | `string` — `open`, `closed` | Indicate if the device is open or closed |

## StatefulDualThermostat

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setCoolingTargetTemperature` | `float` (7.0–35.0) | Set the cooling target temperature (manual set point) |
| `setHeatingTargetTemperature` | `float` (7.0–35.0) | Set the heating target temperature (manual set point) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:CoolingTargetTemperatureState` | `float` (12.0–30.0) | Room target temperature (°C) for dual heating/cooling system |
| `core:HeatingTargetTemperatureState` | `float` (12.0–30.0) | Room target temperature (°C) for dual heating/cooling system |

## StatefulDualThermostatWithSensor

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setCoolingTargetTemperature` | `float` (7.0–35.0) | Set the cooling target temperature (manual set point) |
| `setHeatingTargetTemperature` | `float` (7.0–35.0) | Set the heating target temperature (manual set point) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:CoolingTargetTemperatureState` | `float` (12.0–30.0) | Room target temperature (°C) for dual heating/cooling system |
| `core:HeatingTargetTemperatureState` | `float` (12.0–30.0) | Room target temperature (°C) for dual heating/cooling system |
| `core:TemperatureState` | `float` (-100.0–100.0) | Current room temperature (°C) |

## StatefulHeatingLevel

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setHeatingLevel` | `string` — `comfort`, `eco` | Sets the device heating level mode |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:TargetHeatingLevelState` | `string` — `comfort`, `eco` | Current heating level |

## StatefulLevelControl

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setLevel` | `int` (0–100) | Generic device working level (0-100%) Functional meaning depends on device |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:LevelState` | `int` (0–100) | Device working level percentage (0%=min level, 100%=maximum level) |

## StatefulLevelControlHeating

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setLevel` | `int` (0–100) | Generic device working level (0-100%) Functional meaning depends on device |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:LevelState` | `int` (0–100) | Device working level percentage (0%=min level, 100%=maximum level) |

## StatefulLightDimmer

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setIntensity` | `int` (0–100) | Light intensity level (100%=maximum intensity, 0%=off) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:LightIntensityState` | `int` (0–100) | Light intensity percentage (0%=min intensity,100%=maximum intensity) |

## StatefulLock

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `lock` |  | Lock the device |
| `unlock` |  | Unlock the device |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:LockedUnlockedState` | `string` — `locked`, `unlocked` | Indicate if the device is locked or unlocked |

## StatefulLockWithOpeningStatus

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `lock` |  | Lock the device |
| `unlock` |  | Unlock the device |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:LockedUnlockedState` | `string` — `locked`, `unlocked` | Indicate if the device is locked or unlocked |
| `core:OpenClosedState` | `string` — `open`, `closed` | Indicate if the device is open or closed |

## StatefulOpenClose

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `close` |  | Fully close the device |
| `open` |  | Fully open the device |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:OpenClosedState` | `string` — `open`, `closed` | Indicate if the device is open or closed |

## StatefulOpenCloseGateOpener

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `close` |  | Fully close the device |
| `open` |  | Fully open the device |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:OpenClosedState` | `string` — `open`, `closed` | Indicate if the device is open or closed |

## StatefulOpenCloseShutter

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `close` |  | Fully close the device |
| `open` |  | Fully open the device |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:OpenClosedState` | `string` — `open`, `closed` | Indicate if the device is open or closed |

## StatefulOpenCloseSwimmingPoolShutter

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `close` |  | Fully close the device |
| `open` |  | Fully open the device |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:OpenClosedState` | `string` — `open`, `closed` | Indicate if the device is open or closed |

## StatefulOpenCloseSwingingShutter

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `close` |  | Fully close the device |
| `open` |  | Fully open the device |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:OpenClosedState` | `string` — `open`, `closed` | Indicate if the device is open or closed |

## StatefulOpenCloseValve

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `close` |  | Fully close the device |
| `open` |  | Fully open the device |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:OpenClosedState` | `string` — `open`, `closed` | Indicate if the device is open or closed |

## StatefulOperatingModeHeating

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setOperatingMode` | `any` | Set an operating mode |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:OperatingModeState` | `string` — `antifreeze`, `auto`, `away`, `eco`, `frostprotection`, `manual`, `max`, `normal`, `off`, `on`, `prog`, `program`, `boost` | Current operating mode |

## StatefulOrientableAndCloseable

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosureAndOrientation` | `int` (0–100), `int` (0–100) | Set both the closure level (0-100%) and relative slats orientation (0-100%) of the device |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ClosureState` | `int` (0–100) | Device closure percentage (0%=fully open, 100%=fully closed) |
| `core:SlateOrientationState` | `int` (0–100) | Slats orientation percentage (0%=not tilted,100%=maximum tilt) |

## StatefulOrientableAndCloseableShutter

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosureAndOrientation` | `int` (0–100), `int` (0–100) | Set both the closure level (0-100%) and relative slats orientation (0-100%) of the device |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ClosureState` | `int` (0–100) | Device closure percentage (0%=fully open, 100%=fully closed) |
| `core:SlateOrientationState` | `int` (0–100) | Slats orientation percentage (0%=not tilted,100%=maximum tilt) |

## StatefulOrientableOrCloseable

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosureOrOrientation` | `int` (0–100), `int` (0–100) | Set device closure level (0-100%), or put the device in rocking position ('rocker') and set the relative slats orientation (0-100%) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ClosureState` | `int` (0–100) | Device closure percentage (0%=fully open, 100%=fully closed) |
| `core:SlateOrientationState` | `int` (0–100) | Slats orientation percentage (0%=not tilted,100%=maximum tilt) |

## StatefulOrientablePlusCloseable

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosure` | `int` (0–100) | Closure level (100%=fully close, 0%=open) |
| `setOrientation` | `int` (0–100) | Set the relative orientation (0-100%) of the device slats |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ClosureState` | `int` (0–100) | Device closure percentage (0%=fully open, 100%=fully closed) |
| `core:SlateOrientationState` | `int` (0–100) | Slats orientation percentage (0%=not tilted,100%=maximum tilt) |

## StatefulOrientablePlusCloseablePergola

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosure` | `int` (0–100) | Closure level (100%=fully close, 0%=open) |
| `setOrientation` | `int` (0–100) | Set the relative orientation (0-100%) of the device slats |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ClosureState` | `int` (0–100) | Device closure percentage (0%=fully open, 100%=fully closed) |
| `core:SlateOrientationState` | `int` (0–100) | Slats orientation percentage (0%=not tilted,100%=maximum tilt) |

## StatefulOrientableShutter

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosure` | `int` (0–100) | Closure level (100%=fully close, 0%=open) |
| `setOrientation` | `int` (0–100) | Set the relative orientation (0-100%) of the device slats |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ClosureState` | `int` (0–100) | Device closure percentage (0%=fully open, 100%=fully closed) |
| `core:SlateOrientationState` | `int` (0–100) | Slats orientation percentage (0%=not tilted,100%=maximum tilt) |

## StatefulOrientableSlats

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setOrientation` | `int` (0–100) | Set the relative orientation (0-100%) of the device slats |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:SlateOrientationState` | `int` (0–100) | Slats orientation percentage (0%=not tilted,100%=maximum tilt) |

## StatefulRockingShutter

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosureOrOrientation` | `int` (0–100), `int` (0–100) | Set device closure level (0-100%), or put the device in rocking position ('rocker') and set the relative slats orientation (0-100%) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ClosureState` | `int` (0–100) | Device closure percentage (0%=fully open, 100%=fully closed) |
| `core:SlateOrientationState` | `int` (0–100) | Slats orientation percentage (0%=not tilted,100%=maximum tilt) |

## StatefulSiren

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `ring` |  | Ask the device to start ringing |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:OnOffState` | `string` — `on`, `off` | Device on/off status |

## StatefulSlidingPergola

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setDeployment` | `int` (0–100) | Device deployment level (100%=fully deployed, 0%=fully undeployed) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:DeploymentState` | `int` (0–100) | Device deployment percentage (0%=fully retracted, 100%=fully deployed) |

## StatefulStartStop

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `start` |  | Start the default actuator behavior (movement, sound or timer) |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:StartedStoppedState` | `string` — `started`, `stopped` | Indicate if the sequence if started or stopped |

## StatefulStartStopOven

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `start` |  | Start the default actuator behavior (movement, sound or timer) |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:StartedStoppedState` | `string` — `started`, `stopped` | Indicate if the sequence if started or stopped |

## StatefulStartStopWashingMachine

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `start` |  | Start the default actuator behavior (movement, sound or timer) |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:StartedStoppedState` | `string` — `started`, `stopped` | Indicate if the sequence if started or stopped |

## StatefulStartable

*Details unavailable.*

## StatefulSwitchable

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `off` |  | Turn off the device |
| `on` |  | Turn on the device |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:OnOffState` | `string` — `on`, `off` | Device on/off status |

## StatefulSwitchableHeating

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `off` |  | Turn off the device |
| `on` |  | Turn on the device |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:OnOffState` | `string` — `on`, `off` | Device on/off status |

## StatefulSwitchableLight

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `off` |  | Turn off the device |
| `on` |  | Turn on the device |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:OnOffState` | `string` — `on`, `off` | Device on/off status |

## StatefulSwitchablePlug

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `off` |  | Turn off the device |
| `on` |  | Turn on the device |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:OnOffState` | `string` — `on`, `off` | Device on/off status |

## StatefulSwitchableVentilation

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `off` |  | Turn off the device |
| `on` |  | Turn on the device |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:OnOffState` | `string` — `on`, `off` | Device on/off status |

## StatefulThermostat

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setTargetTemperature` | `float` (12.0–30.0) | Set the new air temperature to reach |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:TargetTemperatureState` | `float` (12.0–30.0) | Room target temperature (°C) |

## StatefulThermostatWithSensor

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setTargetTemperature` | `float` (12.0–30.0) | Set the new air temperature to reach |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:TargetTemperatureState` | `float` (12.0–30.0) | Room target temperature (°C) |
| `core:TemperatureState` | `float` (-100.0–100.0) | Current room temperature (°C) |

## StatefulVenetianBlind

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosureAndOrientation` | `int` (0–100), `int` (0–100) | Set both the closure level (0-100%) and relative slats orientation (0-100%) of the device |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ClosureState` | `int` (0–100) | Device closure percentage (0%=fully open, 100%=fully closed) |
| `core:SlateOrientationState` | `int` (0–100) | Slats orientation percentage (0%=not tilted,100%=maximum tilt) |

## StatefulVenetianSlats

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setOrientation` | `int` (0–100) | Set the relative orientation (0-100%) of the device slats |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:SlateOrientationState` | `int` (0–100) | Slats orientation percentage (0%=not tilted,100%=maximum tilt) |

## StatefulWindowLockWithOpeningStatus

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `lock` |  | Lock the device |
| `unlock` |  | Unlock the device |

### States

| State | Type | Description |
|-------|------|-------------|
| `core:LockedUnlockedState` | `string` — `locked`, `unlocked` | Indicate if the device is locked or unlocked |
| `core:OpenClosedState` | `string` — `open`, `closed` | Indicate if the device is open or closed |

## StoppableMusicPlayer

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `pause` |  | Pause current action |
| `play` |  | Play media |
| `setVolume` | `int` (0–100) | Set the device output volume |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |

## Switch

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ActionState` | `string` | Contains the id of current active button action (stateful information). Example, physical position of a switch. |
| `core:AvailableActionsState` | `array` | List of action ids available |

## SwitchEvent

### States

| State | Type | Description |
|-------|------|-------------|
| `core:AvailableActionsState` | `array` | List of action ids available |
| `core:ButtonActionsEventState` | `string` | Contains the id of triggered button action (stateless information, makes sense only punctually at a certain time, does not indicate a stable or continuous status). |

## Switchable

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `off` |  | Turn off the device |
| `on` |  | Turn on the device |

## SwitchableHeating

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `off` |  | Turn off the device |
| `on` |  | Turn on the device |

## SwitchableHeatingStatus

*Form factor specific* — tied to a specific physical device type.

### States

| State | Type | Description |
|-------|------|-------------|
| `core:OnOffState` | `string` — `on`, `off` | Device on/off status |

## SwitchableLight

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `off` |  | Turn off the device |
| `on` |  | Turn on the device |

## SwitchablePlug

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `off` |  | Turn off the device |
| `on` |  | Turn on the device |

## SwitchableVentilation

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `off` |  | Turn off the device |
| `on` |  | Turn on the device |

## Temperature

### States

| State | Type | Description |
|-------|------|-------------|
| `core:TemperatureState` | `float` (-100.0–100.0) | Current room temperature (°C) |

## ThermalEnergyConsumption

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ThermalEnergyConsumptionState` | `int` (≥ 0) | Thermal energy consumption index (Wh) |

## Thermostat

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setTargetTemperature` | `float` (12.0–30.0) | Set the new air temperature to reach |

## ThermostatOffsetReader

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ThermostatOffsetState` | `int` (-5–5) | Thermostat offset (°C) |

## ThermostatTargetReader

### States

| State | Type | Description |
|-------|------|-------------|
| `core:TargetTemperatureState` | `float` (12.0–30.0) | Room target temperature (°C) |

## TiltableOpeningStatus

### States

| State | Type | Description |
|-------|------|-------------|
| `core:OpenClosedState` | `string` — `open`, `closed` | Indicate if the device is open or closed |
| `core:TiltedState` | `boolean` | Indicate if a device is titled or straight |

## TiltableWindowOpeningStatus

*Form factor specific* — tied to a specific physical device type.

### States

| State | Type | Description |
|-------|------|-------------|
| `core:OpenClosedState` | `string` — `open`, `closed` | Indicate if the device is open or closed |
| `core:TiltedState` | `boolean` | Indicate if a device is titled or straight |

## TiltedStatus

### States

| State | Type | Description |
|-------|------|-------------|
| `core:TiltedState` | `boolean` | Indicate if a device is titled or straight |

## UpDown

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `down` |  | Move the device completely down |
| `stop` |  | Stop the current actuator behavior (movement, sound or timer) |
| `up` |  | Move the device completely up |

## UpdatableComponent

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `update` |  | Update the gateway software. The update may have to be downloaded first, which can take a while. |

## VOCConcentration

### States

| State | Type | Description |
|-------|------|-------------|
| `core:VOCConcentrationState` | `float` (≥ 0.0) | Current volatile organic compounds concentration (ppm) |

## VenetianBlind

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setClosureAndOrientation` | `int` (0–100), `int` (0–100) | Set both the closure level (0-100%) and relative slats orientation (0-100%) of the device |

## VenetianSlats

*Form factor specific* — tied to a specific physical device type.

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setOrientation` | `int` (0–100) | Set the relative orientation (0-100%) of the device slats |

## VibrationDetector

### States

| State | Type | Description |
|-------|------|-------------|
| `core:VibrationState` | `string` — `detected`, `notDetected` | Indicate if strong vibrations are detected or not |

## VolumeControl

### Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `setVolume` | `int` (0–100) | Set the device output volume |

## WaterConsumption

### States

| State | Type | Description |
|-------|------|-------------|
| `core:WaterConsumptionState` | `float` (≥ 0.0) | Water consumption index (m^3) |

## WaterDetector

### States

| State | Type | Description |
|-------|------|-------------|
| `core:WaterDetectionState` | `string` — `detected`, `notDetected` | Indicate if a water leak is detected or not |

## WindDirection

### States

| State | Type | Description |
|-------|------|-------------|
| `core:WindDirectionState` | `int` (0–360) | Wind direction (0°=North, clockwise) |

## WindSpeed

### States

| State | Type | Description |
|-------|------|-------------|
| `core:WindSpeedState` | `float` (≥ 0.0) | Wind speed (km/h) |

## WindSpeedAndDirection

### States

| State | Type | Description |
|-------|------|-------------|
| `core:WindDirectionState` | `int` (0–360) | Wind direction (0°=North, clockwise) |
| `core:WindSpeedState` | `float` (≥ 0.0) | Wind speed (km/h) |

## WindowContactAndVibrationSensor

*Form factor specific* — tied to a specific physical device type.

### States

| State | Type | Description |
|-------|------|-------------|
| `core:ContactState` | `string` — `open`, `closed` | Contact sensor is open or closed |
| `core:VibrationState` | `string` — `detected`, `notDetected` | Indicate if strong vibrations are detected or not |

## WindowOpeningStatus

*Form factor specific* — tied to a specific physical device type.

### States

| State | Type | Description |
|-------|------|-------------|
| `core:OpenClosedState` | `string` — `open`, `closed` | Indicate if the device is open or closed |
