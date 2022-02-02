import logging
from enum import Enum, unique

_LOGGER = logging.getLogger(__name__)


@unique
class Protocol(str, Enum):
    """Protocol used by Overkiz.

    Values have been retrieved from /reference/protocolTypes
    """

    UNKNOWN = "unknown"
    IO = "io"
    RTS = "rts"
    RTD = "rtd"
    RTDS = "rtds"
    RAMSES = "ramses"
    ENOCEAN = "enocean"
    ZWAVE = "zwave"
    CAMERA = "camera"
    OVP = "ovp"
    MODBUS = "modbus"
    MODBUSLINK = "modbuslink"
    HUE = "hue"
    VERISURE = "verisure"
    INTERNAL = "internal"
    JSW = "jsw"
    OPENDOORS = "opendoors"
    MYFOX = "myfox"
    SOMFY_THERMOSTAT = "somfythermostat"
    ZIGBEE = "zigbee"
    UPNP_CONTROL = "upnpcontrol"
    ELIOT = "eliot"
    WISER = "wiser"
    PROFALUX_868 = "profalux868"
    OGP = "ogp"
    HOMEKIT = "homekit"
    AUGUST = "august"
    HLRR_WIFI = "hlrrwifi"
    RTN = "rtn"

    @classmethod
    def _missing_(cls, value):  # type: ignore
        _LOGGER.warning(f"Unsupported protocol {value} has been returned for {cls}")
        return cls.UNKNOWN
