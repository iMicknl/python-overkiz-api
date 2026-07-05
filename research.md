# Implementing Somfy multi-site in python-overkiz-api

**Status:** verified live against prod 2026-07-04 (app `com.somfy.homeapp`
v2.5.1, account `somfy@imick.nl`). Working reference implementation:
`tools/somfy-multisite-poc/somfy_multisite.py` (aiohttp, no other deps).

This document explains what to add to `python-overkiz-api` to support Somfy
accounts that own or are invited to **multiple sites (homes)** — the "multi
account sign in" feature in the current TaHoma app. It maps everything onto the
patterns pyoverkiz already has (`SomfyAuthStrategy`, the Rexel
`SupportsGatewaySelection` mixin, `ServerConfig`).

---

## 1. Background: how the app does multi-site

Somfy layered a **Keycloak** identity provider ("Ginaite") and a **back-office
directory** ("BOB") on top of the existing per-region Overkiz clouds. The legacy
Somfy Accounts login still works and still maps to a single region; multi-site
adds a directory in front of it.

The pieces (all prod, from the app's Firebase Remote Config `config_servers`):

| Role | URL |
|---|---|
| Keycloak (Ginaite) realm | `https://ginaite-prod.ovkube.net/realms/somfy-tahoma/protocol/openid-connect` |
| BOB site directory | `https://backoffice-service.ovkube.net/site-api/public/v1` |
| BOB invitations | `https://backoffice-service.ovkube.net/invitation-api/public/v1` |
| BOB `X-Api-Key` | `184638B3FBE874ACD24C14FBD657B` |
| Somfy Accounts (IdP) | `https://accounts.somfy.com` |
| Overkiz EMEA / APAC / SNABA | `https://ha101-1.overkiz.com` / `ha201` / `ha401` |

Key facts (each verified live):

- The Keycloak realm `somfy-tahoma` federates to Somfy Accounts through an IdP
  alias **`somfy-customer`**. The OAuth `client_id` is the **same Somfy Accounts
  client id pyoverkiz already stores** (`SOMFY_CLIENT_ID`), *not* the
  `somfy-client` string hardcoded in the app (that one 400s — it's a fallback).
- A **site-scoped Ginaite token is a Bearer that the classic Overkiz enduser API
  accepts** — so once you have it, every existing pyoverkiz endpoint call works
  unchanged. The token's JWT carries `soid` (site oid), `tenantOID`, and a
  `sites` array.
- A site maps to a gateway on exactly one region's Overkiz server (EMEA for this
  account; the others return `403 No such user account`).

---

## 2. The two auth paths

There are two ways to get a Ginaite token. **Both are verified working.** The
first is far simpler and is the recommended default; the second mirrors what the
app literally does and is the fallback if Somfy ever disables token exchange.

### Path A — password grant + Keycloak token exchange (recommended)

Pure OAuth2, two POSTs, no HTML/redirects. This is what `somfy_multisite.py`
implements.

1. **Somfy Accounts password grant** (pyoverkiz already does exactly this in
   `SomfyAuthStrategy._request_access_token`):
   ```
   POST https://accounts.somfy.com/oauth/oauth/v2/token/jwt
   grant_type=password
   client_id=<SOMFY_CLIENT_ID>
   client_secret=<SOMFY_CLIENT_SECRET>
   username=<email>&password=<password>
   → { access_token (iss=accounts.somfy.com), refresh_token, ... }
   ```
2. **Keycloak external→internal token exchange** (public client — no secret):
   ```
   POST https://ginaite-prod.ovkube.net/realms/somfy-tahoma/protocol/openid-connect/token
   grant_type=urn:ietf:params:oauth:grant-type:token-exchange
   client_id=<SOMFY_CLIENT_ID>
   subject_token=<somfy accounts access_token>
   subject_issuer=somfy-customer
   subject_token_type=urn:ietf:params:oauth:token-type:access_token
   → { access_token (iss=…/somfy-tahoma), refresh_token, expires_in=900, ... }
   ```

Note: Keycloak's ROPC (direct password grant) for this client is **disabled**
("Client not allowed for direct access grants"), which is why the two-step
exchange is needed rather than a single password grant against Keycloak.

### Path B — WebView-style authorization code + PKCE (fallback)

What the app does inside its login WebView. Requires following the broker→IdP
redirect chain and POSTing the Somfy Accounts login form (has a `_csrf_token`
hidden field, so it needs light HTML handling).

```
GET  {ginaite}/auth?client_id=<SOMFY_CLIENT_ID>&response_type=code
        &scope=openid&redirect_uri=com.somfy.homeapp
        &code_challenge=<S256>&code_challenge_method=S256
   → 303 /broker/somfy-customer/login → 303 accounts.somfy.com
POST accounts.somfy.com/login_check  (_csrf_token,_username,_password)
   → brokered 302 chain → https://ginaite-prod.ovkube.net/com.somfy.homeapp?code=…
POST {ginaite}/token  grant_type=authorization_code&code_verifier=…&redirect_uri=com.somfy.homeapp
```

`redirect_uri` is schemeless (`com.somfy.homeapp`); Keycloak resolves it against
its own host, so the callback URL is
`https://ginaite-prod.ovkube.net/com.somfy.homeapp?code=…`. No `kc_idp_hint` is
sent (the realm's only IdP is `somfy-customer`).

---

## 3. Getting from a global token to a controllable gateway

Same for both paths once you hold the initial Ginaite token:

1. **List sites** (global token):
   ```
   GET {bob}/site-api/public/v1/sites?withGateways=true&limit=20&offset=0
   Authorization: Bearer <ginaite token>
   X-Api-Key: 184638B3FBE874ACD24C14FBD657B
   ```
   `limit` must be ≤ 20. Response:
   ```jsonc
   { "totalCount": 2, "results": [
     { "siteOID": "bbbb…", "name": "Mick", "country": "NL",
       "currentUserRoles": [{"roleOID": "owner"}],
       "subSites": [{"externalOID": "…", "type": "SETUP",
                     "gateways": [{"gatewayId": "2025-8464-6867", "type": 98,
                                   "connectivity": {"protocolVersion": "2026.1.3"}}]}] },
     { "siteOID": "31a6…", "name": "Smientstraat", … } ] }
   ```
2. **Mint a site-scoped token** (refresh grant + `?siteOID`):
   ```
   POST {ginaite}/token?siteOID=<siteOID>
   grant_type=refresh_token&client_id=<SOMFY_CLIENT_ID>&refresh_token=<refresh token>
   ```
   The returned access_token's JWT contains `soid=<siteOID>` and `tenantOID`.
3. **Talk to the gateway**: use the site-scoped token as
   `Authorization: Bearer` against the classic Overkiz enduser API for the site's
   region (`{ha10x}/enduser-mobile-web/enduserAPI/...`). All existing pyoverkiz
   endpoint code works unchanged.

Invitations (e.g. a `tahoma.somfy.cloud/invitation?token=…` link) are accepted
with the global token:
`POST {bob}/invitation-api/public/v1/invitations/{token}/accept`.

---

## 4. How this maps onto pyoverkiz

The repo is already shaped for this. Reuse, don't reinvent:

- `pyoverkiz/auth/base.py` already defines `SupportsGatewaySelection` and
  `GatewayCandidate`. A Somfy multi-site strategy should implement that protocol
  exactly like `RexelGatewayMixin` does — `discover_gateways()`,
  `select_gateway()`, `selected_gateway`.
- `SOMFY_CLIENT_ID` / `SOMFY_CLIENT_SECRET` / `SOMFY_API` in `const.py` are the
  same values the multi-site flow needs. Add the Ginaite/BOB constants alongside.
- `AuthContext` already stores access/refresh tokens and expiry and knows how to
  refresh — reuse it for the Ginaite token.

### Suggested additions

**`const.py`** — new constants:
```python
GINAITE_TOKEN_URL = "https://ginaite-prod.ovkube.net/realms/somfy-tahoma/protocol/openid-connect/token"
GINAITE_SUBJECT_ISSUER = "somfy-customer"
GINAITE_TOKEN_EXCHANGE_GRANT = "urn:ietf:params:oauth:grant-type:token-exchange"
BOB_SITE_API = "https://backoffice-service.ovkube.net/site-api/public/v1"
BOB_API_KEY = "184638B3FBE874ACD24C14FBD657B"
```

**`enums/server.py`** — a new `Server.SOMFY_MULTISITE = "somfy_multisite"` (keep
`SOMFY_EUROPE` untouched for the single-site legacy path).

**`auth/strategies.py`** — a new `SomfyAccountAuthStrategy(BaseAuthStrategy)`
implementing `SupportsGatewaySelection`:

```python
class SomfyAccountAuthStrategy(BaseAuthStrategy):
    """Somfy multi-site: Keycloak token exchange + BOB site directory."""

    def __init__(self, credentials, session, server, ssl_context):
        super().__init__(session, server, ssl_context)
        self.credentials = credentials          # UsernamePasswordCredentials
        self.context = AuthContext()            # Ginaite token
        self._site_oid: str | None = None
        self._sites: list[GatewayCandidate] = []

    async def login(self) -> None:
        sso_access = await self._somfy_password_grant()   # reuse SomfyAuthStrategy logic
        await self._token_exchange(sso_access)            # -> self.context (Ginaite)
        self._sites = await self.discover_gateways()
        if len(self._sites) == 1:
            self.select_gateway(self._sites[0].gateway_id)

    async def discover_gateways(self) -> list[GatewayCandidate]:
        data = await self._bob_get("sites?withGateways=true&limit=20")
        out = []
        for site in data["results"]:
            for ss in site.get("subSites", []):
                for gw in ss.get("gateways", []):
                    out.append(GatewayCandidate(
                        gateway_id=str(gw["gatewayId"]),
                        home_id=site["siteOID"],
                        label=site.get("name"),
                        external_id=ss.get("externalOID"),
                    ))
        return out

    def select_gateway(self, gateway_id: str) -> None:
        site = next(s for s in self._sites if s.gateway_id == gateway_id)
        self._site_oid = site.home_id       # siteOID
        self._selected = gateway_id

    async def refresh_if_needed(self) -> bool:
        if not self.context.is_expired() or not self.context.refresh_token:
            return False
        # refresh scoped to the selected site so the token stays site-scoped
        await self._refresh(site_oid=self._site_oid)
        return True

    async def auth_headers(self, path: str | None = None):
        # site-scoped Ginaite token is a plain Bearer for the Overkiz enduser API
        return {"Authorization": f"Bearer {self.context.access_token}"}
```

Key detail: after `select_gateway`, mint/refresh the token **with
`?siteOID=<site_oid>`** so `auth_headers` returns a site-scoped Bearer. That is
the whole trick — no gateway header is needed (unlike Rexel); the token itself
carries the scope, and the classic Overkiz endpoints accept it directly.

**`endpoint`**: return the region's Overkiz base (`ha101-1.overkiz.com/...`).
The region can be discovered by probing `setup/gateways` across regions (as the
POC's `find_overkiz_region` does), or by mapping `site.country` → region.

**`factory.py`**: route `Server.SOMFY_MULTISITE` +
`UsernamePasswordCredentials` to `SomfyAccountAuthStrategy`.

---

## 5. Home Assistant integration — can this use HA's native OAuth2/PKCE?

Short answer: **partially, and it's worth trying both.** There are two layers.

### 5a. What HA's native OAuth2 helper gives you

HA's `config_entry_oauth2_flow` (`AbstractOAuth2Implementation` /
`LocalOAuth2Implementation`) implements the **authorization-code + PKCE** flow:
it opens the authorize URL in the user's browser, catches the redirect, exchanges
the code, and then **transparently refreshes** the token and persists it in the
config entry. This maps cleanly onto **Path B** (§2) — the same flow the app uses.

To use it you would configure an `OAuth2Implementation` with:

- authorize URL = `{ginaite}/auth`
- token URL = `{ginaite}/token`
- `client_id` = `SOMFY_CLIENT_ID`, `scope=openid`
- PKCE (`code_challenge_method=S256`)

**Blocker (now verified — the redirect URI):** the Keycloak client only
whitelists the app's **mobile custom scheme**, not any http(s) URL. Probed live
2026-07-04 with `probe_redirect_uri.py` (Keycloak validates `redirect_uri` at
`/auth` before any login: allowed → 303 to the broker, disallowed → 400 "Invalid
parameter: redirect_uri"):

| redirect_uri | result |
|---|---|
| `com.somfy.homeapp` | ✅ 303 accepted |
| `com.somfy.homeapp://auth`, `…://auth/callback`, `…://x?y=1` | ✅ 303 accepted |
| `com.somfy.homeapp://` (scheme only) | ❌ 400 rejected |
| `https://my.home-assistant.io/redirect/oauth` | ❌ 400 rejected |
| `http(s)://homeassistant.local:8123/auth/external/callback` | ❌ 400 rejected |
| `http://localhost:8123/auth/external/callback` | ❌ 400 rejected |

So the whitelist is `com.somfy.homeapp` (exact) + `com.somfy.homeapp://<path>`
(custom-scheme wildcard). **HA's web-hosted OAuth2 callback
(`https://my.home-assistant.io/redirect/oauth`) is rejected**, so HA's stock
`config_entry_oauth2_flow` cannot drive this client as-is.

What this means for Path B:

- **HA native OAuth2 is not usable out of the box** with the current client.
- It could only work if either (a) Somfy adds an https redirect to the client's
  whitelist (out of our control), or (b) HA registers/uses the
  `com.somfy.homeapp://` scheme and intercepts that redirect — which the stock
  helper doesn't do; it would need a custom OAuth2 implementation that captures
  the custom-scheme callback (feasible but non-standard).
- The user would still log in at **accounts.somfy.com** (Keycloak brokers to it),
  so the browser step would show the familiar Somfy login — good UX if it worked.

The repo already has a precedent for HA owning the OAuth2 lifecycle:
`RexelTokenCredentials` takes an async `access_token_callback` so HA's
`application_credentials` platform refreshes/persists the token and pyoverkiz
just consumes it. A `SomfyMultisiteTokenCredentials` with the same
`access_token_callback` shape could still let an *externally driven* OAuth2 flow
own the Ginaite token — but given the redirect-URI constraint, that external
flow can't be HA's stock helper without custom callback handling.

### 5b. Why you probably still want Path A in pyoverkiz

HA's native OAuth2 helper does not model:

- the **BOB site directory** (listing sites, choosing one),
- **per-site token scoping** (`?siteOID` on refresh), or
- the **token-exchange** step.

So even with native OAuth2, the site-selection and `siteOID` scoping live in
pyoverkiz. And Path A (password grant + token exchange) needs **no browser at
all** — it fits HA's classic username/password config flow, which is the current
Somfy integration UX. That means **you can ship multi-site without changing the
HA login UX at all**: keep the username/password form, do Path A under the hood,
then present a "which site?" selection step (a standard HA config-flow menu) fed
by `discover_gateways()`.

### Recommendation

- **Ship Path A.** Password grant + token exchange requires no HA OAuth2
  plumbing and no redirect URI at all; it reuses the existing username/password
  config flow, with a site-selection step layered on via
  `SupportsGatewaySelection`. Lowest risk, fully verified, and — importantly —
  it side-steps the redirect-URI blocker entirely (token exchange has no
  `redirect_uri`).
- **Path B (HA native OAuth2) is currently blocked** by the client's
  redirect-URI whitelist (§5a): HA's web callback is rejected. Don't invest in it
  unless Somfy adds an https redirect, or you're willing to build a custom OAuth2
  implementation that intercepts the `com.somfy.homeapp://` custom scheme.

Both converge on the same post-auth code (BOB discovery → `siteOID` scoping →
Overkiz), so implementing §4 first means whichever auth path you choose plugs in
with minimal extra work.

---

## 6. Verification checklist (all passed in the POC)

- [x] Token exchange returns a Ginaite token + refresh_token (public client).
- [x] BOB `/sites` lists all sites with gateways using the Ginaite token.
- [x] `?siteOID` refresh yields a token whose JWT has `soid`/`tenantOID`.
- [x] Site-scoped token drives the classic Overkiz enduser API (`setup`,
      `setup/gateways`, `setup/devices`, `setup/places`, `actionGroups`) → 200.
- [x] Two sites enumerated for the test account (Mick, Smientstraat), each on
      EMEA/ha101.

Reproduce: `cd tools/somfy-multisite-poc && python main.py`.
