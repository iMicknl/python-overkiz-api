# Somfy multi-site support — design

**Status:** approved 2026-07-04. Verified live against prod (app
`com.somfy.homeapp` v2.5.1, account `somfy@imick.nl`, 2 sites) via a throwaway
POC in `tools/`. Supersedes the "add a `SOMFY_MULTISITE` server" proposal in
`research.md`.

## Goal

Let a single Somfy account that owns or is invited to **multiple sites (homes)**
authenticate and control each site through pyoverkiz — the "multi account
sign-in" feature in the current TaHoma app — while reusing every existing Overkiz
endpoint call unchanged.

## Decisions

- **One region-agnostic `Server.SOMFY`**, not a parallel `SOMFY_MULTISITE`.
  The multi-site flow works for any region; the strategy resolves the region at
  runtime. Legacy per-region servers (`SOMFY_EUROPE/AMERICA/OCEANIA`) stay for
  the classic single-site password login and the local API.
- **Path A only** (password grant + Keycloak token exchange). No browser, no
  PKCE, no redirect URI — fits the existing username/password config flow. Path B
  (WebView authorization-code) is a documented fallback, not implemented.
- **Region resolved from a static `country → region` map** (verified: no API
  field carries the region — not the JWT, not `/sites`, not `/sites/{oid}`; the
  only geo signals are `country` and `partnerOIDs`). The map mirrors the TaHoma
  app's `BusinessArea.fromCountry` (from the decompiled `com.somfy.homeapp`): all
  three regions' countries are enumerated (EMEA=ha101, APAC=ha201, SNABA=ha401),
  and **any unresolvable country (unlisted or missing) falls back to EMEA** —
  identical to the app. An unresolvable country is logged as a warning (signals
  the map needs updating), but still resolves to EMEA.
- **Invitations deferred** (YAGNI — irreversible, no HA consumer yet).

## Background (verified live)

Somfy layered Keycloak ("Ginaite", realm `somfy-tahoma`) and a back-office
directory ("BOB") on top of the per-region Overkiz clouds.

| Role | URL |
|---|---|
| Keycloak token endpoint | `https://ginaite-prod.ovkube.net/realms/somfy-tahoma/protocol/openid-connect/token` |
| Keycloak IdP alias (federates to Somfy Accounts) | `somfy-customer` |
| BOB site directory | `https://backoffice-service.ovkube.net/site-api/public/v1` |
| BOB `X-Api-Key` | `184638B3FBE874ACD24C14FBD657B` |
| Somfy Accounts (IdP) | `https://accounts.somfy.com` (reuses existing `SOMFY_CLIENT_ID/SECRET`) |
| Overkiz EMEA / APAC / SNABA | `https://ha101-1` / `ha201-1` / `ha401-1` `.overkiz.com` |

