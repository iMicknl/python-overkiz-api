import sys
from enum import unique

# Since we support Python versions lower than 3.11, we use
# a backport for StrEnum when needed.
if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from backports.strenum import StrEnum


@unique
class OverkizCommand(StrEnum):
    """Device commands used by Overkiz."""

    ACTIVATE_OPTION = "activateOption"
    ADVANCED_REFRESH = "advancedRefresh"
    ALARM_OFF = "alarmOff"
    ALARM_ON = "alarmOn"
    ALARM_PARTIAL_1 = "alarmPartial1"
    ALARM_PARTIAL_2 = "alarmPartial2"
    ALARM_ZONE_ON = "alarmZoneOn"
    ARM = "arm"
    ARM_PARTIAL_DAY = "armPartialDay"
    ARM_PARTIAL_NIGHT = "armPartialNight"
    BIP = "bip"
    CANCEL_ABSENCE = "cancelAbsence"
    CLOSE = "close"
    CLOSE_SLATS = "closeSlats"
    CYCLE = "cycle"
    DEACTIVATE_OPTION = "deactivateOption"
    DELAYED_STOP_IDENTIFY = "delayedStopIdentify"
    DEPLOY = "deploy"
    DISARM = "disarm"
    DING_DONG = "dingDong"
    DOWN = "down"
    EXIT_DEROGATION = "exitDerogation"
    FAST_BIP_SEQUENCE = "fastBipSequence"
    GET_LEVEL = "getLevel"
    GET_NAME = "getName"
    GLOBAL_CONTROL = "globalControl"
    GO_TO_ALIAS = "goToAlias"
    IDENTIFY = "identify"
    LOCK = "lock"
    MEMORIZED_VOLUME = "memorizedVolume"
    MY = "my"
    OFF = "off"
    OFFLINE = "offline"
    ON = "on"
    ONLINE = "online"
    ON_WITH_TIMER = "onWithTimer"
    OPEN = "open"
    OPEN_SLATS = "openSlats"
    PARTIAL = "partial"
    PARTIAL_POSITION = "partialPosition"
    REFRESH_ABSENCE_SCHEDULING_AVAILABILITY = "refreshAbsenceSchedulingAvailability"
    REFRESH_BOOST_MODE_DURATION = "refreshBoostModeDuration"
    REFRESH_COMFORT_COOLING_TARGET_TEMPERATURE = (
        "refreshComfortCoolingTargetTemperature"
    )
    REFRESH_COMFORT_HEATING_TARGET_TEMPERATURE = (
        "refreshComfortHeatingTargetTemperature"
    )
    REFRESH_COMFORT_TARGET_DWH_TEMPERATURE = "refreshComfortTargetDHWTemperature"
    REFRESH_DEROGATION_REMAINING_TIME = "refreshDerogationRemainingTime"
    REFRESH_DEVICE_SERIAL_NUMBER = "refreshDeviceSerialNumber"
    REFRESH_ECO_COOLING_TARGET_TEMPERATURE = "refreshEcoCoolingTargetTemperature"
    REFRESH_ECO_HEATING_TARGET_TEMPERATURE = "refreshEcoHeatingTargetTemperature"
    REFRESH_ECO_TARGET_DWH_TEMPERATURE = "refreshEcoTargetDHWTemperature"
    REFRESH_ERROR_CODE = "refreshErrorCode"
    REFRESH_DHW_MODE = "refreshDHWMode"
    REFRESH_HEATING_DEROGATION_AVAILABILITY = "refreshHeatingDerogationAvailability"
    REFRESH_OPERATING_MODE = "refreshOperatingMode"
    REFRESH_PASS_APC_COOLING_MODE = "refreshPassAPCCoolingMode"
    REFRESH_PASS_APC_COOLING_PROFILE = "refreshPassAPCCoolingProfile"
    REFRESH_PASS_APC_HEATING_MODE = "refreshPassAPCHeatingMode"
    REFRESH_PASS_APC_HEATING_PROFILE = "refreshPassAPCHeatingProfile"
    REFRESH_PRODUCT_TYPE = "refreshProductType"
    REFRESH_STATE = "refreshState"
    REFRESH_TARGET_DWH_TEMPERATURE = "refreshTargetDHWTemperature"
    REFRESH_TARGET_TEMPERATURE = "refreshTargetTemperature"
    REFRESH_THERMAL_SCHEDULING_AVAILABILITY = "refreshThermalSchedulingAvailability"
    REFRESH_TIME_PROGRAM_BY_ID = "refreshTimeProgramById"
    REFRESH_VENTILATION_CONFIGURATION_MODE = "refreshVentilationConfigurationMode"
    REFRESH_VENTILATION_STATE = "refreshVentilationState"
    REFRESH_WATER_TARGET_TEMPERATURE = "refreshWaterTargetTemperature"
    REFRESH_ZONES_NUMBER = "refreshZonesNumber"
    REFRESH_ZONES_TARGET_TEMPERATURE = "refreshZonesTargetTemperature"
    REFRESH_ZONES_TEMPERATURE = "refreshZonesTemperature"
    REFRESH_ZONES_TEMPERATURE_SENSOR_AVAILABILITY = (
        "refreshZonesTemperatureSensorAvailability"
    )
    REFRESH_ZONES_THERMAL_CONFIGURATION = "refreshZonesThermalConfiguration"
    REFRESH_ZONES_PASS_APC_COOLING_PROFILE = "refreshZonesPassAPCCoolingProfile"
    REFRESH_ZONES_PASS_APC_HEATING_PROFILE = "refreshZonesPassAPCHeatingProfile"
    RIGHT = "right"
    RING = "ring"
    RING_WITH_SINGLE_SIMPLE_SEQUENCE = "ringWithSingleSimpleSequence"
    SAVE_ALIAS = "saveAlias"
    SET_ABSENCE_MODE = "setAbsenceMode"
    SET_ABSENCE_COOLING_TARGET_TEMPERATURE = "setAbsenceCoolingTargetTemperature"
    SET_ABSENCE_END_DATE_TIME = "setAbsenceEndDateTime"
    SET_ABSENCE_HEATING_TARGET_TEMPERATURE = "setAbsenceHeatingTargetTemperature"
    SET_ABSENCE_START_DATE_TIME = "setAbsenceStartDateTime"
    SET_ACTIVE_MODE = "setActiveMode"
    SET_AIR_DEMAND_MODE = "setAirDemandMode"
    SET_ALARM_STATUS = "setAlarmStatus"
    SET_ALL_MODE_TEMPERATURES = "setAllModeTemperatures"
    SET_AUTO_MANU_MODE = "setAutoManuMode"
    SET_AWAY_MODE_DURATION = "setAwayModeDuration"
    SET_BOOST_MODE = "setBoostMode"
    SET_BOOST_MODE_DURATION = "setBoostModeDuration"
    SET_BOOST_ON_OFF_STATE = "setBoostOnOffState"
    SET_CLOSURE = "setClosure"
    SET_CLOSURE_AND_LINEAR_SPEED = "setClosureAndLinearSpeed"
    SET_CLOSURE_AND_ORIENTATION = "setClosureAndOrientation"
    SET_COMFORT_COOLING_TARGET_TEMPERATURE = "setComfortCoolingTargetTemperature"
    SET_COMFORT_HEATING_TARGET_TEMPERATURE = "setComfortHeatingTargetTemperature"
    SET_COMFORT_TARGET_DHW_TEMPERATURE = "setComfortTargetDHWTemperature"
    SET_COMFORT_TEMPERATURE = "setComfortTemperature"
    SET_CONTROL_DHW = "setControlDHW"
    SET_CONTROL_DHW_SETTING_TEMPERATURE = "setControlDHWSettingTemperature"
    SET_COOLING_ON_OFF = "setCoolingOnOffState"
    SET_COOLING_TARGET_TEMPERATURE = "setCoolingTargetTemperature"
    SET_CURRENT_OPERATING_MODE = "setCurrentOperatingMode"
    SET_DEPLOYMENT = "setDeployment"
    SET_DEROGATED_TARGET_TEMPERATURE = "setDerogatedTargetTemperature"
    SET_DEROGATION = "setDerogation"
    SET_DEROGATION_ON_OFF_STATE = "setDerogationOnOffState"
    SET_DEROGATION_TIME = "setDerogationTime"
    SET_DHW_MODE = "setDHWMode"
    SET_DHW_ON_OFF_STATE = "setDHWOnOffState"
    SET_ECO_COOLING_TARGET_TEMPERATURE = "setEcoCoolingTargetTemperature"
    SET_ECO_HEATING_TARGET_TEMPERATURE = "setEcoHeatingTargetTemperature"
    SET_ECO_TARGET_DHW_TEMPERATURE = "setEcoTargetDHWTemperature"
    SET_ECO_TEMPERATURE = "setEcoTemperature"
    SET_EXPECTED_NUMBER_OF_SHOWER = "setExpectedNumberOfShower"
    SET_FORCE_HEATING = "setForceHeating"
    SET_HEATING_COOLING_AUTO_SWITCH = "setHeatingCoolingAutoSwitch"
    SET_HEATING_LEVEL = "setHeatingLevel"
    SET_HEATING_ON_OFF = "setHeatingOnOffState"
    SET_HEATING_TARGET_TEMPERATURE = "setHeatingTargetTemperature"
    SET_HOLIDAYS = "setHolidays"
    SET_INTENSITY = "setIntensity"
    SET_LEVEL = "setLevel"
    SET_MANU_AND_SET_POINT_MODES = "setManuAndSetPointModes"
    SET_MEMORIZED_1_POSITION = "setMemorized1Position"
    SET_MEMORIZED_SIMPLE_VOLUME = "setMemorizedSimpleVolume"
    SET_MODE_TEMPERATURE = "setModeTemperature"
    SET_NAME = "setName"
    SET_OPERATING_MODE = "setOperatingMode"
    SET_ORIENTATION = "setOrientation"
    SET_PASS_APC_COOLING_MODE = "setPassAPCCoolingMode"
    SET_PASS_APC_DHW_MODE = "setPassAPCDHWMode"
    SET_PASS_APC_HEATING_MODE = "setPassAPCHeatingMode"
    SET_PASS_APC_OPERATING_MODE = "setPassAPCOperatingMode"
    SET_PEDESTRIAN_POSITION = "setPedestrianPosition"
    SET_RGB = "setRGB"
    SET_SCHEDULING_TYPE = "setSchedulingType"
    SET_SECURED_POSITION_TEMPERATURE = "setSecuredPositionTemperature"
    SET_TARGET_MODE = "setTargetMode"
    SET_TARGET_ALARM_MODE = "setTargetAlarmMode"
    SET_TARGET_TEMPERATURE = "setTargetTemperature"
    SET_TARGET_DHW_TEMPERATURE = "setTargetDHWTemperature"
    SET_THERMOSTAT_SETTING_CONTROL_ZONE_1 = "setThermostatSettingControlZone1"
    SET_TIME_PROGRAM_BY_ID = "setTimeProgramById"
    SET_TOWEL_DRYER_OPERATING_MODE = "setTowelDryerOperatingMode"
    SET_TOWEL_DRYER_TEMPORARY_STATE = "setTowelDryerTemporaryState"
    SET_VALVE_SETTINGS = "setValveSettings"
    SET_VENTILATION_CONFIGURATION_MODE = "setVentilationConfigurationMode"
    SET_VENTILATION_MODE = "setVentilationMode"
    SET_WATER_TARGET_TEMPERATURE = "setWaterTargetTemperature"
    STANDARD = "standard"
    START_IDENTIFY = "startIdentify"
    STOP = "stop"
    STOP_IDENTIFY = "stopIdentify"
    TEST = "test"
    TILT = "tilt"
    TILT_DOWN = "tiltDown"
    TILT_UP = "tiltUp"
    UNDEPLOY = "undeploy"
    UNINSTALLED = "uninstalled"
    UNLOCK = "unlock"
    UP = "up"
    UPDATE = "update"
    WINK = "wink"


