"""Server and API type enums used to select target Overkiz endpoints."""

from enum import StrEnum, unique


@unique
class APIType(StrEnum):
    """API types supported by the client (cloud or local)."""

    CLOUD = "cloud"
    LOCAL = "local"


@unique
class Server(StrEnum):
    """Known named Overkiz server endpoints."""

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
