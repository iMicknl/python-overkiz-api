import logging
from enum import Enum, unique

_LOGGER = logging.getLogger(__name__)


@unique
class ExecutionType(str, Enum):
    UNKNOWN = "UNKNOWN"
    IMMEDIATE_EXECUTION = "Immediate execution"
    DELAYED_EXECUTION = "Delayed execution"
    TECHNICAL_EXECUTION = "Technical execution"
    PLANNING = "Planning"
    RAW_TRIGGER_SERVER = "Raw trigger (Server)"
    RAW_TRIGGER_GATEWAY = "Raw trigger (Gateway)"

    @classmethod
    def _missing_(cls, value):  # type: ignore
        _LOGGER.warning(f"Unsupported value {value} has been returned for {cls}")
        return cls.UNKNOWN


@unique
class ExecutionState(str, Enum):
    UNKNOWN = "UNKNOWN"
    INITIALIZED = "INITIALIZED"
    NOT_TRANSMITTED = "NOT_TRANSMITTED"
    TRANSMITTED = "TRANSMITTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    QUEUED_GATEWAY_SIDE = "QUEUED_GATEWAY_SIDE"
    QUEUED_SERVER_SIDE = "QUEUED_SERVER_SIDE"

    @classmethod
    def _missing_(cls, value):  # type: ignore
        _LOGGER.warning(f"Unsupported value {value} has been returned for {cls}")
        return cls.UNKNOWN


@unique
class ExecutionSubType(str, Enum):
    UNKNOWN = "UNKNOWN"
    _ = "-"
    ACTION_GROUP = "ACTION_GROUP"
    ACTION_GROUP_SEQUENCE = "ACTION_GROUP_SEQUENCE"
    DAWN_TRIGGER = "DAWN_TRIGGER"
    DUSK_TRIGGER = "DUSK_TRIGGER"
    DISCRETE_TRIGGER = "DISCRETE_TRIGGER"
    DISCRETE_TRIGGER_USER = "DISCRETE_TRIGGER_USER"
    GENERIC_COMMAND_SCHEDULING = "GENERIC_COMMAND_SCHEDULING"
    IFT_CONDITION = "IFT_CONDITION"
    INTERNAL = "INTERNAL"
    MANUAL_CONTROL = "MANUAL_CONTROL"
    NO_ERROR = "NO_ERROR"
    P2P_COMMAND_REGULATION = "P2P_COMMAND_REGULATION"
    TIME_TRIGGER = "TIME_TRIGGER"

    @classmethod
    def _missing_(cls, value):  # type: ignore
        _LOGGER.warning(f"Unsupported value {value} has been returned for {cls}")
        return cls.UNKNOWN
