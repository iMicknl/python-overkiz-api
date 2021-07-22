from pyhoma.models import OverkizHub

SUPPORTED_HUBS = {
    "atlantic_cozytouch": OverkizHub(
        name="Atlantic Cozytouch",
        endpoint="https://ha110-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Atlantic",
    ),
    "hi_kumo_asia": OverkizHub(
        name="Hitachi Hi Kumo (Asia)",
        endpoint="https://ha203-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hitachi",
    ),
    "hi_kumo_europe": OverkizHub(
        name="Hitachi Hi Kumo (Europe)",
        endpoint="https://ha117-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hitachi",
    ),
    "hi_kumo_oceania": OverkizHub(
        name="Hitachi Hi Kumo (Oceania)",
        endpoint="https://ha203-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Hitachi",
    ),
    "nexity": OverkizHub(
        name="Nexity Eugénie",
        endpoint="https://ha106-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Nexity",
    ),
    "rexel": OverkizHub(
        name="Rexel Energeasy Connect",
        endpoint="https://ha112-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Rexel",
    ),
    "somfy_europe": OverkizHub(  # uses https://ha101-1.overkiz.com
        name="Somfy (Europe)",
        endpoint="https://tahomalink.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
    ),
    "somfy_america": OverkizHub(
        name="Somfy (North America)",
        endpoint="https://ha401-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
    ),
    "somfy_oceania": OverkizHub(
        name="Somfy (Oceania)",
        endpoint="https://ha201-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        manufacturer="Somfy",
    ),
}
