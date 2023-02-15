from __future__ import annotations

from typing import Callable

from aiohttp import ClientSession

from pyoverkiz.clients.atlantic_cozytouch import AtlanticCozytouchClient
from pyoverkiz.clients.default import DefaultClient
from pyoverkiz.clients.nexity import NexityClient
from pyoverkiz.clients.overkiz import OverkizClient
from pyoverkiz.clients.somfy import SomfyClient

SUPPORTED_SERVERS: dict[str, Callable[[str, str, ClientSession], OverkizClient]] = {
    "atlantic_cozytouch": lambda username, password, session: AtlanticCozytouchClient(
        name="Atlantic Cozytouch",
        endpoint="https://ha110-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Atlantic",
        configuration_url=None,
        session=session,
        username=username,
        password=password,
    ),
    "brandt": lambda username, password, session: DefaultClient(
        name="Brandt Smart Control",
        endpoint="https://ha3-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Brandt",
        configuration_url=None,
        session=session,
        username=username,
        password=password,
    ),
    "flexom": lambda username, password, session: DefaultClient(
        name="Flexom",
        endpoint="https://ha108-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Bouygues",
        configuration_url=None,
        session=session,
        username=username,
        password=password,
    ),
    "hexaom_hexaconnect": lambda username, password, session: DefaultClient(
        name="Hexaom HexaConnect",
        endpoint="https://ha5-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hexaom",
        configuration_url=None,
        session=session,
        username=username,
        password=password,
    ),
    "hi_kumo_asia": lambda username, password, session: DefaultClient(
        name="Hitachi Hi Kumo (Asia)",
        endpoint="https://ha203-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hitachi",
        configuration_url=None,
        session=session,
        username=username,
        password=password,
    ),
    "hi_kumo_europe": lambda username, password, session: DefaultClient(
        name="Hitachi Hi Kumo (Europe)",
        endpoint="https://ha117-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hitachi",
        configuration_url=None,
        session=session,
        username=username,
        password=password,
    ),
    "hi_kumo_oceania": lambda username, password, session: DefaultClient(
        name="Hitachi Hi Kumo (Oceania)",
        endpoint="https://ha203-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hitachi",
        configuration_url=None,
        session=session,
        username=username,
        password=password,
    ),
    "nexity": lambda username, password, session: NexityClient(
        name="Nexity Eugénie",
        endpoint="https://ha106-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Nexity",
        configuration_url=None,
        session=session,
        username=username,
        password=password,
    ),
    "rexel": lambda username, password, session: DefaultClient(
        name="Rexel Energeasy Connect",
        endpoint="https://ha112-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Rexel",
        configuration_url="https://utilisateur.energeasyconnect.com/user/#/zone/equipements",
        session=session,
        username=username,
        password=password,
    ),
    "simu_livein2": lambda username, password, session: DefaultClient(  # alias of https://tahomalink.com
        name="SIMU (LiveIn2)",
        endpoint="https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
        configuration_url=None,
        session=session,
        username=username,
        password=password,
    ),
    "somfy_europe": lambda username, password, session: SomfyClient(  # alias of https://tahomalink.com
        name="Somfy (Europe)",
        endpoint="https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
        configuration_url="https://www.tahomalink.com",
        session=session,
        username=username,
        password=password,
    ),
    "somfy_america": lambda username, password, session: DefaultClient(
        name="Somfy (North America)",
        endpoint="https://ha401-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
        configuration_url=None,
        session=session,
        username=username,
        password=password,
    ),
    "somfy_oceania": lambda username, password, session: DefaultClient(
        name="Somfy (Oceania)",
        endpoint="https://ha201-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
        configuration_url=None,
        session=session,
        username=username,
        password=password,
    ),
    "ubiwizz": lambda username, password, session: DefaultClient(
        name="Ubiwizz",
        endpoint="https://ha129-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Decelect",
        configuration_url=None,
        session=session,
        username=username,
        password=password,
    ),
}
