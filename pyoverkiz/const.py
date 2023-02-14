from __future__ import annotations

from typing import Callable

from aiohttp import ClientSession

from pyoverkiz.servers.atlantic_cozytouch import AtlanticCozytouch
from pyoverkiz.servers.default import DefaultServer
from pyoverkiz.servers.nexity import NexityServer
from pyoverkiz.servers.overkiz_server import OverkizServer
from pyoverkiz.servers.somfy import SomfyServer

SUPPORTED_SERVERS: dict[str, Callable[[ClientSession], OverkizServer]] = {
    "atlantic_cozytouch": lambda session: AtlanticCozytouch(
        name="Atlantic Cozytouch",
        endpoint="https://ha110-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Atlantic",
        configuration_url=None,
        session=session,
    ),
    "brandt": lambda session: DefaultServer(
        name="Brandt Smart Control",
        endpoint="https://ha3-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Brandt",
        configuration_url=None,
        session=session,
    ),
    "flexom": lambda session: DefaultServer(
        name="Flexom",
        endpoint="https://ha108-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Bouygues",
        configuration_url=None,
        session=session,
    ),
    "hexaom_hexaconnect": lambda session: DefaultServer(
        name="Hexaom HexaConnect",
        endpoint="https://ha5-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hexaom",
        configuration_url=None,
        session=session,
    ),
    "hi_kumo_asia": lambda session: DefaultServer(
        name="Hitachi Hi Kumo (Asia)",
        endpoint="https://ha203-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hitachi",
        configuration_url=None,
        session=session,
    ),
    "hi_kumo_europe": lambda session: DefaultServer(
        name="Hitachi Hi Kumo (Europe)",
        endpoint="https://ha117-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hitachi",
        configuration_url=None,
        session=session,
    ),
    "hi_kumo_oceania": lambda session: DefaultServer(
        name="Hitachi Hi Kumo (Oceania)",
        endpoint="https://ha203-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hitachi",
        configuration_url=None,
        session=session,
    ),
    "nexity": lambda session: NexityServer(
        name="Nexity Eugénie",
        endpoint="https://ha106-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Nexity",
        configuration_url=None,
        session=session,
    ),
    "rexel": lambda session: DefaultServer(
        name="Rexel Energeasy Connect",
        endpoint="https://ha112-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Rexel",
        configuration_url="https://utilisateur.energeasyconnect.com/user/#/zone/equipements",
        session=session,
    ),
    "simu_livein2": lambda session: DefaultServer(  # alias of https://tahomalink.com
        name="SIMU (LiveIn2)",
        endpoint="https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
        configuration_url=None,
        session=session,
    ),
    "somfy_europe": lambda session: SomfyServer(  # alias of https://tahomalink.com
        name="Somfy (Europe)",
        endpoint="https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
        configuration_url="https://www.tahomalink.com",
        session=session,
    ),
    "somfy_america": lambda session: DefaultServer(
        name="Somfy (North America)",
        endpoint="https://ha401-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
        configuration_url=None,
        session=session,
    ),
    "somfy_oceania": lambda session: DefaultServer(
        name="Somfy (Oceania)",
        endpoint="https://ha201-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
        configuration_url=None,
        session=session,
    ),
    "ubiwizz": lambda session: DefaultServer(
        name="Ubiwizz",
        endpoint="https://ha129-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Decelect",
        configuration_url=None,
        session=session,
    ),
}
