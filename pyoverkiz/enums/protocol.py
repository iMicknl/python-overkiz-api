"""Protocol enums describe device URL schemes used by Overkiz."""

from enum import StrEnum, unique

from pyoverkiz.enums.base import UnknownEnumMixin


@unique
class Protocol(UnknownEnumMixin, StrEnum):
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

    __missing_message__ = "Unsupported protocol %s has been returned for %s"
