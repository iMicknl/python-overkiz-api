from pyhoma.models import OverkizServer

COZYTOUCH_CLIENT_ID = (
    "czduc0RZZXdWbjVGbVV4UmlYN1pVSUM3ZFI4YTphSDEzOXZmbzA1ZGdqeDJkSFVSQkFTbmhCRW9h"
)

NEXITY_COGNITO_CLIENT_ID = "3mca95jd5ase5lfde65rerovok"
NEXITY_COGNITO_USER_POOL = "eu-west-1_wj277ucoI"
NEXITY_COGNITO_REGION = "eu-west-1"

SUPPORTED_SERVERS = {
    "atlantic_cozytouch": OverkizServer(
        name="Atlantic Cozytouch",
        endpoint="https://ha110-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Atlantic",
    ),
    "hi_kumo_asia": OverkizServer(
        name="Hitachi Hi Kumo (Asia)",
        endpoint="https://ha203-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hitachi",
    ),
    "hi_kumo_europe": OverkizServer(
        name="Hitachi Hi Kumo (Europe)",
        endpoint="https://ha117-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hitachi",
    ),
    "hi_kumo_oceania": OverkizServer(
        name="Hitachi Hi Kumo (Oceania)",
        endpoint="https://ha203-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hitachi",
    ),
    "nexity": OverkizServer(
        name="Nexity Eugénie",
        endpoint="https://ha106-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Nexity",
    ),
    "rexel": OverkizServer(
        name="Rexel Energeasy Connect",
        endpoint="https://ha112-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Rexel",
    ),
    "somfy_europe": OverkizServer(  # uses https://ha101-1.overkiz.com
        name="Somfy (Europe)",
        endpoint="https://tahomalink.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
    ),
    "somfy_america": OverkizServer(
        name="Somfy (North America)",
        endpoint="https://ha401-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
    ),
    "somfy_oceania": OverkizServer(
        name="Somfy (Oceania)",
        endpoint="https://ha201-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
    ),
}
