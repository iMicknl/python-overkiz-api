import logging
import sys
from enum import unique

_LOGGER = logging.getLogger(__name__)

# Since we support Python versions lower than 3.11, we use
# a backport for StrEnum when needed.
if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from backports.strenum import StrEnum


@unique
class Protocol(StrEnum):
    """Protocol used by Overkiz.

    Values have been retrieved from /reference/protocolTypes
    """

    UNKNOWN = "unknown"

    AUGUST = "august"
    CAMERA = "camera"
    ELIOT = "eliot"
    ENOCEAN = "enocean"
    HLRR_WIFI = "hlrrwifi"
    HOMEKIT = "homekit"
    HUE = "hue"
    INTERNAL = "internal"
    IO = "io"
    JSW = "jsw"
    MODBUS = "modbus"
    MODBUSLINK = "modbuslink"
    MYFOX = "myfox"
    NETATMO = "netatmo"
    OGCP = "ogcp"
    OGP = "ogp"
    OPENDOORS = "opendoors"
    OVP = "ovp"
    PROFALUX_868 = "profalux868"
    RAMSES = "ramses"
    RTD = "rtd"
    RTDS = "rtds"
    RTN = "rtn"
    RTS = "rts"
    SOMFY_THERMOSTAT = "somfythermostat"
    UPNP_CONTROL = "upnpcontrol"
    VERISURE = "verisure"
    WISER = "wiser"
    ZIGBEE = "zigbee"
    ZWAVE = "zwave"

    @classmethod
    def _missing_(cls, value):  # type: ignore
        _LOGGER.warning(f"Unsupported protocol {value} has been returned for {cls}")
        return cls.UNKNOWN
