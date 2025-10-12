import sys
from enum import unique

# Since we support Python versions lower than 3.11, we use
# a backport for StrEnum when needed.
if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from backports.strenum import StrEnum


@unique
class APIType(StrEnum):
    CLOUD = "cloud"
    LOCAL = "local"


@unique
class Server(StrEnum):
    ATLANTIC_COZYTOUCH = "atlantic_cozytouch"
    BRANDT = "brandt"
    FLEXOM = "flexom"
    HEXAOM_HEXACONNECT = "hexaom_hexaconnect"
    HI_KUMO_ASIA = "hi_kumo_asia"
    HI_KUMO_EUROPE = "hi_kumo_europe"
    HI_KUMO_OCEANIA = "hi_kumo_oceania"
    NEXITY = "nexity"
    REXEL = "rexel"
    SAUTER_COZYTOUCH = "sauter_cozytouch"
    SIMU_LIVEIN2 = "simu_livein2"
    SOMFY_DEVELOPER_MODE = "somfy_developer_mode"
    SOMFY_EUROPE = "somfy_europe"
    SOMFY_AMERICA = "somfy_america"
    SOMFY_OCEANIA = "somfy_oceania"
    THERMOR_COZYTOUCH = "thermor_cozytouch"
    UBIWIZZ = "ubiwizz"
