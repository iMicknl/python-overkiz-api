from enum import Enum, unique


@unique
class Protocol(str, Enum):
    """Protocol used by Overkiz.

    Values have been retrieved from /reference/protocolTypes
    """

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
