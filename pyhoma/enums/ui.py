from enum import Enum, unique


@unique
class UIClass(str, Enum):
    # A list of all defined UI classes from /reference/ui/classes
    ADJUSTABLE_SLATS_ROLLER_SHUTTER = "AdjustableSlatsRollerShutter"
    AIR_SENSOR = "AirSensor"
    ALARM = "Alarm"
    AWNING = "Awning"
    BALLAST = "Ballast"
    CAMERA = "Camera"
    CAR_BUTTON_SENSOR = "CarButtonSensor"
    CIRCUIT_BREAKER = "CircuitBreaker"
    CONFIGURATION_COMPONENT = "ConfigurationComponent"
    CONSUMPTION_SENSOR = "ConsumptionSensor"
    CONTACT_SENSOR = "ContactSensor"
    CURTAIN = "Curtain"
    DOCK = "Dock"
    DOOR_LOCK = "DoorLock"
    ELECTRICITY_SENSOR = "ElectricitySensor"
    EVO_HOME = "EvoHome"
    EXTERIOR_HEATING_SYSTEM = "ExteriorHeatingSystem"
    EXTERIOR_SCREEN = "ExteriorScreen"
    EXTERIOR_VENETIAN_BLIND = "ExteriorVenetianBlind"
    GARAGE_DOOR = "GarageDoor"
    GAS_SENSOR = "GasSensor"
    GATE = "Gate"
    GENERIC = "Generic"
    GENERIC_SENSOR = "GenericSensor"
    GROUP_CONFIGURATION = "GroupConfiguration"
    HEAT_PUMP_SYSTEM = "HeatPumpSystem"
    HEATING_SYSTEM = "HeatingSystem"
    HITACHI_HEATING_SYSTEM = "HitachiHeatingSystem"
    HUMIDITY_SENSOR = "HumiditySensor"
    IR_BLASTER_CONTROLLER = "IRBlasterController"
    INTRUSION_SENSOR = "IntrusionSensor"
    LIGHT = "Light"
    LIGHT_SENSOR = "LightSensor"
    MUSIC_PLAYER = "MusicPlayer"
    NETWORK_COMPONENT = "NetworkComponent"
    OCCUPANCY_SENSOR = "OccupancySensor"
    ON_OFF = "OnOff"
    OVEN = "Oven"
    PERGOLA = "Pergola"
    POD = "Pod"
    PROTOCOL_GATEWAY = "ProtocolGateway"
    RAIN_SENSOR = "RainSensor"
    REMOTE_CONTROLLER = "RemoteController"
    ROLLER_SHUTTER = "RollerShutter"
    SCREEN = "Screen"
    SHUTTER = "Shutter"
    SIREN = "Siren"
    SMOKE_SENSOR = "SmokeSensor"
    SUN_INTENSITY_SENSOR = "SunIntensitySensor"
    SUN_SENSOR = "SunSensor"
    SWIMMING_POOL = "SwimmingPool"
    SWINGING_SHUTTER = "SwingingShutter"
    TEMPERATURE_SENSOR = "TemperatureSensor"
    THERMAL_ENERGY_SENSOR = "ThermalEnergySensor"
    THIRD_PARTY_GATEWAY = "ThirdPartyGateway"
    VENETIAN_BLIND = "VenetianBlind"
    VENTILATION_SYTEM = "VentilationSystem"
    WASHING_MACHINE = "WashingMachine"
    WATER_HEATING_SYSTEM = "WaterHeatingSystem"
    WATER_SENSOR = "WaterSensor"
    WEATHER_SENSOR = "WeatherSensor"
    WIFI = "Wifi"
    WIND_SENSOR = "WindSensor"
    WINDOW = "Window"
    WINDOW_HANDLE = "WindowHandle"