@unique
class OverkizCommandParam(StrEnum):
    """Parameter used by Overkiz commands and/or states."""

    A = "A"
    ABSENCE = "absence"
    ACTIVE = "active"
    ADJUSTMENT = "adjustment"
    ARMED = "armed"
    ARMED_DAY = "armedDay"
    ARMED_NIGHT = "armedNight"
    AT_HOME_MODE = "atHomeMode"
    AUTO = "auto"
    AUTOCOOLING = "autocooling"
    AUTOHEATING = "autoheating"
    AUTO_MODE = "autoMode"
    AVAILABLE = "available"
    AWAY = "away"
    AWAY_MODE = "awayMode"
    B = "B"
    BASIC = "basic"
    BY_PASS = "by_pass"
    BOOST = "boost"
    BOTH = "both"
    C = "C"
    CLOSE = "close"
    CLOSED = "closed"
    COMFORT = "comfort"
    COMFORT_1 = "comfort-1"
    COMFORT_2 = "comfort-2"
    COOLING = "cooling"
    DATE_SCHEDULING = "dateScheduling"
    DAY_OFF = "day-off"
    DEROGATION = "derogation"
    DEAD = "dead"
    DEHUMIDIFY = "dehumidify"
    DETECTED = "detected"
    DISARMED = "disarmed"
    DISABLE = "disable"
    DISABLED = "disabled"
    DRYING = "drying"
    ECO = "eco"
    ENABLE = "enable"
    ENABLED = "enabled"
    ENERGY_DEMAND_STATUS = "energyDemandStatus"
    EXTERNAL = "external"
    EXTERNAL_GATEWAY = "externalGateway"
    EXTERNAL_SCHEDULING = "externalScheduling"
    EXTERNAL_SETPOINT = "externalSetpoint"
    FAN = "fan"
    FINISHED = "finished"
    FREE = "free"
    FREEZE_MODE = "freezeMode"
    FROSTPROTECTION = "frostprotection"
    FULL = "full"
    FULL_CLOSED = "full_closed"
    FULL_OPEN = "full_open"
    FURTHER_NOTICE = "further_notice"
    GEOFENCING_MODE = "geofencingMode"
    HEATING = "heating"
    HEATING_AND_COOLING = "heatingAndCooling"
    HEATING_AND_COOLING_COMMON_SCHEDULING = "heatingAndCoolingCommonScheduling"
    HEATING_AND_COOLING_SEPARATED_SCHEDULING = "heatingAndCoolingSeparatedScheduling"
    HI = "hi"
    HIGH = "high"
    HIGHEST = "highest"
    HIGH_DEMAND = "high demand"  # not a typo...
    HOLIDAYS = "holidays"
    HORIZONTAL = "horizontal"
    INACTIVE = "inactive"
    INTERNAL = "internal"
    INTERNAL_SCHEDULING = "internalScheduling"
    LO = "lo"
    LOCAL_USER = "localUser"
    LOCKED = "locked"
    LOCK_KEY = "lock_key"
    LOW = "low"
    LOWSPEED = "lowspeed"
    LOW_BATTERY = "lowBattery"
    LSC = "LSC"
    MAINTENANCE_REQUIRED = "maintenanceRequired"
    MANU = "manu"
    MANUAL = "manual"
    MANUAL_ECO_ACTIVE = "manualEcoActive"
    MANUAL_ECO_INACTIVE = "manualEcoInactive"
    MANUAL_MODE = "manualMode"
    MAX_SETPOINT = "max_setpoint"
    MED = "med"
    MEDIUM = "medium"
    MEMORIZED_VOLUME = "memorizedVolume"
    MIN_SETPOINT = "min_setpoint"
    NORMAL = "normal"
    NONE = "none"
    NOT_DETECTED = "notDetected"
    NO_DEFECT = "noDefect"
    NUMBER_OF_DAYS_SCHEDULING = "numberOfDaysScheduling"
    OFF = "off"
    ON = "on"
    OPEN = "open"
    OPENED = "opened"
    OPEN_WINDOW = "open_window"
    PAIRING = "pairing"
    PARTIAL = "partial"
    PARTIAL_1 = "partial1"
    PARTIAL_2 = "partial2"
    PEDESTRIAN = "pedestrian"
    PENDING = "pending"
    PERFORMANCE = "performance"
    PERMANENT_HEATING = "permanentHeating"
    PERSON_INSIDE = "personInside"
    PROG = "prog"
    RELAUNCH = "relaunch"
    RESET = "reset"
    SAAC = "SAAC"
    SECURED = "secured"
    SFC = "SFC"
    SILENCE = "silence"
    SILENT = "silent"
    SLEEPING_MODE = "sleepingMode"
    STANDARD = "standard"
    STANDBY = "standby"
    STOP = "stop"
    SUDDEN_DROP_MODE = "suddenDropMode"
    TEMPERATURE_OFFSET = "temperature_offset"
    TILT = "tilt"
    TOTAL = "total"
    UNDETECTED = "undetected"
    UPS = "UPS"
    VERTICAL = "vertical"
    VERY_LOW = "verylow"
    ZONE_1 = "zone1"
    ZONE_2 = "zone2"


@unique
class CommandMode(StrEnum):
    HIGH_PRIORITY = "highPriority"
    GEOLOCATED = "geolocated"
    INTERNAL = "internal"
