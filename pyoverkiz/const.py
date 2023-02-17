from __future__ import annotations

from enum import Enum, unique


@unique
class Server(str, Enum):
    ATLANTIC_COZYTOUCH = "atlantic_cozytouch"
    BRANDT = "brandt"
    FLEXOM = "flexom"
    HEXAOM_HEXACONNECT = "hexaom_hexaconnect"
    HI_KUMO_ASIA = "hi_kumo_asia"
    HI_KUMO_EUROPE = "hi_kumo_europe"
    HI_KUMO_OCEANIA = "hi_kumo_oceania"
    NEXITY = "nexity"
    REXEL = "rexel"
    SIMU_LIVEIN2 = "simu_livein2"
    SOMFY_EUROPE = "somfy_europe"
    SOMFY_DEV_MODE = "somfy_dev_mode"
    SOMFY_AMERICA = "somfy_america"
    SOMFY_OCEANIA = "somfy_oceania"
    UBIWIZZ = "ubiwizz"
