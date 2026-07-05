"""Constants and server descriptors used across the package."""

from __future__ import annotations

from importlib.metadata import version
from types import MappingProxyType

from pyoverkiz.enums import Server
from pyoverkiz.enums.server import APIType
from pyoverkiz.models import ServerConfig

USER_AGENT = f"pyoverkiz/{version('pyoverkiz')}"

COZYTOUCH_ATLANTIC_API = "https://apis.groupe-atlantic.com"
COZYTOUCH_CLIENT_ID = (
    "Q3RfMUpWeVRtSUxYOEllZkE3YVVOQmpGblpVYToyRWNORHpfZHkzNDJVSnFvMlo3cFNKTnZVdjBh"
)

NEXITY_API = "https://api.egn.prd.aws-nexity.fr"
NEXITY_COGNITO_CLIENT_ID = "3mca95jd5ase5lfde65rerovok"
NEXITY_COGNITO_USER_POOL = "eu-west-1_wj277ucoI"
NEXITY_COGNITO_REGION = "eu-west-1"

# Account-wide homes/gateways directory; works before a gateway is selected.
REXEL_ENDUSER_API = "https://econnect-api.rexelservices.fr/api/enduser"
# Device (Overkiz-proxy) calls live under /overkiz; gateway-scoped, need the gatewayId header.
REXEL_BACKEND_API = f"{REXEL_ENDUSER_API}/overkiz/"
REXEL_OAUTH_CLIENT_ID = "2b635ede-c3fb-43bc-8d23-f6d17f80e96d"
REXEL_OAUTH_REDIRECT_URI = "https://my.home-assistant.io/redirect/oauth"
REXEL_OAUTH_SCOPE = "https://adb2cservicesfrenduserprod.onmicrosoft.com/94f05108-65f7-477a-a84d-e67e1aed6f79/ExternalProvider"
REXEL_OAUTH_TENANT = (
    "https://consumerlogin.rexelservices.fr/670998c0-f737-4d75-a32f-ba9292755b70"
)
REXEL_OAUTH_POLICY = "b2c_1a_signinonlyhomeassistant"
REXEL_OAUTH_AUTHORIZE_URL = f"{REXEL_OAUTH_TENANT}/oauth2/v2.0/authorize"
REXEL_OAUTH_TOKEN_URL = f"{REXEL_OAUTH_TENANT}/oauth2/v2.0/token?p={REXEL_OAUTH_POLICY}"
REXEL_REQUIRED_CONSENT = "homeassistant"
REXEL_GATEWAY_HEADER = "gatewayId"

SOMFY_API = "https://accounts.somfy.com"
SOMFY_CLIENT_ID = "0d8e920c-1478-11e7-a377-02dd59bd3041_1ewvaqmclfogo4kcsoo0c8k4kso884owg08sg8c40sk4go4ksg"
# OAuth client secrets are public by design (embedded in mobile apps)
SOMFY_CLIENT_SECRET = "12k73w1n540g8o4cokg0cw84cog840k84cwggscwg884004kgk"  # noqa: S105

# Somfy multi-site (Keycloak "Ginaite" realm + BOB back-office directory).
# The token exchange reuses SOMFY_CLIENT_ID as a PUBLIC client (no secret).
SOMFY_GINAITE_TOKEN_URL = (
    "https://ginaite-prod.ovkube.net/realms/somfy-tahoma/protocol/openid-connect/token"  # noqa: S105
)
SOMFY_GINAITE_SUBJECT_ISSUER = "somfy-customer"
SOMFY_GINAITE_TOKEN_EXCHANGE_GRANT = "urn:ietf:params:oauth:grant-type:token-exchange"  # noqa: S105
SOMFY_GINAITE_SUBJECT_TOKEN_TYPE = "urn:ietf:params:oauth:token-type:access_token"  # noqa: S105

SOMFY_BOB_SITE_API = "https://backoffice-service.ovkube.net/site-api/public/v1"
SOMFY_BOB_API_KEY = "184638B3FBE874ACD24C14FBD657B"

