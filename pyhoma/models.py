from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Iterator, List, Optional

# pylint: disable=unused-argument, too-many-instance-attributes


class Device:
    __slots__ = (
        "id",
        "attributes",
        "controllable_name",
        "creation_time",
        "last_update_time",
        "label",
        "deviceurl",
        "shortcut",
        "controllable_name",
        "definition",
        "states",
        "data_properties",
        "available",
        "enabled",
        "widget",
        "ui_class",
        "qualified_name",
        "type",
    )

    def __init__(
        self,
        *,
        attributes: Optional[List[Dict[str, Any]]] = None,
        available: bool,
        enabled: bool,
        label: str,
        deviceurl: str,
        controllable_name: str,
        definition: Dict[str, Any],
        data_properties: Optional[List[Dict[str, Any]]] = None,
        widget: Optional[str] = None,
        ui_class: Optional[str] = None,
        qualified_name: Optional[str] = None,
        states: Optional[List[Dict[str, Any]]] = None,
        type: int,
        **_: Any
    ) -> None:
        self.id = deviceurl
        self.attributes = States(attributes) if attributes else None
        self.available = available
        self.definition = Definition(**definition)
        self.deviceurl = deviceurl
        self.enabled = enabled
        self.label = label
        self.controllable_name = controllable_name
        self.states = States(states) if states else None
        self.data_properties = data_properties
        self.widget = widget
        self.ui_class = ui_class
        self.qualified_name = qualified_name
        self.type = ProductType(type)


class Definition:
    __slots__ = ("commands", "states", "widget_name", "ui_class", "qualified_name")

    def __init__(
        self,
        *,
        commands: List[Dict[str, Any]],
        states: Optional[List[Dict[str, Any]]] = None,
        widget_name: Optional[str] = None,
        ui_class: Optional[str] = None,
        qualified_name: str,
        **_: Any
    ) -> None:
        self.commands = CommandDefinitions(commands)
        self.states = [StateDefinition(**sd) for sd in states] if states else None
        self.widget_name = widget_name
        self.ui_class = ui_class
        self.qualified_name = qualified_name


class StateDefinition:
    __slots__ = (
        "qualified_name",
        "type",
        "values",
    )

    def __init__(
        self,
        qualified_name: str,
        type: str,
        values: Optional[List[str]] = None,
        **_: Any
    ) -> None:
        self.qualified_name = qualified_name
        self.type = type
        self.values = values


class CommandDefinition:
    __slots__ = (
        "command_name",
        "nparams",
    )

    def __init__(self, command_name: str, nparams: int, **_: Any) -> None:
        self.command_name = command_name
        self.nparams = nparams


class CommandDefinitions:
    def __init__(self, commands: List[Dict[str, Any]]):
        self._commands = [CommandDefinition(**command) for command in commands]

    def __iter__(self) -> Iterator[CommandDefinition]:
        return self._commands.__iter__()

    def __contains__(self, name: str) -> bool:
        return self.__getitem__(name) is not None

    def __getitem__(self, command: str) -> Optional[CommandDefinition]:
        return next((cd for cd in self._commands if cd.command_name == command), None)

    def __len__(self) -> int:
        return len(self._commands)

    get = __getitem__


class State:
    __slots__ = "name", "value", "type"

    def __init__(self, name: str, type: int, value: Optional[str] = None, **_: Any):
        self.name = name
        self.value = value
        self.type = DataType(type)


class States:
    def __init__(self, states: List[Dict[str, Any]]) -> None:
        self._states = [State(**state) for state in states]

    def __iter__(self) -> Iterator[State]:
        return self._states.__iter__()

    def __contains__(self, name: str) -> bool:
        return self.__getitem__(name) is not None

    def __getitem__(self, name: str) -> Optional[State]:
        return next((state for state in self._states if state.name == name), None)

    def __setitem__(self, name: str, state: State) -> None:
        found = self.__getitem__(name)
        if found is None:
            self._states.append(state)
        else:
            self._states[self._states.index(found)] = state

    def __len__(self) -> int:
        return len(self._states)

    get = __getitem__


