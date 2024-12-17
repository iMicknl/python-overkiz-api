import logging
import sys
from enum import IntEnum, unique

_LOGGER = logging.getLogger(__name__)

# Since we support Python versions lower than 3.11, we use
# a backport for StrEnum when needed.
if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from backports.strenum import StrEnum


@unique
class GatewayType(IntEnum):
    UNKNOWN = -1
    VIRTUAL_KIZBOX = 0
    KIZBOX_V1 = 2
    TAHOMA = 15
    VERISURE_ALARM_SYSTEM = 20
    KIZBOX_MINI = 21
    HI_KUMO_ADAPTER = 22  # Hi Kumo Adapter SPX-WFG01 (constant added manually)
    KIZBOX_V2 = 24
    MYFOX_ALARM_SYSTEM = 25
    KIZBOX_MINI_VMBUS = 27
    KIZBOX_MINI_IO = 28
    TAHOMA_V2 = 29
    KIZBOX_V2_3H = 30
    KIZBOX_V2_2H = 31
    COZYTOUCH = 32
    CONNEXOON = 34
    JSW_CAMERA = 35
    TAHOMA_V2_RTS = 41
    KIZBOX_MINI_MODBUS = 42
    KIZBOX_MINI_OVP = 43
    HI_BOX = 44  # Hi Kumo AHP-SMB01 Hi Box (constant added manually)
    HATTARA_RAIL_DIN = 47
    WIZZ_BOX = 52
    CONNEXOON_RTS = 53
    OPENDOORS_LOCK_SYSTEM = 54
    CONNEXOON_RTS_JAPAN = 56
    ENERGEASY_CONNECT = 57
    HOME_PROTECT_SYSTEM = 58
    CONNEXOON_RTS_AUSTRALIA = 62
    THERMOSTAT_SOMFY_SYSTEM = 63
    SMARTLY_MINI_DAUGHTERBOARD_ZWAVE = 65
    SMARTLY_MINIBOX_RAILDIN = 66
    TAHOMA_BEE = 67
    TAHOMA_RAIL_DIN = 72
    NEXITY_RAIL_DIN = 74
    TAHOMA_BEECON = 75
    ELIOT = 77
    COZYTOUCH_SAUTER = 83
    WISER = 88
    NETATMO = 92
    TAHOMA_SWITCH = 98
    SOMFY_CONNECTIVITY_KIT = 99
    COZYTOUCH_V2 = 105
    TAHOMA_RAIL_DIN_S = 108
    NEXITY_RAIL_DIN_S = 109
    HEXACONNECT = 117
    DAIKIN_ONECTA = 118
    TAHOMA_SWITCH_US = 121
    TAHOMA_SWITCH_OC = 122
    TAHOMA_SWITCH_AU = 123
    TAHOMA_SWITCH_CH = 126
    TAHOMA_SWITCH_SC = 128

    @classmethod
    def _missing_(cls, value):  # type: ignore
        _LOGGER.warning(f"Unsupported value {value} has been returned for {cls}")
        return cls.UNKNOWN

    @property
    def beautify_name(self) -> str:
        name = self.name.replace("_", " ").title()
        name = name.replace("Tahoma", "TaHoma")
        name = name.replace("Rts", "RTS")
        return name


@unique
class GatewaySubType(IntEnum):
    UNKNOWN = -1
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
    # TAHOMA_BOX_C_IO = 12 That’s probably 17, but tahomalink.com says it’s 12

    @classmethod
    def _missing_(cls, value):  # type: ignore
        _LOGGER.warning(f"Unsupported value {value} has been returned for {cls}")
        return cls.UNKNOWN

    @property
    def beautify_name(self) -> str:
        name = self.name.replace("_", " ").title()
        name = name.replace("Tahoma", "TaHoma")
        name = name.replace("Rts", "RTS")
        return name


@unique
class UpdateBoxStatus(StrEnum):
    NOT_UPDATABLE = "NOT_UPDATABLE"
    READY_TO_UPDATE = "READY_TO_UPDATE"
    READY_TO_BE_UPDATED_BY_SERVER = "READY_TO_BE_UPDATED_BY_SERVER"
    READY_TO_UPDATE_LOCALLY = "READY_TO_UPDATE_LOCALLY"
    UP_TO_DATE = "UP_TO_DATE"
    UNKNOWN = "UNKNOWN"
    UPDATING = "UPDATING"