Key facts:
- The token exchange uses the **same `SOMFY_CLIENT_ID`** pyoverkiz already stores
  (the app's hardcoded `somfy-client` is a dead fallback). Exchange is a **public
  client** — no secret. Only the initial password grant uses the secret.
- A **site-scoped Ginaite token is a plain Bearer the classic Overkiz enduser API
  accepts** — so every existing endpoint call works unchanged.
- Tokens carry `soid`/`tenantOID`/`sites[]` and **`expires_in=900`** — refresh
  matters.
- **No region field anywhere.** Region must be derived client-side.

## Flow

```
login():
  1. POST accounts.somfy.com/oauth/oauth/v2/token/jwt   (grant_type=password)
        -> SSO access_token  (iss=accounts.somfy.com)     [reuses SomfyAuthStrategy logic]
  2. POST {ginaite}/token   (grant_type=token-exchange, subject_issuer=somfy-customer)
        -> global Ginaite token + refresh_token           [AuthContext]
  3. discover_gateways(); if exactly one -> select_gateway(it)

discover_gateways():
  GET {bob}/sites?withGateways=true&limit=20&offset=0     (Bearer + X-Api-Key; limit<=20)
     flatten site -> subSites -> gateways into GatewayCandidate
     (gateway_id, home_id=siteOID, label=name, external_id=externalOID)
     stash each site's country + siteOID for later

select_gateway(gateway_id):
  - record selected siteOID + country
  - region = COUNTRY_REGION.get(country, EMEA)  (unlisted/missing -> EMEA)
  - self._endpoint = REGION_ENDPOINT[region]
  - mint site-scoped token: POST {ginaite}/token?siteOID=<oid> (grant_type=refresh_token)

endpoint (property):  resolved per-site Overkiz endpoint (overrides placeholder)
refresh_if_needed():  refresh with ?siteOID=<selected> so the token stays scoped
auth_headers():       {"Authorization": "Bearer <token>"}  (no gateway header)
```

## Components

### `enums/server.py`
Add `SOMFY = "somfy"`.

### `const.py`
- `SOMFY_GINAITE_TOKEN_URL`, `SOMFY_GINAITE_SUBJECT_ISSUER = "somfy-customer"`,
  `SOMFY_GINAITE_TOKEN_EXCHANGE_GRANT`, `SOMFY_GINAITE_SUBJECT_TOKEN_TYPE`.
- `SOMFY_BOB_SITE_API`, `SOMFY_BOB_API_KEY`.
- `SOMFY_COUNTRY_REGION: Mapping[str, str]` (ISO 3166 country → region key) and
  `SOMFY_REGION_ENDPOINT: Mapping[str, str]` (region → Overkiz enduser base).
  Regions mirror the existing server groupings: EMEA=ha101, APAC=ha201,
  SNABA=ha401. Seeded from those groupings; `NL→EMEA` verified. Reuse
  `SOMFY_CLIENT_ID/SECRET/API`.
- `SUPPORTED_SERVERS[Server.SOMFY]`: name "Somfy", manufacturer "Somfy",
  `api_type=CLOUD`, `endpoint` = EMEA placeholder (overridden at runtime).

### `auth/strategies.py` — `SomfyMultisiteAuthStrategy(BaseAuthStrategy)`
Implements `SupportsGatewaySelection`. Holds: `credentials`
(`UsernamePasswordCredentials`), `context: AuthContext` (Ginaite token),
`_sites: list[GatewayCandidate]`, per-site `country`, `_selected_site_oid`,
`_endpoint`. Reuses the existing Somfy password-grant helper (factor the shared
`_request_access_token` body so both strategies use it, or call a small shared
function — no duplication).

### `auth/factory.py`
Route `Server.SOMFY` + `UsernamePasswordCredentials` →
`SomfyMultisiteAuthStrategy` (mirrors the `SOMFY_EUROPE` branch).

### `client.py`
**No changes.** Verified: the client already requests against
`self._auth.endpoint` and delegates `discover_gateways()`/`select_gateway()` to
the strategy when it implements `SupportsGatewaySelection`.

## Error handling

- Bad credentials in the password grant → `SomfyBadCredentialsError` (existing).
- Token-exchange / BOB non-200 → `SomfyServiceError` (existing).
- Unresolvable `country` (unlisted or missing) → falls back to EMEA (the app's
  behavior); never raises. EMEA is the largest region and the safe default. It is
  logged as a warning so the map can be extended.
- `auth_headers`/`endpoint` before a gateway is selected: `endpoint` returns the
  placeholder; requests only succeed after selection (mirrors Rexel's
  select-before-use contract).

## Testing

Unit tests with mocked HTTP (match the existing aresponses-based suite; no live
calls in CI):
- login: password grant + token exchange populate the context.
- discovery: multi-site `/sites` flattens to the expected `GatewayCandidate`s.
- select: resolves region from country, sets endpoint, mints a `?siteOID` token.
- unknown/missing country → falls back to EMEA endpoint.
- refresh: expired token refreshes with `?siteOID` and stays scoped.
- factory: `Server.SOMFY` + username/password → `SomfyMultisiteAuthStrategy`.

Live verification is done via the throwaway `tools/` POC (not committed to the
test suite), reproducible with the test account.

## Out of scope

- Invitation acceptance (`POST {bob}/invitation-api/.../invitations/{token}/accept`).
- Path B (WebView authorization-code + PKCE) and HA native OAuth2 — blocked by
  the client's redirect-URI whitelist (documented in `research.md`).
- HA integration changes (config-flow site-selection step) — separate repo.
```