@unique
class UIWidget(str, Enum):
    # A list of all defined UI widgets from /reference/ui/widgets
    AIR_FLOW_SENSOR = "AirFlowSensor"
    AIR_QUALITY_SENSOR = "AirQualitySensor"
    ALARM_PANEL_CONTROLLER = "AlarmPanelController"
    ALARM_REMOTE_CONTROLLER = "AlarmRemoteController"
    ATLANTIC_ELECTRICAL_HEATER = "AtlanticElectricalHeater"
    ATLANTIC_ELECTRICAL_HEATER_WITH_ADJUSTABLE_TEMPERATURE_SETPOINT = (
        "AtlanticElectricalHeaterWithAdjustableTemperatureSetpoint"
    )
    ATLANTIC_ELECTRICAL_TOWEL_DRYER = "AtlanticElectricalTowelDryer"
    ATLANTIC_HEAT_RECOVERY_VENTILATION = "AtlanticHeatRecoveryVentilation"
    ATLANTIC_MULTI_METER_ELECTRIC_CONFIGURATION = (
        "AtlanticMultiMeterElectricConfiguration"
    )
    ATLANTIC_MULTI_METER_ELECTRIC_HEAT_PUMP = "AtlanticMultiMeterElectricHeatPump"
    ATLANTIC_MULTI_METER_ELECTRIC_SENSOR = "AtlanticMultiMeterElectricSensor"
    ATLANTIC_PASS_APC_BOILER = "AtlanticPassAPCBoiler"
    ATLANTIC_PASS_APC_DHW = "AtlanticPassAPCDHW"
    ATLANTIC_PASS_APC_HEAT_PUMP = "AtlanticPassAPCHeatPump"
    ATLANTIC_PASS_APC_HEATING_AND_COOLING_ZONE = "AtlanticPassAPCHeatingAndCoolingZone"
    ATLANTIC_PASS_APC_HEATING_ZONE = "AtlanticPassAPCHeatingZone"
    ATLANTIC_PASS_APC_ZONE_CONTROL = "AtlanticPassAPCZoneControl"
    AWNING_VALANCE = "AwningValance"
    BALLAST = "Ballast"
    BATTERY_SENSOR = "BatterySensor"
    BIOCLIMATIC_PERGOLA = "BioclimaticPergola"
    CO2_SENSOR = "CO2Sensor"
    COSENSOR = "COSensor"
    CAR_BUTTON_SENSOR = "CarButtonSensor"
    CAR_LOCK = "CarLock"
    CARD_SWITCH = "CardSwitch"
    CIRCUIT_BREAKER = "CircuitBreaker"
    CONTACT_SENSOR = "ContactSensor"
    COTHERM_THERMOSTAT = "CothermThermostat"
    CUMULATIVE_ELECTRIC_POWER_CONSUMPTION_SENSOR = (
        "CumulativeElectricPowerConsumptionSensor"
    )
    CUMULATIVE_ELECTRIC_POWER_PRODUCTION_SENSOR = (
        "CumulativeElectricPowerProductionSensor"
    )
    CUMULATIVE_FOSSIL_ENERGY_CONSUMPTION_SENSOR = (
        "CumulativeFossilEnergyConsumptionSensor"
    )
    CUMULATIVE_GAS_CONSUMPTION_SENSOR = "CumulativeGasConsumptionSensor"
    CUMULATIVE_THERMAL_ENERGY_CONSUMPTION_SENSOR = (
        "CumulativeThermalEnergyConsumptionSensor"
    )
    CUMULATIVE_WATER_CONSUMPTION_SENSOR = "CumulativeWaterConsumptionSensor"
    CURTAIN_TRACK_UNO = "CurtainTrackUno"
    CYCLIC_GENERIC = "CyclicGeneric"
    DHW_SET_POINT = "DHWSetPoint"
    DE_DIETRICH_BOILER = "DeDietrichBoiler"
    DE_DIETRICH_DHW = "DeDietrichDHW"
    DE_DIETRICH_HEATING_CIRCUIT = "DeDietrichHeatingCircuit"
    DE_DIETRICH_MODBUS_GATEWAY = "DeDietrichModbusGateway"
    DE_DIETRICH_SWIMMING_POOL = "DeDietrichSwimmingPool"
    DIMMER_CIECOLOR_SPACE_XYLIGHT = "DimmerCIEColorSpaceXYLight"
    DIMMER_COLOR_TEMPERATURE_LIGHT = "DimmerColorTemperatureLight"
    DIMMER_EXTERIOR_HEATING = "DimmerExteriorHeating"
    DIMMER_HUE_SAT_OR_CTLIGHT = "DimmerHueSatOrCTLight"
    DIMMER_HUE_SATURATION_LIGHT = "DimmerHueSaturationLight"
    DIMMER_LIGHT = "DimmerLight"
    DIMMER_ON_OFF = "DimmerOnOff"
    DIMMER_ON_OFF_LIGHT = "DimmerOnOffLight"
    DIMMER_RGBCOLOURED_LIGHT = "DimmerRGBColouredLight"
    DIMPLEX_VENTILATION_INLET_OUTLET = "DimplexVentilationInletOutlet"
    DISCRETE_EXTERIOR_HEATING = "DiscreteExteriorHeating"
    DISCRETE_POSITIONABLE_GARAGE_DOOR = "DiscretePositionableGarageDoor"
    DISCRETE_POSITIONABLE_GATE = "DiscretePositionableGate"
    DOCK = "Dock"
    DOMESTIC_HOT_WATER_PRODUCTION = "DomesticHotWaterProduction"
    DOMESTIC_HOT_WATER_TANK = "DomesticHotWaterTank"
    DOOR_LOCK = "DoorLock"
    DROP_ARM_AWNING = "DropArmAwning"
    DYNAMIC_AIR_VENT = "DynamicAirVent"
    DYNAMIC_ALARM = "DynamicAlarm"
    DYNAMIC_AWNING = "DynamicAwning"
    DYNAMIC_BRIDGE = "DynamicBridge"
    DYNAMIC_CIRCUIT_BREAKER = "DynamicCircuitBreaker"
    DYNAMIC_CURTAIN = "DynamicCurtain"
    DYNAMIC_GARAGE_DOOR = "DynamicGarageDoor"
    DYNAMIC_GATE = "DynamicGate"
    DYNAMIC_GATEWAY = "DynamicGateway"
    DYNAMIC_HEATER = "DynamicHeater"
    DYNAMIC_HUMIDITY_SENSOR = "DynamicHumiditySensor"
    DYNAMIC_HVAC_CENTRAL_UNIT = "DynamicHvacCentralUnit"
    DYNAMIC_INTRUSION_SENSOR = "DynamicIntrusionSensor"
    DYNAMIC_LIGHT = "DynamicLight"
    DYNAMIC_LIGHT_SENSOR = "DynamicLightSensor"
    DYNAMIC_OCCUPANCY_SENSOR = "DynamicOccupancySensor"
    DYNAMIC_OPENING_SENSOR = "DynamicOpeningSensor"
    DYNAMIC_OUTLET = "DynamicOutlet"
    DYNAMIC_OVEN = "DynamicOven"
    DYNAMIC_PERGOLA = "DynamicPergola"
    DYNAMIC_RAIN_SENSOR = "DynamicRainSensor"
    DYNAMIC_SCREEN = "DynamicScreen"
    DYNAMIC_SHUTTER = "DynamicShutter"
    DYNAMIC_TEMPERATURE_SENSOR = "DynamicTemperatureSensor"
    DYNAMIC_THERMOSTAT = "DynamicThermostat"
    DYNAMIC_THIRD_PARTY_GATEWAY = "DynamicThirdPartyGateway"
    DYNAMIC_VENETIAN_BLIND = "DynamicVenetianBlind"
    DYNAMIC_VENTILATION = "DynamicVentilation"
    DYNAMIC_WASHING_MACHINE = "DynamicWashingMachine"
    DYNAMIC_WEATHER_STATION = "DynamicWeatherStation"
    DYNAMIC_WIND_SENSOR = "DynamicWindSensor"
    DYNAMIC_WINDOW = "DynamicWindow"
    ELECTRICAL_HEATER = "ElectricalHeater"
    ELECTRICAL_HEATER_WITH_ADJUSTABLE_TEMPERATURE_SETPOINT = (
        "ElectricalHeaterWithAdjustableTemperatureSetpoint"
    )
    EMPTY_REMOTE_CONTROLLER = "EmptyRemoteController"
    EN_OCEAN_GENERIC = "EnOceanGeneric"
    EN_OCEAN_GENERIC_ELECTRIC_COUNTER = "EnOceanGenericElectricCounter"
    EN_OCEAN_TRANSCEIVER = "EnOceanTransceiver"
    EVO_HOME_CONTROLLER = "EvoHomeController"
    EWATTCH_TICCOUNTER = "EwattchTICCounter"
    EXTERIOR_VENETIAN_BLIND = "ExteriorVenetianBlind"
    FLOOR_HEATING = "FloorHeating"
    GAS_DHW_CONSUMPTION_SENSOR = "GasDHWConsumptionSensor"
    GAS_HEATER_CONSUMPTION_SENSOR = "GasHeaterConsumptionSensor"
    GENERIC_16_CHANNELS_COUNTER = "Generic16ChannelsCounter"
    GENERIC_1_CHANNEL_COUNTER = "Generic1ChannelCounter"
    GENERIC_CAMERA = "GenericCamera"
    GROUP_CONFIGURATION = "GroupConfiguration"
    HEAT_DETECTION_SENSOR = "HeatDetectionSensor"
    HEAT_PUMP = "HeatPump"
    HEATING_SET_POINT = "HeatingSetPoint"
    HEATING_TEMPERATURE_INTERFACE = "HeatingTemperatureInterface"
    HITACHI_AIR_TO_AIR_HEAT_PUMP = "HitachiAirToAirHeatPump"
    HITACHI_AIR_TO_WATER_HEATING_ZONE = "HitachiAirToWaterHeatingZone"
    HITACHI_AIR_TO_WATER_MAIN_COMPONENT = "HitachiAirToWaterMainComponent"
    HITACHI_DHW = "HitachiDHW"
    HITACHI_SWIMMING_POOL = "HitachiSwimmingPool"
    HITACHI_THERMOSTAT = "HitachiThermostat"
    HOMEKIT_STACK = "HomekitStack"
    HUE_BRIDGE = "HueBridge"
    IOGENERIC = "IOGeneric"
    IOSIREN = "IOSiren"
    IOSTACK = "IOStack"
    IRBLASTER = "IRBlaster"
    IMHOTEP_HEATING_TEMPERATURE_INTERFACE = "ImhotepHeatingTemperatureInterface"
    INSTANT_ELECTRIC_CURRENT_CONSUMPTION_SENSOR = (
        "InstantElectricCurrentConsumptionSensor"
    )
    INSTANT_ELECTRIC_POWER_CONSUMPTION_SENSOR = "InstantElectricPowerConsumptionSensor"
    INTRUSION_DETECTOR = "IntrusionDetector"
    INTRUSION_EVENT_SENSOR = "IntrusionEventSensor"
    INTRUSION_SENSOR = "IntrusionSensor"
    INVALID = "Invalid"
    JSWCAMERA = "JSWCamera"
    KIZ_OTHERM_BRIDGE = "KizOThermBridge"
    KIZ_OTHERM_V2_BRIDGE = "KizOThermV2Bridge"
    LOCK_UNLOCK_DOOR_LOCK_WITH_UNKNOWN_POSITION = (
        "LockUnlockDoorLockWithUnknownPosition"
    )
    LUMINANCE_SENSOR = "LuminanceSensor"
    MEDIA_RENDERER = "MediaRenderer"
    MOTION_SENSOR = "MotionSensor"
    MULTI_METER_ELECTRIC_SENSOR = "MultiMeterElectricSensor"
    MY_FOX_ALARM_CONTROLLER = "MyFoxAlarmController"
    MY_FOX_CAMERA = "MyFoxCamera"
    MY_FOX_SECURITY_CAMERA = "MyFoxSecurityCamera"
    NODE = "Node"
    OVPGENERIC = "OVPGeneric"
    OCCUPANCY_SENSOR = "OccupancySensor"
    ON_OFF_HEATING_SYSTEM = "OnOffHeatingSystem"
    ON_OFF_LIGHT = "OnOffLight"
    ON_OFF_REMOTECONTROLLER = "OnOffRemotecontroller"
    OPEN_CLOSE_GATE = "OpenCloseGate"
    OPEN_CLOSE_GATE_4T = "OpenCloseGate4T"
    OPEN_CLOSE_GATE_WITH_PEDESTRIAN_POSITION = "OpenCloseGateWithPedestrianPosition"
    OPEN_CLOSE_SLIDING_GARAGE_DOOR = "OpenCloseSlidingGarageDoor"
    OPEN_CLOSE_SLIDING_GARAGE_DOOR_4T = "OpenCloseSlidingGarageDoor4T"
    OPEN_CLOSE_SLIDING_GARAGE_DOOR_WITH_PEDESTRIAN_POSITION = (
        "OpenCloseSlidingGarageDoorWithPedestrianPosition"
    )
    OPEN_CLOSE_SLIDING_GATE = "OpenCloseSlidingGate"
    OPEN_CLOSE_SLIDING_GATE_4T = "OpenCloseSlidingGate4T"
    OPEN_CLOSE_SLIDING_GATE_WITH_PEDESTRIAN_POSITION = (
        "OpenCloseSlidingGateWithPedestrianPosition"
    )
    OPEN_THERM_DIAGNOSTIC = "OpenThermDiagnostic"
    PERGOLA_HORIZONTAL_AWNING = "PergolaHorizontalAwning"
    PERGOLA_HORIZONTAL_AWNING_UNO = "PergolaHorizontalAwningUno"
    PERGOLA_SIDE_SCREEN = "PergolaSideScreen"
    POD = "Pod"
    POSITIONABLE_AND_LOCKABLE_SLIDING_WINDOW = "PositionableAndLockableSlidingWindow"
    POSITIONABLE_AND_STRETCHABLE_PERGOLA_SCREEN = (
        "PositionableAndStretchablePergolaScreen"
    )
    POSITIONABLE_CURTAIN = "PositionableCurtain"
    POSITIONABLE_DUAL_ROLLER_SHUTTER = "PositionableDualRollerShutter"
    POSITIONABLE_EXTERIOR_VENETIAN_BLIND = "PositionableExteriorVenetianBlind"
    POSITIONABLE_EXTERIOR_VENETIAN_BLIND_UNO = "PositionableExteriorVenetianBlindUno"
    POSITIONABLE_EXTERIOR_VENETIAN_BLIND_WITH_WP = (
        "PositionableExteriorVenetianBlindWithWP"
    )
    POSITIONABLE_EXTERIOR_VENETIAN_BLIND_WITH_WP2 = (
        "PositionableExteriorVenetianBlindWithWP2"
    )
    POSITIONABLE_GARAGE_DOOR = "PositionableGarageDoor"
    POSITIONABLE_GARAGE_DOOR_WITH_PARTIAL_POSITION = (
        "PositionableGarageDoorWithPartialPosition"
    )
    POSITIONABLE_GATE = "PositionableGate"
    POSITIONABLE_GATE_WITH_PEDESTRIAN_POSITION = (
        "PositionableGateWithPedestrianPosition"
    )
    POSITIONABLE_HORIZONTAL_AWNING = "PositionableHorizontalAwning"
    POSITIONABLE_HORIZONTAL_AWNING_UNO = "PositionableHorizontalAwningUno"
    POSITIONABLE_OR_ORIENTABLE_ROLLER_SHUTTER = "PositionableOrOrientableRollerShutter"
    POSITIONABLE_OR_PROGRESSIVE_ORIENTABLE_ROLLER_SHUTTER = (
        "PositionableOrProgressiveOrientableRollerShutter"
    )
    POSITIONABLE_PROJECTION_ROLLER_SHUTTER = "PositionableProjectionRollerShutter"
    POSITIONABLE_ROLLER_SHUTTER = "PositionableRollerShutter"
    POSITIONABLE_ROLLER_SHUTTER_UNO = "PositionableRollerShutterUno"
    POSITIONABLE_ROLLER_SHUTTER_WITH_LOW_SPEED_MANAGEMENT = (
        "PositionableRollerShutterWithLowSpeedManagement"
    )
    POSITIONABLE_SCREEN = "PositionableScreen"
    POSITIONABLE_SCREEN_UNO = "PositionableScreenUno"
    POSITIONABLE_SLIDING_WINDOW = "PositionableSlidingWindow"
    POSITIONABLE_TILTED_ROLLER_SHUTTER = "PositionableTiltedRollerShutter"
    POSITIONABLE_TILTED_SCREEN = "PositionableTiltedScreen"
    POSITIONABLE_TILTED_WINDOW = "PositionableTiltedWindow"
    POSITIONABLE_VENETIAN_BLIND = "PositionableVenetianBlind"
    POSITIONABLE_WINDOW = "PositionableWindow"
    POSITIONABLE_WINDOW_UNO = "PositionableWindowUno"
    PROGRAMMABLE_AND_PROTECTABLE_THERMOSTAT_SET_POINT = (
        "ProgrammableAndProtectableThermostatSetPoint"
    )
    RTD_INDOOR_SIREN = "RTDIndoorSiren"
    RTD_OUTDOOR_SIREN = "RTDOutdoorSiren"
    RTS_GENERIC = "RTSGeneric"
    RTS_GENERIC_4T = "RTSGeneric4T"
    RTS_THERMOSTAT = "RTSThermostat"
    RAIN_SENSOR = "RainSensor"
    RELATIVE_HUMIDITY_SENSOR = "RelativeHumiditySensor"
    REMOTE_CONTROLLER_ONE_WAY = "RemoteControllerOneWay"
    REPEATER = "Repeater"
    ROCKER_SWITCH_AUTO_MANU_UP_DOWN_CONTROLLER = "RockerSwitchAutoManuUpDownController"
    ROCKER_SWITCHX_1_CONTROLLER = "RockerSwitchx1Controller"
    ROCKER_SWITCHX_2_CONTROLLER = "RockerSwitchx2Controller"
    ROCKER_SWITCHX_4_CONTROLLER = "RockerSwitchx4Controller"
    SCENE_CONTROLLER = "SceneController"
    SCHNEIDER_SWITCH_CONFIGURATION = "SchneiderSwitchConfiguration"
    SIREN_STATUS = "SirenStatus"
    SLATS_ORIENTATION = "SlatsOrientation"
    SLIDING_DISCRETE_GATE_WITH_PEDESTRIAN_POSITION = (
        "SlidingDiscreteGateWithPedestrianPosition"
    )
    SMOKE_SENSOR = "SmokeSensor"
    SOMFY_CONFIGURATION_TOOL = "SomfyConfigurationTool"
    SOMFY_HEATING_TEMPERATURE_INTERFACE = "SomfyHeatingTemperatureInterface"
    SOMFY_PILOT_WIRE_ELECTRICAL_HEATER = "SomfyPilotWireElectricalHeater"
    SOMFY_PILOT_WIRE_HEATING_INTERFACE = "SomfyPilotWireHeatingInterface"
    SOMFY_THERMOSTAT = "SomfyThermostat"
    STATEFUL_ALARM_CONTROLLER = "StatefulAlarmController"
    STATEFUL_ON_OFF = "StatefulOnOff"
    STATEFUL_ON_OFF_LIGHT = "StatefulOnOffLight"
    STATELESS_ALARM_CONTROLLER = "StatelessAlarmController"
    STATELESS_EXTERIOR_HEATING = "StatelessExteriorHeating"
    STATELESS_ON_OFF = "StatelessOnOff"
    SUN_ENERGY_SENSOR = "SunEnergySensor"
    SUN_INTENSITY_SENSOR = "SunIntensitySensor"
    SWIMMING_POOL = "SwimmingPool"
    SWINGING_SHUTTER = "SwingingShutter"
    TSKALARM_CONTROLLER = "TSKAlarmController"
    TEMPERATURE_SENSOR = "TemperatureSensor"
    THERMOSTAT_HEATING_TEMPERATURE_INTERFACE = "ThermostatHeatingTemperatureInterface"
    THERMOSTAT_SET_POINT = "ThermostatSetPoint"
    THERMOSTAT_ZONES_CONTROLLER = "ThermostatZonesController"
    THREE_WAY_WINDOW_HANDLE = "ThreeWayWindowHandle"
    TILT_ONLY_VENETIAN_BLIND = "TiltOnlyVenetianBlind"
    TIMED_ON_OFF = "TimedOnOff"
    TIMED_ON_OFF_LIGHT = "TimedOnOffLight"
    UNIVERSAL_SENSOR = "UniversalSensor"
    UNTYPED = "Untyped"
    UP_DOWN_BIOCLIMATIC_PERGOLA = "UpDownBioclimaticPergola"
    UP_DOWN_CELLULAR_SCREEN = "UpDownCellularScreen"
    UP_DOWN_CURTAIN = "UpDownCurtain"
    UP_DOWN_DUAL_CURTAIN = "UpDownDualCurtain"
    UP_DOWN_EXTERIOR_SCREEN = "UpDownExteriorScreen"
    UP_DOWN_EXTERIOR_VENETIAN_BLIND = "UpDownExteriorVenetianBlind"
    UP_DOWN_GARAGE_DOOR = "UpDownGarageDoor"
    UP_DOWN_GARAGE_DOOR_4T = "UpDownGarageDoor4T"
    UP_DOWN_GARAGE_DOOR_WITH_VENTILATION_POSITION = (
        "UpDownGarageDoorWithVentilationPosition"
    )
    UP_DOWN_HORIZONTAL_AWNING = "UpDownHorizontalAwning"
    UP_DOWN_ROLLER_SHUTTER = "UpDownRollerShutter"
    UP_DOWN_SCREEN = "UpDownScreen"
    UP_DOWN_SHEER_SCREEN = "UpDownSheerScreen"
    UP_DOWN_SWINGING_SHUTTER = "UpDownSwingingShutter"
    UP_DOWN_VENETIAN_BLIND = "UpDownVenetianBlind"
    UP_DOWN_WINDOW = "UpDownWindow"
    UP_DOWN_ZEBRA_SCREEN = "UpDownZebraScreen"
    VOCSENSOR = "VOCSensor"
    VALVE_HEATING_TEMPERATURE_INTERFACE = "ValveHeatingTemperatureInterface"
    VENTILATION_INLET = "VentilationInlet"
    VENTILATION_OUTLET = "VentilationOutlet"
    VENTILATION_TRANSFER = "VentilationTransfer"
    WATER_DETECTION_SENSOR = "WaterDetectionSensor"
    WEATHER_FORECAST_SENSOR = "WeatherForecastSensor"
    WIFI = "Wifi"
    WIND_SPEED_SENSOR = "WindSpeedSensor"
    WINDOW_LOCK = "WindowLock"
    WINDOW_WITH_TILT_SENSOR = "WindowWithTiltSensor"
    ZWAVE_AEOTEC_CONFIGURATION = "ZWaveAeotecConfiguration"
    ZWAVE_CONFIGURATION = "ZWaveConfiguration"
    ZWAVE_DANFOSS_RSLINK = "ZWaveDanfossRSLink"
    ZWAVE_DOOR_LOCK_CONFIGURATION = "ZWaveDoorLockConfiguration"
    ZWAVE_FIBARO_ROLLER_SHUTTER_CONFIGURATION = "ZWaveFibaroRollerShutterConfiguration"
    ZWAVE_HEATIT_THERMOSTAT_CONFIGURATION = "ZWaveHeatitThermostatConfiguration"
    ZWAVE_NODON_CONFIGURATION = "ZWaveNodonConfiguration"
    ZWAVE_QUBINO_CONFIGURATION = "ZWaveQubinoConfiguration"
    ZWAVE_SEDEVICE_CONFIGURATION = "ZWaveSEDeviceConfiguration"
    ZWAVE_TRANSCEIVER = "ZWaveTransceiver"
    ZIGBEE_NETWORK = "ZigbeeNetwork"
    ZIGBEE_STACK = "ZigbeeStack"
