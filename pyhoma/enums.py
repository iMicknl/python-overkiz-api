import logging
from enum import Enum, IntEnum, unique

_LOGGER = logging.getLogger(__name__)


@unique
class ProductType(IntEnum):
    NONE = 0
    ACTUATOR = 1
    SENSOR = 2
    VIDEO = 3
    CONTROLLABLE = 4
    GATEWAY = 5
    INFRASTRUCTURE_COMPONENT = 6
    GROUP = 7


@unique
class DataType(IntEnum):
    NONE = 0
    INTEGER = 1
    FLOAT = 2
    STRING = 3
    BLOB = 4
    DATE = 5
    BOOLEAN = 6
    PASSWORD = 9
    JSON_ARRAY = 10
    JSON_OBJECT = 11


@unique
class ExecutionType(str, Enum):
    IMMEDIATE_EXECUTION = "Immediate execution"
    DELAYED_EXECUTION = "Delayed execution"
    TECHNICAL_EXECUTION = "Technical execution"
    PLANNING = "Planning"
    RAW_TRIGGER_SERVER = "Raw trigger (Server)"
    RAW_TRIGGER_GATEWAY = "Raw trigger (Gateway)"


@unique
class ExecutionState(str, Enum):
    INITIALIZED = "INITIALIZED"
    NOT_TRANSMITTED = "NOT_TRANSMITTED"
    TRANSMITTED = "TRANSMITTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    QUEUED_GATEWAY_SIDE = "QUEUED_GATEWAY_SIDE"
    QUEUED_SERVER_SIDE = "QUEUED_SERVER_SIDE"


@unique
class ExecutionSubType(str, Enum):
    ACTION_GROUP = "ACTION_GROUP"
    ACTION_GROUP_SEQUENCE = "ACTION_GROUP_SEQUENCE"
    DAWN_TRIGGER = "DAWN_TRIGGER"
    DUSK_TRIGGER = "DUSK_TRIGGER"
    DISCRETE_TRIGGER_USER = "DISCRETE_TRIGGER_USER"
    GENERIC_COMMAND_SCHEDULING = "GENERIC_COMMAND_SCHEDULING"
    IFT_CONDITION = "IFT_CONDITION"
    INTERNAL = "INTERNAL"
    MANUAL_CONTROL = "MANUAL_CONTROL"
    NO_ERROR = "NO_ERROR"
    P2P_COMMAND_REGULATION = "P2P_COMMAND_REGULATION"
    TIME_TRIGGER = "TIME_TRIGGER"


