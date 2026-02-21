"""Convenience re-exports for the enums package."""

# Explicitly re-export all Enum subclasses to avoid wildcard import issues
from pyoverkiz.enums.command import CommandMode, OverkizCommand, OverkizCommandParam
from pyoverkiz.enums.execution import (
    ExecutionState,
    ExecutionSubType,
    ExecutionType,
)
from pyoverkiz.enums.gateway import GatewaySubType, GatewayType, UpdateBoxStatus
from pyoverkiz.enums.general import DataType, EventName, FailureType, ProductType
from pyoverkiz.enums.measured_value_type import MeasuredValueType
from pyoverkiz.enums.protocol import Protocol
from pyoverkiz.enums.server import APIType, Server
from pyoverkiz.enums.state import OverkizAttribute, OverkizState
from pyoverkiz.enums.ui import UIClass, UIClassifier, UIWidget
from pyoverkiz.enums.ui_profile import UIProfile

__all__ = [
    "APIType",
    "CommandMode",
    "DataType",
    "EventName",
    "ExecutionState",
    "ExecutionSubType",
    "ExecutionType",
    "FailureType",
    "GatewaySubType",
    "GatewayType",
    "MeasuredValueType",
    "OverkizAttribute",
    "OverkizCommand",
    "OverkizCommandParam",
    "OverkizState",
    "ProductType",
    "Protocol",
    "Server",
    "UIClass",
    "UIClassifier",
    "UIProfile",
    "UIWidget",
    "UpdateBoxStatus",
]
