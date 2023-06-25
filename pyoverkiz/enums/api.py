from enum import Enum, unique


@unique
class APIType(str, Enum):
    CLOUD = "cloud"
    LOCAL = "local"