@unique
class FailureType(IntEnum):
    UNKNOWN = -1
    NO_FAILURE = 0
    NON_EXECUTING = 11
    ERROR_WHILE_EXECUTING = 12
    ACTUATORUNKNOWN = 101
    ACTUATORNOANSWER = 102
    ERRORREADWRITEACCESS = 103
    ERRORCOMMAND = 104
    CMDUNKNOWN = 105
    CMDCANCELLED = 106
    NOREMOTECONTROL = 107
    ERROR_TRANSFER_KEY = 108
    ERRORDATABASE = 109
    MODELOCALENABLED = 110
    BAD_CMD = 111
    BAD_HD = 112
    BAD_LEN = 113
    BAD_ADDRESS = 114
    BAD_PARAM = 115
    NOT_FOUND_ETX = 116
    BAD_CRC_SERIAL = 117
    BAD_STATUS = 118
    KEY_NOT_RECEIVE = 119
    INSERTION_ERROR = 120
    NODE_NOT_VERIFY_WITH_NEW_KEY = 121
    POOL_FULL = 122
    ADDRESS_UNKNOWN = 123
    NODE_CANT_PAIRED = 124
    NODE_CANT_UPDATE_TRANSFER_STATUS = 125
    UNKNOWN_ERROR = 126
    INVALID_CHANNEL = 127
    INVALID_COMMAND = 128
    SERIAL_IO_ERROR = 129
    OPERATION_NOT_ALLOWED = 130
    RESTART_STACK = 131
    INCOMPLETE_DISCOVER = 132
    TRANFER_KEY_NO_REMOTE_CONTROLLER = 133
    TRANFER_KEY_MULTI_REMOTE_CONTROLLER = 134
    RF_PROTOCOL_FATAL_ERROR = 135
    INTERNAL_ERROR = 136
    BUSY_RADIO_ERROR = 137
    BAD_MAC_ERROR = 138
    SETUP_REQUIRED = 139
    MASTER_AUTHENTICATION_FAILED_ERROR = 140
    END_OF_RECEIVING_CONFIGURATION_MODE = 141
    DATA_TRANSPORT_SERVICE_ERROR = 142
    DATA_TRANSPORT_SERVICE_ABORTED_BY_RECIPIENT = 143
    STOPPED_BY_CONFIGURATION_OPERATION_ERROR = 144
    COMMAND_NAME_TYPE_INVALID = 145
    COMMAND_NAME_NOT_INSTALLED_OR_INVALID = 146
    COMMAND_INVALID_LEN_ON_FRAME = 147
    COMMAND_ZONE_INVALID_OR_NOT_INSTALLED = 148
    COMMAND_SENSOR_VALUE_INVALID = 149
    COMMAND_ZONE_TEMPERATURE_INVALID = 150
    COMMAND_DHW_NOT_INSTALLED_OR_INVALID = 151
    COMMAND_INSERTION_FAILED_ERROR = 152
    NONEXEC_BLOCKED_BY_HAZARD = 153
    NONEXEC_OVERHEATING_PROTECTION = 154
    NONEXEC_DEVICE_LIMITATION = 155
    NONEXEC_DOOR_IS_OPENED = 156
    NONEXEC_MAINTENANCE_REQUIRED = 157
    DEAD_SENSOR = 158
    SENSOR_MAINTENANCE_REQUIRED = 159
    NONEXEC_OTHER = 160
    WHILEEXEC_BLOCKED_BY_HAZARD = 161
    WHILEEXEC_OVERHEATING_PROTECTION = 162
    WHILEEXEC_DEVICE_LIMITATION = 163
    WHILEEXEC_DOOR_IS_OPENED = 164
    WHILEEXEC_MAINTENANCE_REQUIRED = 165
    WHILEEXEC_OTHER = 166
    PRIORITY_LOCK__LOCAL_USER = 167
    PRIORITY_LOCK__USER = 168
    PRIORITY_LOCK__RAIN = 169
    PRIORITY_LOCK__TIMER = 170
    PRIORITY_LOCK__SECURITY = 171
    PRIORITY_LOCK__UPS = 172
    PRIORITY_LOCK__SFC = 173
    PRIORITY_LOCK__LSC = 174
    PRIORITY_LOCK__SAAC = 175
    PRIORITY_LOCK__WIND = 176
    PRIORITY_LOCK__EXTERNAL_ACCESS = 177
    PRIORITY_LOCK__EMERGENCY = 178
    NO_DISTANT_FOR_DISCOVER = 179
    ANOTHER_COMMAND_IS_RUNNING = 180
    PROBLEM_WITH_BOILER_COMMUNICATION = 181
    LOCKED_BY_RCM = 182
    RCM_NO_REMOTE_CONTROL = 183
    DISCOVER_NO_REMOTE_CONTROLLER_ERROR = 184
    COMMAND_INTERRUPTED = 185
    PRIORITY_LOCK__WIND_FORCING_AVAILABLE = 190
    PRIORITY_LOCK__WIND_FORCING_UNAVAILABLE = 191
    PRIORITY_LOCK__NO_SECURITY_DEVICE = 192
    PRIORITY_LOCK__DEAD_SENSOR = 193
    PRIORITY_LOCK__UNKNOWN_ERROR = 194
    DBUS_ERROR = 200
    DBUS_NO_MEMORY = 201
    DBUS_SERVICE_UNKNOWN = 202
    DBUS_NAME_HAS_NO_OWNER = 203
    DBUS_NO_REPLY = 204
    DBUS_IO_ERROR = 205
    DBUS_BAD_ADDRESS = 206
    DBUS_NOT_SUPPORTED = 207
    DBUS_LIMITS_EXCEEDED = 208
    DBUS_ACCESS_DENIED = 209
    DBUS_AUTH_FAILED = 210
    DBUS_NO_SERVER = 211
    DBUS_TIMEOUT = 212
    DBUS_NO_NETWORK = 213
    DBUS_ADDRESS_IN_USE = 214
    DBUS_DISCONNECTED = 215
    DBUS_INVALID_ARGS = 216
    DBUS_FILE_NOT_FOUND = 217
    DBUS_FILE_EXISTS = 218
    DBUS_UNKNOWN_METHOD = 219
    DBUS_UNKNOWN_OBJECT = 220
    DBUS_UNKNOWN_INTERFACE = 221
    DBUS_UNKNOWN_PROPERTY = 222
    DBUS_PROPERTY_READ_ONLY = 223
    DBUS_TIMED_OUT = 224
    DBUS_MATCH_RULE_NOT_FOUND = 225
    DBUS_MATCH_RULE_INVALID = 226
    DBUS_SPAWN_EXEC_FAILED = 227
    DBUS_SPAWN_FORK_FAILED = 228
    DBUS_SPAWN_CHILD_EXITED = 229
    DBUS_SPAWN_CHILD_SIGNALED = 230
    DBUS_SPAWN_FAILED = 231
    DBUS_SPAWN_SETUP_FAILED = 232
    DBUS_SPAWN_CONFIG_INVALID = 233
    DBUS_SPAWN_SERVICE_INVALID = 234
    DBUS_SPAWN_SERVICE_NOT_FOUND = 235
    DBUS_SPAWN_PERMISSIONS_INVALID = 236
    DBUS_SPAWN_FILE_INVALID = 237
    DBUS_SPAWN_NO_MEMORY = 238
    DBUS_UNIX_PROCESS_ID_UNKNOWN = 239
    DBUS_INVALID_SIGNATURE = 240
    DBUS_INVALID_FILE_CONTENT = 241
    DBUS_SELINUX_SECURITY_CONTEXT_UNKNOWN = 242
    DBUS_ADT_AUDIT_DATA_UNKNOWN = 243
    DBUS_OBJECT_PATH_IN_USE = 244
    DBUS_INCONSISTENT_MESSAGE = 245
    NOT_IMPLEMENTED_YET = 300
    MODULE_NOT_LOADED = 301
    APPLICATION_NOT_RUNNING = 302
    NONEXEC_MANUALLY_CONTROLLED = 400
    NONEXEC_AUTOMATIC_CYCLE = 401
    NONEXEC_BATTERY_LEVEL = 402
    NONEXEC_WRONG_LOAD_CONNECTED = 403
    NONEXEC_HIGH_CONSUMPTION = 404
    NONEXEC_LOW_CONSUMPTION = 405
    NONEXEC_COLOUR_NOT_REACHABLE = 406
    NONEXEC_USER_ACTION_NEEDED = 407
    NONEXEC_COMMAND_INCOMPATIBLE_WITH_MOVEMENT = 408
    NONEXEC_CANNOT_CHANGE_STATE = 409
    NONEXEC_FILTER_MAINTENANCE = 410
    NONEXEC_OPERATING_MODE_NOT_SUPPORTED = 411
    WHILEEXEC_MANUALLY_CONTROLLED = 420
    WHILEEXEC_AUTOMATIC_CYCLE = 421
    WHILEEXEC_BATTERY_LEVEL = 422
    WHILEEXEC_WRONG_LOAD_CONNECTED = 423
    WHILEEXEC_HIGH_CONSUMPTION = 424
    WHILEEXEC_LOW_CONSUMPTION = 425
    WHILEEXEC_COLOUR_NOT_REACHABLE = 426
    WHILEEXEC_USER_ACTION_NEEDED = 427
    WHILEEXEC_COMMAND_INCOMPATIBLE_WITH_MOVEMENT = 428
    WHILEEXEC_CANNOT_CHANGE_STATE = 429
    WHILEEXEC_FILTER_MAINTENANCE = 430
    WHILEEXEC_OPERATING_MODE_NOT_SUPPORTED = 431
    OVERRIDEMODE_ERROR = 450
    CAMERA_INVALID_CREDENTIALS = 500
    UNSUPPORTED_CAMERA_TYPE = 501
    NETWORK_COULDNT_RESOLVE_HOST = 601
    NETWORK_COULDNT_CONNECT = 602
    NETWORK_OPERATION_TIMEDOUT = 603
    LPB_APP_OUT_OF_RANGE = 701
    LPB_APP_OUT_OF_MAXRANGE = 702
    LPB_APP_OUT_OF_MINRANGE = 703
    LPB_APP_MEMORY_ERROR = 704
    LPB_APP_READ_ONLY = 705
    LPB_APP_ILLEGAL_CMD = 706
    LPB_APP_VOID_DP = 707
    LPB_APP_TYPE_CONFLICT = 708
    LPB_APP_READ_CMD_INCORRECT = 709
    LPB_APP_WRITE_CMD_INCORRECT = 710
    LPB_APP_CMD_TYPE_INCORRECT = 711
    LPB_APP_WRITE_TIMEOUT = 712
    LPB_APP_CANNOT_WRITE_GW = 713
    LPB_APP_UNKNOWN_GATEWAY = 714
    LPB_APP_GATEWAY_UNREACHABLE = 715
    APPLICATION_ERROR = 800
    HUE_INVALID_CREDENTIALS = 900
    HUE_LINK_BUTTON_NOT_PRESSED = 901
    HUE_DEVICE_IS_OFF = 902
    TIMED_OUT = 10001
    CANCELLED = 10002
    UNKNOWN_ERROR_CODE = 10003
    SERVER_FAILURE = 10004
    PEER_DOWN = 10005
    GATEWAY_BUFFER_OVERFLOW = 10006
    UNKNOWN_DETAILED_ERROR = 10007

    @classmethod
    def _missing_(cls, value):  # type: ignore
        _LOGGER.warning(f"Unsupported value {value} has been returned for {cls}")
        return cls.UNKNOWN


