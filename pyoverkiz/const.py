"""Constants and server descriptors used across the package."""

from __future__ import annotations

from pyoverkiz.enums import Server
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
        name="Atlantic Cozytouch",
        endpoint="https://ha110-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Atlantic",
        configuration_url=None,
    ),
    Server.BRANDT: ServerConfig(
        name="Brandt Smart Control",
        endpoint="https://ha3-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Brandt",
        configuration_url=None,
    ),
    Server.FLEXOM: ServerConfig(
        name="Flexom",
        endpoint="https://ha108-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Bouygues",
        configuration_url=None,
    ),
    Server.HEXAOM_HEXACONNECT: ServerConfig(
        name="Hexaom HexaConnect",
        endpoint="https://ha5-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hexaom",
        configuration_url=None,
    ),
    Server.HI_KUMO_ASIA: ServerConfig(
        name="Hitachi Hi Kumo (Asia)",
        endpoint="https://ha203-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hitachi",
        configuration_url=None,
    ),
    Server.HI_KUMO_EUROPE: ServerConfig(
        name="Hitachi Hi Kumo (Europe)",
        endpoint="https://ha117-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hitachi",
        configuration_url=None,
    ),
    Server.HI_KUMO_OCEANIA: ServerConfig(
        name="Hitachi Hi Kumo (Oceania)",
        endpoint="https://ha203-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hitachi",
        configuration_url=None,
    ),
    Server.NEXITY: ServerConfig(
        name="Nexity Eugénie",
        endpoint="https://ha106-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Nexity",
        configuration_url=None,
    ),
    Server.REXEL: ServerConfig(
        name="Rexel Energeasy Connect",
        endpoint=REXEL_BACKEND_API,
        manufacturer="Rexel",
        configuration_url="https://utilisateur.energeasyconnect.com/user/#/zone/equipements",
    ),
    Server.SAUTER_COZYTOUCH: ServerConfig(  # duplicate of Atlantic Cozytouch
        name="Sauter Cozytouch",
        endpoint="https://ha110-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Sauter",
        configuration_url=None,
    ),
    Server.SIMU_LIVEIN2: ServerConfig(  # alias of https://tahomalink.com
        name="SIMU (LiveIn2)",
        endpoint="https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
        configuration_url=None,
    ),
    Server.SOMFY_EUROPE: ServerConfig(  # alias of https://tahomalink.com
        name="Somfy (Europe)",
        endpoint="https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
        configuration_url=None,
    ),
    Server.SOMFY_AMERICA: ServerConfig(
        name="Somfy (North America)",
        endpoint="https://ha401-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
        configuration_url=None,
    ),
    Server.SOMFY_OCEANIA: ServerConfig(
        name="Somfy (Oceania)",
        endpoint="https://ha201-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
        configuration_url=None,
    ),
    Server.THERMOR_COZYTOUCH: ServerConfig(  # duplicate of Atlantic Cozytouch
        name="Thermor Cozytouch",
        endpoint="https://ha110-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Thermor",
        configuration_url=None,
    ),
    Server.UBIWIZZ: ServerConfig(
        name="Ubiwizz",
        endpoint="https://ha129-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Decelect",
        configuration_url=None,
    ),
}
