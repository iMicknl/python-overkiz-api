"""Main entropoint for the Overkiz API client."""
from __future__ import annotations

from typing import Callable

from aiohttp import ClientSession

from pyoverkiz.clients.atlantic_cozytouch import AtlanticCozytouchClient
from pyoverkiz.clients.default import DefaultClient
from pyoverkiz.clients.nexity import NexityClient
from pyoverkiz.clients.overkiz import OverkizClient
from pyoverkiz.clients.somfy import SomfyClient
from pyoverkiz.clients.somfy_local import SomfyLocalClient
from pyoverkiz.const import Server

SUPPORTED_SERVERS: dict[Server, Callable[[str, str, ClientSession], OverkizClient]] = {
    Server.ATLANTIC_COZYTOUCH: lambda username, password, session: AtlanticCozytouchClient(
        name="Atlantic Cozytouch",
        endpoint="https://ha110-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Atlantic",
        configuration_url=None,
        session=session,
        username=username,
        password=password,
    ),
    Server.BRANDT: lambda username, password, session: DefaultClient(
        name="Brandt Smart Control",
        endpoint="https://ha3-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Brandt",
        configuration_url=None,
        session=session,
        username=username,
        password=password,
    ),
    Server.FLEXOM: lambda username, password, session: DefaultClient(
        name="Flexom",
        endpoint="https://ha108-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Bouygues",
        configuration_url=None,
        session=session,
        username=username,
        password=password,
    ),
    Server.HEXAOM_HEXACONNECT: lambda username, password, session: DefaultClient(
        name="Hexaom HexaConnect",
        endpoint="https://ha5-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hexaom",
        configuration_url=None,
        session=session,
        username=username,
        password=password,
    ),
    Server.HI_KUMO_ASIA: lambda username, password, session: DefaultClient(
        name="Hitachi Hi Kumo (Asia)",
        endpoint="https://ha203-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hitachi",
        configuration_url=None,
        session=session,
        username=username,
        password=password,
    ),
    Server.HI_KUMO_EUROPE: lambda username, password, session: DefaultClient(
        name="Hitachi Hi Kumo (Europe)",
        endpoint="https://ha117-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hitachi",
        configuration_url=None,
        session=session,
        username=username,
        password=password,
    ),
    Server.HI_KUMO_OCEANIA: lambda username, password, session: DefaultClient(
        name="Hitachi Hi Kumo (Oceania)",
        endpoint="https://ha203-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hitachi",
        configuration_url=None,
        session=session,
        username=username,
        password=password,
    ),
    Server.NEXITY: lambda username, password, session: NexityClient(
        name="Nexity Eugénie",
        endpoint="https://ha106-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Nexity",
        configuration_url=None,
        session=session,
        username=username,
        password=password,
    ),
    Server.REXEL: lambda username, password, session: DefaultClient(
        name="Rexel Energeasy Connect",
        endpoint="https://ha112-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Rexel",
        configuration_url="https://utilisateur.energeasyconnect.com/user/#/zone/equipements",
        session=session,
        username=username,
        password=password,
    ),
    Server.SIMU_LIVEIN2: lambda username, password, session: DefaultClient(  # alias of https://tahomalink.com
        name="SIMU (LiveIn2)",
        endpoint="https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
        configuration_url=None,
        session=session,
        username=username,
        password=password,
    ),
    Server.SOMFY_EUROPE: lambda username, password, session: SomfyClient(  # alias of https://tahomalink.com
        name="Somfy (Europe)",
        endpoint="https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
        configuration_url="https://www.tahomalink.com",
        session=session,
        username=username,
        password=password,
    ),
    Server.SOMFY_DEV_MODE: lambda domain, token, session: SomfyLocalClient(
        name="Somfy Developer Mode (Local API)",
        endpoint=f"https://{domain}:8443/enduser-mobile-web/1/enduserAPI/",
        manufacturer="Somfy",
        configuration_url=None,
        session=session,
        token=token,
    ),
    Server.SOMFY_AMERICA: lambda username, password, session: DefaultClient(
        name="Somfy (North America)",
        endpoint="https://ha401-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
        configuration_url=None,
        session=session,
        username=username,
        password=password,
    ),
    Server.SOMFY_OCEANIA: lambda username, password, session: DefaultClient(
        name="Somfy (Oceania)",
        endpoint="https://ha201-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
        configuration_url=None,
        session=session,
        username=username,
        password=password,
    ),
    Server.UBIWIZZ: lambda username, password, session: DefaultClient(
        name="Ubiwizz",
        endpoint="https://ha129-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Decelect",
        configuration_url=None,
        session=session,
        username=username,
        password=password,
    ),
}


class Overkiz:
    @staticmethod
    def create_client(
        server: Server, username: str, password: str, session: ClientSession
    ) -> OverkizClient:
        """Get the client for the given server"""
        return SUPPORTED_SERVERS[server](username, password, session)