# Site region derived offline from its ISO country, mirroring the TaHoma app's BusinessArea.fromCountry (EMEA fallback).
SOMFY_DEFAULT_REGION = "EMEA"
SOMFY_REGION_ENDPOINT: MappingProxyType[str, str] = MappingProxyType(
    {
        "EMEA": "https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        "APAC": "https://ha201-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        "SNABA": "https://ha401-1.overkiz.com/enduser-mobile-web/enduserAPI/",
    }
)
SOMFY_COUNTRY_REGION: MappingProxyType[str, str] = MappingProxyType(
    {
        # Americas — ha401 (SNABA).
        "CA": "SNABA",
        "US": "SNABA",
        "MX": "SNABA",
        # Asia-Pacific — ha201 (APAC).
        "AU": "APAC",
        "HK": "APAC",
        "IN": "APAC",
        "ID": "APAC",
        "JP": "APAC",
        "MY": "APAC",
        "NZ": "APAC",
        "PH": "APAC",
        "SG": "APAC",
        "TW": "APAC",
        "TH": "APAC",
        "VN": "APAC",
        "KR": "APAC",
        "CN": "APAC",
        # Europe, Middle East & Africa — ha101 (EMEA).
        "AL": "EMEA",
        "AD": "EMEA",
        "AT": "EMEA",
        "BY": "EMEA",
        "BE": "EMEA",
        "BG": "EMEA",
        "HR": "EMEA",
        "CY": "EMEA",
        "CZ": "EMEA",
        "DK": "EMEA",
        "EG": "EMEA",
        "EE": "EMEA",
        "FO": "EMEA",
        "FI": "EMEA",
        "FR": "EMEA",
        "GF": "EMEA",
        "PF": "EMEA",
        "DE": "EMEA",
        "GR": "EMEA",
        "GP": "EMEA",
        "HU": "EMEA",
        "IL": "EMEA",
        "IT": "EMEA",
        "JE": "EMEA",
        "JO": "EMEA",
        "KZ": "EMEA",
        "KW": "EMEA",
        "LV": "EMEA",
        "LB": "EMEA",
        "LT": "EMEA",
        "LU": "EMEA",
        "MQ": "EMEA",
        "YT": "EMEA",
        "MC": "EMEA",
        "MA": "EMEA",
        "NL": "EMEA",
        "NO": "EMEA",
        "NC": "EMEA",
        "PS": "EMEA",
        "PL": "EMEA",
        "PT": "EMEA",
        "QA": "EMEA",
        "IE": "EMEA",
        "RE": "EMEA",
        "RO": "EMEA",
        "RU": "EMEA",
        "BL": "EMEA",
        "SA": "EMEA",
        "RS": "EMEA",
        "SK": "EMEA",
        "ZA": "EMEA",
        "ES": "EMEA",
        "SE": "EMEA",
        "CH": "EMEA",
        "TN": "EMEA",
        "TR": "EMEA",
        "UA": "EMEA",
        "AE": "EMEA",
        "GB": "EMEA",
    }
)

# Brandt Smart Control middleware (cookie-session Rails API in front of Overkiz)
BRANDT_MIDDLEWARE_API = "https://www.smartcontrol-app.com"
BRANDT_PARTNER = "brandt-electromenager"

LOCAL_API_PATH = "/enduser-mobile-web/1/enduserAPI/"

SERVERS_WITH_LOCAL_API = [
    Server.SOMFY_EUROPE,
    Server.SOMFY_OCEANIA,
    Server.SOMFY_AMERICA,
    Server.REXEL,
]

