from __future__ import annotations

from pyoverkiz.servers.atlantic_cozytouch import AtlanticCozytouch
from pyoverkiz.servers.default import DefaultServer
from pyoverkiz.servers.nexity import NexityServer
from pyoverkiz.servers.overkiz_server import OverkizServer
from pyoverkiz.servers.somfy import SomfyServer

SUPPORTED_SERVERS: dict[str, OverkizServer] = {
    "atlantic_cozytouch": AtlanticCozytouch(
        name="Atlantic Cozytouch",
        endpoint="https://ha110-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Atlantic",
        configuration_url=None,
    ),
    "brandt": DefaultServer(
        name="Brandt Smart Control",
        endpoint="https://ha3-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Brandt",
        configuration_url=None,
    ),
    "flexom": DefaultServer(
        name="Flexom",
        endpoint="https://ha108-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Bouygues",
        configuration_url=None,
    ),
    "hexaom_hexaconnect": DefaultServer(
        name="Hexaom HexaConnect",
        endpoint="https://ha5-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hexaom",
        configuration_url=None,
    ),
    "hi_kumo_asia": DefaultServer(
        name="Hitachi Hi Kumo (Asia)",
        endpoint="https://ha203-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hitachi",
        configuration_url=None,
    ),
    "hi_kumo_europe": DefaultServer(
        name="Hitachi Hi Kumo (Europe)",
        endpoint="https://ha117-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hitachi",
        configuration_url=None,
    ),
    "hi_kumo_oceania": DefaultServer(
        name="Hitachi Hi Kumo (Oceania)",
        endpoint="https://ha203-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hitachi",
        configuration_url=None,
    ),
    "nexity": NexityServer(
        name="Nexity Eugénie",
        endpoint="https://ha106-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Nexity",
        configuration_url=None,
    ),
    "rexel": DefaultServer(
        name="Rexel Energeasy Connect",
        endpoint="https://ha112-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Rexel",
        configuration_url="https://utilisateur.energeasyconnect.com/user/#/zone/equipements",
    ),
    "simu_livein2": DefaultServer(  # alias of https://tahomalink.com
        name="SIMU (LiveIn2)",
        endpoint="https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
        configuration_url=None,
    ),
    "somfy_europe": SomfyServer(  # alias of https://tahomalink.com
        name="Somfy (Europe)",
        endpoint="https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
        configuration_url="https://www.tahomalink.com",
    ),
    "somfy_america": DefaultServer(
        name="Somfy (North America)",
        endpoint="https://ha401-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
        configuration_url=None,
    ),
    "somfy_oceania": DefaultServer(
        name="Somfy (Oceania)",
        endpoint="https://ha201-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
        configuration_url=None,
    ),
    "ubiwizz": DefaultServer(
        name="Ubiwizz",
        endpoint="https://ha129-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Decelect",
        configuration_url=None,
    ),
}