@unique
class EventName(str, Enum):
    UNKNOWN = "Unknown"
    ACTION_GROUP_CREATED = "ActionGroupCreatedEvent"
    ACTION_GROUP_DELETED = "ActionGroupDeletedEvent"
    ACTION_GROUP_UPDATED = "ActionGroupUpdatedEvent"
    CALENDAR_DAY_CREATED = "CalendarDayCreatedEvent"
    CALENDAR_DAY_UPDATED = "CalendarDayUpdatedEvent"
    CALENDAR_RULE_CREATED = "CalendarRuleCreatedEvent"
    CALENDAR_RULE_DELETED = "CalendarRuleDeletedEvent"
    CAMERA_DISCOVERED = "CameraDiscoveredEvent"
    CAMERA_DISCOVER_FAILED = "CameraDiscoverFailedEvent"
    CAMERA_UPLOAD_PHOTO = "CameraUploadPhotoEvent"
    COMMAND_EXECUTION_STATE_CHANGE = "CommandExecutionStateChangedEvent"
    CONDITION_GROUP_CREATED = "ConditionGroupCreatedEvent"
    CONDITION_GROUP_DELETED = "ConditionGroupDeletedEvent"
    CONDITION_GROUP_UPDATED = "ConditionGroupUpdatedEvent"
    DELAYED_TRIGGER_CANCELLED = "DelayedTriggerCancelledEvent"
    DEVICE_AVAILABLE = "DeviceAvailableEvent"
    DEVICE_CREATED = "DeviceCreatedEvent"
    DEVICE_DELETION_FAILED = "DeviceDeletionFailedEvent"
    DEVICE_DISABLED = "DeviceDisabledEvent"
    DEVICE_FIRMWARE_UPDATE_FAILED = "DeviceFirmwareUpdateFailedEvent"
    DEVICE_PROTOCOL_AVAILABLE = "DeviceProtocolAvailableEvent"
    DEVICE_PROTOCOL_UNAVAILABLE = "DeviceProtocolUnavailableEvent"
    DEVICE_REMOVED = "DeviceRemovedEvent"
    DEVICE_STATE_CHANGED = "DeviceStateChangedEvent"
    DEVICE_UNAVAILABLE = "DeviceUnavailableEvent"
    DEVICE_UPDATED = "DeviceUpdatedEvent"
    DISCOVER_COMPLETE = "DiscoverCompleteEvent"
    DISCOVER_FAILED = "DiscoverFailedEvent"
    ELIOT_DISCOVER_GATEWAYS_COMPLETED = "EliotDiscoverGatewaysCompletedEvent"
    ELIOT_DISCOVER_GATEWAYS_FAILED = "EliotDiscoverGatewaysFailedEvent"
    ELIOT_DISCOVER_GATEWAY_COMPLETED = "EliotDiscoverGatewayCompletedEvent"
    ELIOT_DISCOVER_GATEWAY_FAILED = "EliotDiscoverGatewayFailedEvent"
    ELIOT_REFRESH_CURRENT_TOKEN_COMPLETED = "EliotRefreshCurrentTokenCompletedEvent"
    ELIOT_REFRESH_CURRENT_TOKEN_FAILED = "EliotRefreshCurrentTokenFailedEvent"
    END_USER_LOGIN = "EndUserLoginEvent"
    ENOCEAN_BAD_DEVICE_STIMULATION = "EnOceanBadDeviceStimulationEvent"
    ENOCEAN_KNOWN_DEVICE_FOUND = "EnOceanKnownDeviceFoundEvent"
    ENOCEAN_LEARN_STARTED = "EnOceanLearnStartedEvent"
    ENOCEAN_LEARN_STOPPED = "EnOceanLearnStoppedEvent"
    EXECUTION_REGISTERED = "ExecutionRegisteredEvent"
    EXECUTION_STATE_CHANGED = "ExecutionStateChangedEvent"
    GATEWAY_ALIVE = "GatewayAliveEvent"
    GATEWAY_BOOT = "GatewayBootEvent"
    GATEWAY_DOWN = "GatewayDownEvent"
    GATEWAY_FUNCTION_CHANGED = "GatewayFunctionChangedEvent"
    GATEWAY_MODE_CHANGED = "GatewayModeChangedEvent"
    GATEWAY_SYNCHRONIZATION_ENDED = "GatewaySynchronizationEndedEvent"
    GATEWAY_SYNCHRONIZATION_STARTED = "GatewaySynchronizationStartedEvent"
    INVALID_ADDRESS = "InvalidAddressEvent"
    IO_CHANGED_KEY = "IOChangedKeyEvent"
    OPENDOORS_DISCOVER_COMPLETED = "OpenDoorsDiscoverCompletedEvent"
    OPENDOORS_DISCOVER_FAILED = "OpenDoorsDiscoverFailedEvent"
    OPENDOORS_GENERATE_OAUTH_TOKENS_COMPLETED = (
        "OpenDoorsGenerateOAuthTokensCompletedEvent"
    )
    OPENDOORS_GENERATE_OAUTH_TOKENS_FAILED = "OpenDoorsGenerateOAuthTokensFailedEvent"
    PLACE_CREATED = "PlaceCreatedEvent"
    PLACE_DELETED = "PlaceDeletedEvent"
    PLACE_UPDATED = "PlaceUpdatedEvent"
    PURGE_PARTIAL_RAW_DEVICES = "PurgePartialRawDevicesEvent"
    REFRESH_ALL_DEVICES_STATES_COMPLETED = "RefreshAllDevicesStatesCompletedEvent"
    SETUP_JOB_COMPLETED = "SetupJobCompletedEvent"
    SETUP_JOB_FAILED = "SetupJobFailedEvent"
    SETUP_TRIGGER_TRIGGERED = "SetupTriggerTriggeredEvent"
    SOMFY_PROTECT_GET_SITES_COMPLETED = "SomfyProtectGetSitesCompletedEvent"
    SONOS_GET_TOPOLOGY_SUCCESS = "SonosGetTopologySuccessEvent"
    TOKEN_CREATED = "TokenCreatedEvent"
    TOKEN_CREATION_FAILED = "TokenCreationFailedEvent"
    TOKEN_DELETION_FAILED = "TokenDeletionFailedEvent"
    TOKEN_REMOVED = "TokenRemovedEvent"
    PUSH_SUBSCRIPTION_CREATED = "PushSubscriptionCreatedEvent"
    VALID_ADDRESS = "ValidAddressEvent"
    ZIGBEE_BIND_NETWORK_COMPLETED = "ZigbeeBindNetworkCompletedEvent"
    ZIGBEE_BIND_NETWORK_FAILED = "ZigbeeBindNetworkFailedEvent"
    ZIGBEE_CREATE_NETWORK_COMPLETED = "ZigbeeCreateNetworkCompletedEvent"
    ZIGBEE_CREATE_NETWORK_FAILED = "ZigbeeCreateNetworkFailedEvent"
    ZIGBEE_JOIN_NETWORK_FAILED = "ZigbeeJoinNetworkFailedEvent"
    ZIGBEE_LEAVE_NETWORK_COMPLETED = "ZigbeeLeaveNetworkCompletedEvent"
    ZIGBEE_LEAVE_NETWORK_FAILED = "ZigbeeLeaveNetworkFailedEvent"
    ZIGBEE_REFRESH_NETWORK_COMPLETED = "ZigbeeRefreshNetworkCompletedEvent"

    @classmethod
    def _missing_(cls, value):  # type: ignore
        _LOGGER.warning(f"Unsupported value {value} has been returned for {cls}")
        return cls.UNKNOWN


@unique
class UpdateBoxStatus(str, Enum):
    NOT_UPDATABLE = "NOT_UPDATABLE"
    READY_TO_UPDATE = "READY_TO_UPDATE"
    READY_TO_BE_UPDATED_BY_SERVER = "READY_TO_BE_UPDATED_BY_SERVER"
    READY_TO_UPDATE_LOCALLY = "READY_TO_UPDATE_LOCALLY"
    UP_TO_DATE = "UP_TO_DATE"
    UNKNOWN = "UNKNOWN"
    UPDATING = "UPDATING"


@unique
class CommandMode(str, Enum):
    HIGH_PRIORITY = "highPriority"
    GEOLOCATED = "geolocated"
    INTERNAL = "internal"