SUPPORTED_SERVERS: MappingProxyType[str, ServerConfig] = MappingProxyType(
    {
        Server.ATLANTIC_COZYTOUCH: ServerConfig(
            server=Server.ATLANTIC_COZYTOUCH,
            name="Atlantic Cozytouch",
            endpoint="https://ha110-1.overkiz.com/enduser-mobile-web/enduserAPI/",
            manufacturer="Atlantic",
            api_type=APIType.CLOUD,
        ),
        Server.BRANDT: ServerConfig(
            server=Server.BRANDT,
            name="Brandt Smart Control",
            endpoint="https://ha3-1.overkiz.com/enduser-mobile-web/enduserAPI/",
            manufacturer="Brandt",
            api_type=APIType.CLOUD,
        ),
        Server.FLEXOM: ServerConfig(
            server=Server.FLEXOM,
            name="Flexom",
            endpoint="https://ha108-1.overkiz.com/enduser-mobile-web/enduserAPI/",
            manufacturer="Bouygues",
            api_type=APIType.CLOUD,
        ),
        Server.HEXAOM_HEXACONNECT: ServerConfig(
            server=Server.HEXAOM_HEXACONNECT,
            name="Hexaom HexaConnect",
            endpoint="https://ha5-1.overkiz.com/enduser-mobile-web/enduserAPI/",
            manufacturer="Hexaom",
            api_type=APIType.CLOUD,
        ),
        Server.HI_KUMO_ASIA: ServerConfig(
            server=Server.HI_KUMO_ASIA,
            name="Hitachi Hi Kumo (Asia)",
            endpoint="https://ha203-1.overkiz.com/enduser-mobile-web/enduserAPI/",
            manufacturer="Hitachi",
            api_type=APIType.CLOUD,
        ),
        Server.HI_KUMO_EUROPE: ServerConfig(
            server=Server.HI_KUMO_EUROPE,
            name="Hitachi Hi Kumo (Europe)",
            endpoint="https://ha117-1.overkiz.com/enduser-mobile-web/enduserAPI/",
            manufacturer="Hitachi",
            api_type=APIType.CLOUD,
        ),
        Server.HI_KUMO_OCEANIA: ServerConfig(
            server=Server.HI_KUMO_OCEANIA,
            name="Hitachi Hi Kumo (Oceania)",
            endpoint="https://ha203-1.overkiz.com/enduser-mobile-web/enduserAPI/",
            manufacturer="Hitachi",
            api_type=APIType.CLOUD,
        ),
        Server.NEXITY: ServerConfig(
            server=Server.NEXITY,
            name="Nexity Eugénie",
            endpoint="https://ha106-1.overkiz.com/enduser-mobile-web/enduserAPI/",
            manufacturer="Nexity",
            api_type=APIType.CLOUD,
        ),
        Server.REXEL: ServerConfig(
            server=Server.REXEL,
            name="Rexel Energeasy Connect",
            endpoint=REXEL_BACKEND_API,
            manufacturer="Rexel",
            api_type=APIType.CLOUD,
        ),
        Server.SAUTER_COZYTOUCH: ServerConfig(  # duplicate of Atlantic Cozytouch
            server=Server.SAUTER_COZYTOUCH,
            name="Sauter Cozytouch",
            endpoint="https://ha110-1.overkiz.com/enduser-mobile-web/enduserAPI/",
            manufacturer="Sauter",
            api_type=APIType.CLOUD,
        ),
        Server.SIMU_LIVEIN2: ServerConfig(  # alias of https://tahomalink.com
            server=Server.SIMU_LIVEIN2,
            name="SIMU (LiveIn2)",
            endpoint="https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/",
            manufacturer="Somfy",
            api_type=APIType.CLOUD,
        ),
        Server.SOMFY: ServerConfig(
            server=Server.SOMFY,
            # Region-agnostic multi-site login. The endpoint here is a
            # placeholder; SomfyAccountAuthStrategy overrides it per selected
            # site once the region is resolved.
            name="Somfy",
            endpoint="https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/",
            manufacturer="Somfy",
            api_type=APIType.CLOUD,
        ),
        Server.SOMFY_EUROPE: ServerConfig(  # alias of https://tahomalink.com
            server=Server.SOMFY_EUROPE,
            name="Somfy (Europe)",
            endpoint="https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/",
            manufacturer="Somfy",
            api_type=APIType.CLOUD,
        ),
        Server.SOMFY_AMERICA: ServerConfig(
            server=Server.SOMFY_AMERICA,
            name="Somfy (North America)",
            endpoint="https://ha401-1.overkiz.com/enduser-mobile-web/enduserAPI/",
            manufacturer="Somfy",
            api_type=APIType.CLOUD,
        ),
        Server.SOMFY_OCEANIA: ServerConfig(
            server=Server.SOMFY_OCEANIA,
            name="Somfy (Oceania)",
            endpoint="https://ha201-1.overkiz.com/enduser-mobile-web/enduserAPI/",
            manufacturer="Somfy",
            api_type=APIType.CLOUD,
        ),
        Server.THERMOR_COZYTOUCH: ServerConfig(  # duplicate of Atlantic Cozytouch
            server=Server.THERMOR_COZYTOUCH,
            name="Thermor Cozytouch",
            endpoint="https://ha110-1.overkiz.com/enduser-mobile-web/enduserAPI/",
            manufacturer="Thermor",
            api_type=APIType.CLOUD,
        ),
        Server.UBIWIZZ: ServerConfig(
            server=Server.UBIWIZZ,
            name="Ubiwizz",
            endpoint="https://ha129-1.overkiz.com/enduser-mobile-web/enduserAPI/",
            manufacturer="Decelect",
            api_type=APIType.CLOUD,
        ),
    }
)