class Command(dict):  # type: ignore
    """Represents an TaHoma Command."""

    __slots__ = (
        "name",
        "parameters",
    )

    def __init__(self, name: str, parameters: Optional[str] = None, **_: Any):
        self.name = name
        self.parameters = parameters
        dict.__init__(self, name=name, parameters=parameters)


class CommandMode(Enum):
    high_priority = ("highPriority",)
    geolocated = ("geolocated",)
    internal = "internal"


# pylint: disable-msg=too-many-locals
class Event:
    __slots__ = (
        "timestamp",
        "name",
        "gateway_id",
        "exec_id",
        "deviceurl",
        "device_states",
        "old_state",
        "new_state",
        "owner_key",
        "setupoid",
        "owner_key",
        "type",
        "sub_type",
        "time_to_next_state",
        "failed_commands",
        "failure_type_code",
        "failure_type",
        "condition_groupoid",
        "placeoid",
        "label",
        "metadata",
        "camera_id",
        "deleted_raw_devices_count",
        "protocol_type",
    )

    def __init__(
        self,
        timestamp: int,
        name: EventName,
        setupoid: Optional[str] = None,
        owner_key: Optional[str] = None,
        type: Optional[int] = None,
        sub_type: Optional[int] = None,
        time_to_next_state: Optional[int] = None,
        failed_commands: Optional[List[Dict[str, Any]]] = None,
        failure_type_code: Optional[int] = None,
        failure_type: Optional[str] = None,
        condition_groupoid: Optional[str] = None,
        placeoid: Optional[str] = None,
        label: Optional[str] = None,
        metadata: Optional[Any] = None,
        camera_id: Optional[str] = None,
        deleted_raw_devices_count: Optional[Any] = None,
        protocol_type: Optional[Any] = None,
        gateway_id: Optional[str] = None,
        exec_id: Optional[str] = None,
        deviceurl: Optional[str] = None,
        device_states: Optional[List[Dict[str, Any]]] = None,
        old_state: Optional[ExecutionState] = None,
        new_state: Optional[ExecutionState] = None,
        **_: Any
    ):
        self.timestamp = timestamp
        self.name = EventName(name)
        self.gateway_id = gateway_id
        self.exec_id = exec_id
        self.deviceurl = deviceurl
        self.device_states = (
            [State(**s) for s in device_states] if device_states else None
        )
        self.old_state = ExecutionState(old_state) if old_state else None
        self.new_state = ExecutionState(new_state) if new_state else None
        self.setupoid = setupoid
        self.owner_key = owner_key
        self.type = ExecutionType(type) if type else None
        self.sub_type = ExecutionSubType(sub_type) if sub_type else None
        self.time_to_next_state = time_to_next_state
        self.failed_commands = failed_commands
        self.failure_type_code = (
            FailureType(failure_type_code) if failure_type_code else None
        )
        self.failure_type = failure_type
        self.condition_groupoid = condition_groupoid
        self.placeoid = placeoid
        self.label = label
        self.metadata = metadata
        self.camera_id = camera_id
        self.deleted_raw_devices_count = deleted_raw_devices_count
        self.protocol_type = protocol_type


class Execution:

    __slots__ = (
        "id",
        "description",
        "owner",
        "state",
        "action_group",
    )

    def __init__(
        self,
        id: str,
        description: str,
        owner: str,
        state: str,
        action_group: List[Dict[str, Any]],
        **_: Any
    ):
        self.id = id
        self.description = description
        self.owner = owner
        self.state = state
        self.action_group = action_group


class Scenario:
    __slots__ = ("label", "oid")

    def __init__(self, label: str, oid: str, **_: Any):
        self.label = label
        self.oid = oid


class Partner:
    __slots__ = ("activated", "name", "id", "status")

    def __init__(self, activated: bool, name: str, id: str, status: str, **_: Any):
        self.activated = activated
        self.name = name
        self.id = id
        self.status = status


class Connectivity:
    __slots__ = ("status", "protocol_version")

    def __init__(self, status: str, protocol_version: str, **_: Any):
        self.status = status
        self.protocol_version = protocol_version


