"""Execution related enums (types, states and subtypes)."""

from enum import StrEnum, unique

from pyoverkiz.enums.base import UnknownEnumMixin


@unique
class ExecutionType(UnknownEnumMixin, StrEnum):
    """High-level execution categories returned by the API."""

    UNKNOWN = "UNKNOWN"
    IMMEDIATE_EXECUTION = "Immediate execution"
    DELAYED_EXECUTION = "Delayed execution"
    TECHNICAL_EXECUTION = "Technical execution"
    PLANNING = "Planning"
    RAW_TRIGGER_SERVER = "Raw trigger (Server)"
    RAW_TRIGGER_GATEWAY = "Raw trigger (Gateway)"


@unique
class ExecutionState(UnknownEnumMixin, StrEnum):
    """Execution lifecycle states."""

    UNKNOWN = "UNKNOWN"
    INITIALIZED = "INITIALIZED"
    NOT_TRANSMITTED = "NOT_TRANSMITTED"
    TRANSMITTED = "TRANSMITTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    QUEUED_GATEWAY_SIDE = "QUEUED_GATEWAY_SIDE"
    QUEUED_SERVER_SIDE = "QUEUED_SERVER_SIDE"


@unique
class ExecutionSubType(UnknownEnumMixin, StrEnum):
    """Subtypes for execution reasons or sources."""

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
