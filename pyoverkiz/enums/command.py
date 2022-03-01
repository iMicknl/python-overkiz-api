from enum import Enum, unique


@unique
class OverkizCommand(str, Enum):
    """Device commands used by Overkiz."""

    ADVANCED_REFRESH = "advancedRefresh"
    ALARM_OFF = "alarmOff"
    ALARM_ON = "alarmOn"
    ALARM_PARTIAL_1 = "alarmPartial1"
    ALARM_PARTIAL_2 = "alarmPartial2"
    ALARM_ZONE_ON = "alarmZoneOn"
    ARM = "arm"
    ARM_PARTIAL_DAY = "armPartialDay"
    ARM_PARTIAL_NIGHT = "armPartialNight"
    CLOSE = "close"
    CLOSE_SLATS = "closeSlats"
    CYCLE = "cycle"
    DEPLOY = "deploy"
    DISARM = "disarm"
    DOWN = "down"
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
    REFRESH_BOOST_MODE_DURATION = "refreshBoostModeDuration"
    REFRESH_VENTILATION_CONFIGURATION_MODE = "refreshVentilationConfigurationMode"
    REFRESH_VENTILATION_STATE = "refreshVentilationState"
    RING_WITH_SINGLE_SIMPLE_SEQUENCE = "ringWithSingleSimpleSequence"
    SET_ABSENCE_MODE = "setAbsenceMode"
    SET_ACTIVE_MODE = "setActiveMode"
    SET_AIR_DEMAND_MODE = "setAirDemandMode"
    SET_ALARM_STATUS = "setAlarmStatus"
    SET_ALL_MODE_TEMPERATURES = "setAllModeTemperatures"
    SET_BOOST_MODE = "setBoostMode"
    SET_BOOST_MODE_DURATION = "setBoostModeDuration"
    SET_CLOSURE = "setClosure"
    SET_CLOSURE_AND_LINEAR_SPEED = "setClosureAndLinearSpeed"
    SET_COMFORT_TEMPERATURE = "setComfortTemperature"
    SET_CONTROL_DHW = "setControlDHW"
    SET_CONTROL_DHW_SETTING_TEMPERATURE = "setControlDHWSettingTemperature"
    SET_CURRENT_OPERATING_MODE = "setCurrentOperatingMode"
    SET_DEPLOYMENT = "setDeployment"
    SET_DEROGATION = "setDerogation"
    SET_DEROGATED_TARGET_TEMPERATURE = "setDerogatedTargetTemperature"
    SET_DHW_MODE = "setDHWMode"
    SET_ECO_TEMPERATURE = "setEcoTemperature"
    SET_EXPECTED_NUMBER_OF_SHOWER = "setExpectedNumberOfShower"
    SET_FORCE_HEATING = "setForceHeating"
    SET_HEATING_LEVEL = "setHeatingLevel"
    SET_INTENSITY = "setIntensity"
    SET_LEVEL = "setLevel"
    SET_MANU_AND_SET_POINT_MODES = "setManuAndSetPointModes"
    SET_MEMORIZED_1_POSITION = "setMemorized1Position"
    SET_MEMORIZED_SIMPLE_VOLUME = "setMemorizedSimpleVolume"
    SET_OPERATING_MODE = "setOperatingMode"
    SET_ORIENTATION = "setOrientation"
    SET_PEDESTRIAN_POSITION = "setPedestrianPosition"
    SET_RGB = "setRGB"
    SET_SECURED_POSITION_TEMPERATURE = "setSecuredPositionTemperature"
    SET_TARGET_ALARM_MODE = "setTargetAlarmMode"
    SET_TARGET_TEMPERATURE = "setTargetTemperature"
    SET_TOWER_DRYER_OPERATING_MODE = "setTowelDryerOperatingMode"
    SET_TOWEL_DRYER_TEMPORARY_STATE = "setTowelDryerTemporaryState"
    SET_VENTILATION_MODE = "setVentilationMode"
    SET_VENTILATION_CONFIGURATION_MODE = "setVentilationConfigurationMode"
    STANDARD = "standard"
    STOP = "stop"
    STOP_IDENTIFY = "stopIdentify"
    TEST = "test"
    UNDEPLOY = "undeploy"
    UNINSTALLED = "uninstalled"
    UNLOCK = "unlock"
    UP = "up"
    WINK = "wink"


@unique
class OverkizCommandParam(str, Enum):
    """Parameter used by Overkiz commands and/or states."""

    A = "A"
    ABSENCE = "absence"
    ARMED = "armed"
    ARMED_DAY = "armedDay"
    ARMED_NIGHT = "armedNight"
    AUTO = "auto"
    AUTO_MODE = "autoMode"
    AVAILABLE = "available"
    AWAY = "away"
    B = "B"
    BOOST = "boost"
    C = "C"
    CLOSE = "close"
    CLOSED = "closed"
    COMFORT = "comfort"
    COOLING = "cooling"
    DAY_OFF = "day-off"
    DEAD = "dead"
    DETECTED = "detected"
    DISARMED = "disarmed"
    DRYING = "drying"
    ECO = "eco"
    ENERGY_DEMAND_STATUS = "energyDemandStatus"
    EXTERNAL = "external"
    EXTERNAL_GATEWAY = "externalGateway"
    FREE = "free"
    FROSTPROTECTION = "frostprotection"
    FULL = "full"
    GEOFENCING_MODE = "geofencingMode"
    HEATING = "heating"
    HIGH = "high"
    HIGH_DEMAND = "high demand"  # not a typo...
    HIGHEST = "highest"
    HOLIDAYS = "holidays"
    INTERNAL = "internal"
    LOCAL_USER = "localUser"
    LOCKED = "locked"
    LOW = "low"
    LOW_BATTERY = "lowBattery"
    LOWSPEED = "lowspeed"
    LSC = "LSC"
    MAINTENANCE_REQUIRED = "maintenanceRequired"
    MANU = "manu"
    MANUAL = "manual"
    MANUAL_ECO_ACTIVE = "manualEcoActive"
    MANUAL_ECO_INACTIVE = "manualEcoInactive"
    MEMORIZED_VOLUME = "memorizedVolume"
    NO_DEFECT = "noDefect"
    NORMAL = "normal"
    NOT_DETECTED = "notDetected"
    OFF = "off"
    ON = "on"
    OPEN = "open"
    OPENED = "opened"
    PARTIAL = "partial"
    PARTIAL_1 = "partial1"
    PARTIAL_2 = "partial2"
    PEDESTRIAN = "pedestrian"
    PENDING = "pending"
    PERMANENT_HEATING = "permanentHeating"
    PERSON_INSIDE = "personInside"
    PROG = "prog"
    RELAUNCH = "relaunch"
    SAAC = "SAAC"
    STANDBY = "standby"
    SECURED = "secured"
    SET_AWAY_MODE_DURATION = "setAwayModeDuration"
    SET_BOOST_MODE_DURATION = "setBoostModeDuration"
    SFC = "SFC"
    STANDARD = "standard"
    STOP = "stop"
    TOTAL = "total"
    UNDETECTED = "undetected"
    UPS = "UPS"
    VERY_LOW = "verylow"
    ZONE_1 = "zone1"
    ZONE_2 = "zone2"


@unique
class CommandMode(str, Enum):
    HIGH_PRIORITY = "highPriority"
    GEOLOCATED = "geolocated"
    INTERNAL = "internal"