class Gateway:
    __slots__ = (
        "id",
        "partners",
        "functions",
        "sub_type",
        "gateway_id",
        "alive",
        "mode",
        "placeoid",
        "time_reliable",
        "connectivity",
        "up_to_date",
        "update_status",
        "sync_in_progress",
        "type",
    )

    def __init__(
        self,
        *,
        partners: List[Dict[str, Any]],
        functions: Optional[str],
        sub_type: GatewaySubType,
        gateway_id: str,
        alive: bool,
        mode: str,
        placeoid: str,
        time_reliable: bool,
        connectivity: Dict[str, Any],
        up_to_date: bool,
        update_status: UpdateBoxStatus,
        sync_in_progress: bool,
        type: GatewayType,
        **_: Any
    ) -> None:
        self.id = gateway_id
        self.type = GatewayType(type)
        self.sub_type = GatewaySubType(sub_type)
        self.functions = functions
        self.alive = alive
        self.mode = mode
        self.placeoid = placeoid
        self.time_reliable = time_reliable
        self.connectivity = Connectivity(*connectivity)
        self.up_to_date = up_to_date
        self.update_status = UpdateBoxStatus(update_status)
        self.sync_in_progress = sync_in_progress
        self.partners = [Partner(**p) for p in partners]


class ProductType(Enum):
    NONE = 0
    ACTUATOR = 1
    SENSOR = 2
    VIDEO = 3
    CONTROLLABLE = 4
    GATEWAY = 5
    INFRASTRUCTURE_COMPONENT = 6


class GatewayType(Enum):
    VIRTUAL_KIZBOX = 0
    KIZBOX_V1 = 2
    TAHOMA = 15
    TAHOMA_V2 = 29
    KIZBOX_V2_3H = 30
    KIZBOX_V2_2H = 31
    TAHOMA_V2_RTS = 41
    VERISURE_ALARM_SYSTEM = 20
    CONNEXOON = 34
    CONNEXOON_RTS = 53
    CONNEXOON_RTS_JAPAN = 56
    CONNEXOON_RTS_AUSTRALIA = 62
    JSW_CAMERA = 35
    OPENDOORS_LOCK_SYSTEM = 54
    HOME_PROTECT_SYSTEM = 58
    THERMOSTAT_SOMFY_SYSTEM = 63
    TAHOMA_BEE = 67
    TAHOMA_RAIL_DIN = 72
    ELIOT = 77
    WISER = 88


class GatewaySubType(Enum):
    TAHOMA_BASIC = 1
    TAHOMA_BASIC_PLUS = 2
    TAHOMA_PREMIUM = 3
    SOMFY_BOX = 4
    HITACHI_BOX = 5
    MONDIAL_BOX = 6
    MAROC_TELECOM_BOX = 7
    TAHOMA_SERENITY = 8
    TAHOMA_VERISURE = 9
    TAHOMA_SERENITY_PREMIUM = 10
    TAHOMA_MONSIEUR_STORE = 11
    TAHOMA_MAISON_AVENIR_ET_TRADITION = 12
    TAHOMA_SHORT_CHANNEL = 13
    TAHOMA_PRO = 14
    TAHOMA_SECURITY_SHORT_CHANNEL = 15
    TAHOMA_SECURITY_PRO = 16
    TAHOMA_BOX_C_IO = 12


class DataType(Enum):
    NONE = 0
    INTEGER = 1
    FLOAT = 2
    STRING = 3
    BLOB = 4
    DATE = 5
    BOOLEAN = 6
    JSON_ARRAY = 10
    JSON_OBJECT = 11


class ExecutionType(Enum):
    IMMEDIATE_EXECUTION = "Immediate execution"
    DELAYED_EXECUTION = "Delayed execution"
    TECHNICAL_EXECUTION = "Technical execution"
    PLANNING = "Planning"
    RAW_TRIGGER_SERVER = "Raw trigger (Server)"
    RAW_TRIGGER_GATEWAY = "Raw trigger (Gateway)"


