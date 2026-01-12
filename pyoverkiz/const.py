"""Constants and server descriptors used across the package."""

from __future__ import annotations

from pyoverkiz.enums import Server
from pyoverkiz.enums.server import APIType
from pyoverkiz.models import ServerConfig

COZYTOUCH_ATLANTIC_API = "https://apis.groupe-atlantic.com"
COZYTOUCH_CLIENT_ID = (
    "Q3RfMUpWeVRtSUxYOEllZkE3YVVOQmpGblpVYToyRWNORHpfZHkzNDJVSnFvMlo3cFNKTnZVdjBh"
)

NEXITY_API = "https://api.egn.prd.aws-nexity.fr"
NEXITY_COGNITO_CLIENT_ID = "3mca95jd5ase5lfde65rerovok"
NEXITY_COGNITO_USER_POOL = "eu-west-1_wj277ucoI"
NEXITY_COGNITO_REGION = "eu-west-1"

REXEL_BACKEND_API = (
    "https://app-ec-backend-enduser-prod.azurewebsites.net/api/enduser/overkiz/"
)
REXEL_OAUTH_CLIENT_ID = "2b635ede-c3fb-43bc-8d23-f6d17f80e96d"
REXEL_OAUTH_SCOPE = "https://adb2cservicesfrenduserprod.onmicrosoft.com/94f05108-65f7-477a-a84d-e67e1aed6f79/ExternalProvider"
REXEL_OAUTH_TENANT = (
    "https://consumerlogin.rexelservices.fr/670998c0-f737-4d75-a32f-ba9292755b70"
)
REXEL_OAUTH_POLICY = "B2C_1A_SIGNINONLYHOMEASSISTANT"
REXEL_OAUTH_TOKEN_URL = f"{REXEL_OAUTH_TENANT}/oauth2/v2.0/token?p={REXEL_OAUTH_POLICY}"
REXEL_REQUIRED_CONSENT = "homeassistant"

SOMFY_API = "https://accounts.somfy.com"
SOMFY_CLIENT_ID = "0d8e920c-1478-11e7-a377-02dd59bd3041_1ewvaqmclfogo4kcsoo0c8k4kso884owg08sg8c40sk4go4ksg"
SOMFY_CLIENT_SECRET = "12k73w1n540g8o4cokg0cw84cog840k84cwggscwg884004kgk"

LOCAL_API_PATH = "/enduser-mobile-web/1/enduserAPI/"

SERVERS_WITH_LOCAL_API = [
    Server.SOMFY_EUROPE,
    Server.SOMFY_OCEANIA,
    Server.SOMFY_AMERICA,
]

SUPPORTED_SERVERS: dict[str, ServerConfig] = {
    Server.ATLANTIC_COZYTOUCH: ServerConfig(
        server=Server.ATLANTIC_COZYTOUCH,
        name="Atlantic Cozytouch",
        endpoint="https://ha110-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Atlantic",
        type=APIType.CLOUD,
    ),
    Server.BRANDT: ServerConfig(
        server=Server.BRANDT,
        name="Brandt Smart Control",
        endpoint="https://ha3-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Brandt",
        type=APIType.CLOUD,
    ),
    Server.FLEXOM: ServerConfig(
        server=Server.FLEXOM,
        name="Flexom",
        endpoint="https://ha108-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Bouygues",
        type=APIType.CLOUD,
    ),
    Server.HEXAOM_HEXACONNECT: ServerConfig(
        server=Server.HEXAOM_HEXACONNECT,
        name="Hexaom HexaConnect",
        endpoint="https://ha5-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hexaom",
        type=APIType.CLOUD,
    ),
    Server.HI_KUMO_ASIA: ServerConfig(
        server=Server.HI_KUMO_ASIA,
        name="Hitachi Hi Kumo (Asia)",
        endpoint="https://ha203-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hitachi",
        type=APIType.CLOUD,
    ),
    Server.HI_KUMO_EUROPE: ServerConfig(
        server=Server.HI_KUMO_EUROPE,
        name="Hitachi Hi Kumo (Europe)",
        endpoint="https://ha117-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hitachi",
        type=APIType.CLOUD,
    ),
    Server.HI_KUMO_OCEANIA: ServerConfig(
        server=Server.HI_KUMO_OCEANIA,
        name="Hitachi Hi Kumo (Oceania)",
        endpoint="https://ha203-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hitachi",
        type=APIType.CLOUD,
    ),
    Server.NEXITY: ServerConfig(
        server=Server.NEXITY,
        name="Nexity Eugénie",
        endpoint="https://ha106-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Nexity",
        type=APIType.CLOUD,
    ),
    Server.REXEL: ServerConfig(
        server=Server.REXEL,
        name="Rexel Energeasy Connect",
        endpoint=REXEL_BACKEND_API,
        manufacturer="Rexel",
        type=APIType.CLOUD,
    ),
    Server.SAUTER_COZYTOUCH: ServerConfig(  # duplicate of Atlantic Cozytouch
        server=Server.SAUTER_COZYTOUCH,
        name="Sauter Cozytouch",
        endpoint="https://ha110-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Sauter",
        type=APIType.CLOUD,
    ),
    Server.SIMU_LIVEIN2: ServerConfig(  # alias of https://tahomalink.com
        server=Server.SIMU_LIVEIN2,
        name="SIMU (LiveIn2)",
        endpoint="https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
        type=APIType.CLOUD,
    ),
    Server.SOMFY_EUROPE: ServerConfig(  # alias of https://tahomalink.com
        server=Server.SOMFY_EUROPE,
        name="Somfy (Europe)",
        endpoint="https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
        type=APIType.CLOUD,
    ),
    Server.SOMFY_AMERICA: ServerConfig(
        server=Server.SOMFY_AMERICA,
        name="Somfy (North America)",
        endpoint="https://ha401-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
        type=APIType.CLOUD,
    ),
    Server.SOMFY_OCEANIA: ServerConfig(
        server=Server.SOMFY_OCEANIA,
        name="Somfy (Oceania)",
        endpoint="https://ha201-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
        type=APIType.CLOUD,
    ),
    Server.THERMOR_COZYTOUCH: ServerConfig(  # duplicate of Atlantic Cozytouch
        server=Server.THERMOR_COZYTOUCH,
        name="Thermor Cozytouch",
        endpoint="https://ha110-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Thermor",
        type=APIType.CLOUD,
    ),
    Server.UBIWIZZ: ServerConfig(
        server=Server.UBIWIZZ,
        name="Ubiwizz",
        endpoint="https://ha129-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Decelect",
        type=APIType.CLOUD,
    ),
}
