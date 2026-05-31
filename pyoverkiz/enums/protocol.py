"""Protocol enums describe device URL schemes used by Overkiz.

THIS FILE IS AUTO-GENERATED. DO NOT EDIT MANUALLY.
Run `uv run utils/generate_enums.py` to regenerate.
"""

from enum import StrEnum, unique

from pyoverkiz.enums.base import UnknownEnumMixin


@unique
class Protocol(UnknownEnumMixin, StrEnum):
    """Protocol used by Overkiz.

    Values have been retrieved from /reference/protocolTypes
    """

    UNKNOWN = "unknown"

    ARISTON = "ariston"  # 49: Ariston Webservices
    AUGUST = "august"  # 59: August Webservices
    AURORA = "aurora"  # 34: Aurora protocol
    CAMERA = "camera"  # 13: Generic Camera Control Protocol
    DEDIETRICHSTC = "dedietrichstc"  # 58: De Dietrich SmartTC Webservices
    DELTADORE = "deltadore"  # 57: Deltadore Webservices
    ELIOT = "eliot"  # 45: Eliot Webservices
    ENOCEAN = "enocean"  # 7: EnOcean
    HLRR_WIFI = "hlrrwifi"  # 31: Hitachi HLink Protocol (Wifi Bridge)
    HOMEKIT = "homekit"  # 48: HOMEKIT
    HUE = "hue"  # 22: Philips HUE - Personal Wireless Lighting
    INTERNAL = "internal"  # 29: Kizbox Internal Modules
    IO = "io"  # 1: IO HomeControl©
    JSW = "jsw"  # 30: JSW Webservices
    KNX = "knx"  # 21: KNX
    MODBUS = "modbus"  # 20: Modbus
    MODBUSLINK = "modbuslink"  # 44: ModbusLink
    MYFOX = "myfox"  # 25: MyFox Webservices
    NEST = "nest"  # 41: Nest Webservices
    NETATMO = "netatmo"  # 38: Netatmo Webservices
    OGCP = "ogcp"  # 62: Overkiz Generic Cloud Protocol
    OGP = "ogp"  # 56: Overkiz Generic Protocol
    OPENDOORS = "opendoors"  # 35: OpenDoors Webservices
    OVP = "ovp"  # 14: OVERKIZ Radio Protocol
    PROFALUX_868 = "profalux868"  # 50: Profalux 868
    RAMSES = "ramses"  # 6: Ramses II (Honeywell)
    RTD = "rtd"  # 5: Domis RTD - Actuator
    RTDS = "rtds"  # 11: Domis RTD - Sensor
    RTN = "rtn"
    RTS = "rts"  # 2: Somfy RTS
    SOMFY_THERMOSTAT = "somfythermostat"  # 39: Somfy Thermostat Webservice
    SONOS = "sonos"  # 52: Sonos Cloud Protocol
    UPNP_CONTROL = "upnpcontrol"  # 43: UPnP Control
    URMET = "urmet"  # 42: Urmet Webservices
    VERISURE = "verisure"  # 23: Verisure Webservices
    WISER = "wiser"  # 54: Schneider Wiser
    YOKIS = "yokis"  # 27: Yokis
    ZIGBEE = "zigbee"  # 3: Zigbee
    ZWAVE = "zwave"  # 8: Z-Wave