class ExecutionState(Enum):
    INITIALIZED = "INITIALIZED"
    NOT_TRANSMITTED = "NOT_TRANSMITTED"
    TRANSMITTED = "TRANSMITTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    QUEUED_GATEWAY_SIDE = "QUEUED_GATEWAY_SIDE"
    QUEUED_SERVER_SIDE = "QUEUED_SERVER_SIDE"


class ExecutionSubType(Enum):
    MANUAL_CONTROL = "MANUAL_CONTROL"
    ACTION_GROUP = "ACTION_GROUP"
    ACTION_GROUP_SEQUENCE = "ACTION_GROUP_SEQUENCE"
    INTERNAL = "INTERNAL"
    NO_ERROR = "NO_ERROR"
    P2P_COMMAND_REGULATION = "P2P_COMMAND_REGULATION"
    IFT_CONDITION = "IFT_CONDITION"
    TIME_TRIGGER = "TIME_TRIGGER"
    DISCRETE_TRIGGER_USER = "DISCRETE_TRIGGER_USER"


class FailureType(Enum):
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


class EventName(Enum):
    ACTION_GROUP_CREATED = "ActionGroupCreatedEvent"
    ACTION_GROUP_DELETED = "ActionGroupDeletedEvent"
    ACTION_GROUP_UPDATED = "ActionGroupUpdatedEvent"
    CAMERA_DISCOVERED = "CameraDiscoveredEvent"
    CAMERA_DISCOVER_FAILED = "CameraDiscoverFailedEvent"
    CAMERA_UPLOAD_PHOTO = "CameraUploadPhotoEvent"
    CONDITION_GROUP_CREATED = "ConditionGroupCreatedEvent"
    CONDITION_GROUP_DELETED = "ConditionGroupDeletedEvent"
    CONDITION_GROUP_UPDATED = "ConditionGroupUpdatedEvent"
    DELAYED_TRIGGER_CANCELLED = "DelayedTriggerCancelledEvent"
    DEVICE_AVAILABLE = "DeviceAvailableEvent"
    DEVICE_CREATED = "DeviceCreatedEvent"
    DEVICE_DELETION_FAILED = "DeviceDeletionFailedEvent"
    DEVICE_DISABLED = "DeviceDisabledEvent"
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
    ENOCEAN_BAD_DEVICE_STIMULATION = "EnOceanBadDeviceStimulationEvent"
    ENOCEAN_KNOWN_DEVICE_FOUND = "EnOceanKnownDeviceFoundEvent"
    ENOCEAN_LEARN_STARTED = "EnOceanLearnStartedEvent"
    ENOCEAN_LEARN_STOPPED = "EnOceanLearnStoppedEvent"
    EXECUTION_REGISTERED = "ExecutionRegisteredEvent"
    EXECUTION_STATE_CHANGED = "ExecutionStateChangedEvent"
    GATEWAY_ALIVE = "GatewayAliveEvent"
    GATEWAY_DOWN = "GatewayDownEvent"
    GATEWAY_FUNCTION_CHANGED = "GatewayFunctionChangedEvent"
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
    SONOS_GET_TOPOLOGY_SUCCESS = "SonosGetTopologySuccessEvent"
    TOKEN_CREATED = "TokenCreatedEvent"
    TOKEN_CREATION_FAILED = "TokenCreationFailedEvent"
    TOKEN_DELETION_FAILED = "TokenDeletionFailedEvent"
    TOKEN_REMOVED = "TokenRemovedEvent"
    VALID_ADDRESS = "ValidAddressEvent"


class UpdateBoxStatus(Enum):
    NOT_UPDATABLE = "NOT_UPDATABLE"
    READY_TO_UPDATE = "READY_TO_UPDATE"
    READY_TO_BE_UPDATED_BY_SERVER = "READY_TO_BE_UPDATED_BY_SERVER"
    READY_TO_UPDATE_LOCALLY = "READY_TO_UPDATE_LOCALLY"
    UP_TO_DATE = "UP_TO_DATE"
    UNKNOWN = "UNKNOWN"
