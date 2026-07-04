# Somfy Multi-Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Support Somfy accounts with multiple sites (homes) by adding a region-agnostic `Server.SOMFY` and a `SomfyMultisiteAuthStrategy` that authenticates via Keycloak token exchange, discovers sites from the BOB directory, and scopes tokens per site.

**Architecture:** A new auth strategy implements the existing `SupportsGatewaySelection` protocol (same one Rexel uses). It reuses the Somfy Accounts password grant, exchanges the SSO token for a Ginaite (Keycloak) token, lists sites from BOB, and mints a site-scoped token on selection. The Overkiz region is resolved from a static `country → region` map, overriding the strategy's `endpoint` at runtime. No `client.py` changes are needed — the client already reads `self._auth.endpoint` and delegates gateway selection.

**Tech Stack:** Python 3.12+, aiohttp, attrs, pytest + pytest-asyncio. Commands run through the devcontainer CLI.

## Global Constraints

- Run every command through the devcontainer CLI: `devcontainer exec --workspace-folder . <cmd>`.
- Python 3.12+ minimum.
- No `__all__` / re-exports in package `__init__.py`.
- Reuse existing constants (`SOMFY_CLIENT_ID`, `SOMFY_CLIENT_SECRET`, `SOMFY_API`) and existing exceptions (`SomfyBadCredentialsError`, `SomfyServiceError`).
- The token-exchange step is a **public client** — send `client_id` but **no** `client_secret`. Only the initial password grant uses the secret.
- Site-scoped token is a plain `Bearer` for the Overkiz enduser API — **no** gateway header (unlike Rexel).
- Lint/type checks must pass: `ruff check`, `ruff format`, `mypy`, `ty`.

---

## File Structure

- `pyoverkiz/enums/server.py` — add `Server.SOMFY`.
- `pyoverkiz/const.py` — Ginaite/BOB constants, `SOMFY_COUNTRY_REGION`, `SOMFY_REGION_ENDPOINT`, `SUPPORTED_SERVERS[Server.SOMFY]`.
- `pyoverkiz/auth/strategies.py` — refactor shared Somfy password-grant helper; add `SomfyMultisiteAuthStrategy`.
- `pyoverkiz/auth/factory.py` — route `Server.SOMFY` to the new strategy.
- `tests/test_auth.py` — unit tests for constants, strategy, and factory.

---

## Task 1: Add `Server.SOMFY` enum + constants

**Files:**
- Modify: `pyoverkiz/enums/server.py`
- Modify: `pyoverkiz/const.py`
- Test: `tests/test_auth.py`

**Interfaces:**
- Produces:
  - `Server.SOMFY` (value `"somfy"`).
  - `GINAITE_TOKEN_URL: str`, `GINAITE_SUBJECT_ISSUER: str`, `GINAITE_TOKEN_EXCHANGE_GRANT: str`, `GINAITE_SUBJECT_TOKEN_TYPE: str`.
  - `BOB_SITE_API: str`, `BOB_API_KEY: str`.
  - `SOMFY_COUNTRY_REGION: Mapping[str, str]` (ISO country → region key `"EMEA"|"APAC"|"SNABA"`).
  - `SOMFY_REGION_ENDPOINT: Mapping[str, str]` (region key → Overkiz enduser base URL).
  - `SUPPORTED_SERVERS[Server.SOMFY]` → `ServerConfig`.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_auth.py`:

```python
def test_somfy_multisite_constants_and_server():
    """Server.SOMFY and the Ginaite/BOB constants are defined and consistent."""
    from pyoverkiz.const import (
        BOB_API_KEY,
        BOB_SITE_API,
        GINAITE_SUBJECT_ISSUER,
        GINAITE_TOKEN_EXCHANGE_GRANT,
        GINAITE_TOKEN_URL,
        SOMFY_COUNTRY_REGION,
        SOMFY_REGION_ENDPOINT,
        SUPPORTED_SERVERS,
    )
    from pyoverkiz.enums import Server

    assert Server.SOMFY == "somfy"
    assert GINAITE_TOKEN_URL.endswith("/protocol/openid-connect/token")
    assert GINAITE_SUBJECT_ISSUER == "somfy-customer"
    assert GINAITE_TOKEN_EXCHANGE_GRANT == (
        "urn:ietf:params:oauth:grant-type:token-exchange"
    )
    assert BOB_SITE_API.endswith("/site-api/public/v1")
    assert BOB_API_KEY == "184638B3FBE874ACD24C14FBD657B"

    # Every mapped country points at a region that has an endpoint.
    assert SOMFY_COUNTRY_REGION["NL"] == "EMEA"
    for region in SOMFY_COUNTRY_REGION.values():
        assert region in SOMFY_REGION_ENDPOINT
    assert SOMFY_REGION_ENDPOINT["EMEA"] == (
        "https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/"
    )

    config = SUPPORTED_SERVERS[Server.SOMFY]
    assert config.server == Server.SOMFY
    assert config.name == "Somfy"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `devcontainer exec --workspace-folder . python -m pytest tests/test_auth.py::test_somfy_multisite_constants_and_server -v`
Expected: FAIL — `AttributeError`/`ImportError` (`Server.SOMFY` / constants not defined).

- [ ] **Step 3a: Add the enum member**

In `pyoverkiz/enums/server.py`, inside `class Server`, add (keep alphabetical-ish grouping near the other Somfy entries):

```python
    SOMFY = "somfy"
```

- [ ] **Step 3b: Add constants**

In `pyoverkiz/const.py`, after the existing `SOMFY_CLIENT_SECRET` block, add:

```python
# Somfy multi-site (Keycloak "Ginaite" realm + BOB back-office directory).
# The token exchange reuses SOMFY_CLIENT_ID as a PUBLIC client (no secret).
GINAITE_TOKEN_URL = "https://ginaite-prod.ovkube.net/realms/somfy-tahoma/protocol/openid-connect/token"
GINAITE_SUBJECT_ISSUER = "somfy-customer"
GINAITE_TOKEN_EXCHANGE_GRANT = "urn:ietf:params:oauth:grant-type:token-exchange"
GINAITE_SUBJECT_TOKEN_TYPE = "urn:ietf:params:oauth:token-type:access_token"

BOB_SITE_API = "https://backoffice-service.ovkube.net/site-api/public/v1"
BOB_API_KEY = "184638B3FBE874ACD24C14FBD657B"

# The BOB directory carries no region field, so the site's Overkiz region is
# derived from its ISO country. Regions mirror the existing per-region Somfy
# servers: EMEA=ha101, APAC=ha201 (Oceania), SNABA=ha401 (Americas). Only NL is
# verified live; other countries are seeded from those groupings. An unmapped
# country must raise rather than guess (see SomfyMultisiteAuthStrategy).
SOMFY_REGION_ENDPOINT: MappingProxyType[str, str] = MappingProxyType(
    {
        "EMEA": "https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        "APAC": "https://ha201-1.overkiz.com/enduser-mobile-web/enduserAPI/",
        "SNABA": "https://ha401-1.overkiz.com/enduser-mobile-web/enduserAPI/",
    }
)
SOMFY_COUNTRY_REGION: MappingProxyType[str, str] = MappingProxyType(
    {
        # EMEA (Europe / Middle East / Africa) — ha101. Verified: NL.
        "AT": "EMEA", "BE": "EMEA", "CH": "EMEA", "CZ": "EMEA", "DE": "EMEA",
        "DK": "EMEA", "ES": "EMEA", "FI": "EMEA", "FR": "EMEA", "GB": "EMEA",
        "GR": "EMEA", "IE": "EMEA", "IT": "EMEA", "LU": "EMEA", "NL": "EMEA",
        "NO": "EMEA", "PL": "EMEA", "PT": "EMEA", "SE": "EMEA",
        # Americas — ha401 (SNABA).
        "BR": "SNABA", "CA": "SNABA", "MX": "SNABA", "US": "SNABA",
        # Asia-Pacific / Oceania — ha201.
        "AU": "APAC", "CN": "APAC", "JP": "APAC", "NZ": "APAC",
    }
)
```

- [ ] **Step 3c: Register the server config**

In `pyoverkiz/const.py`, inside the `SUPPORTED_SERVERS` mapping, add an entry (place it just after the `Server.SIMU_LIVEIN2` entry, before `Server.SOMFY_EUROPE`):

```python
        Server.SOMFY: ServerConfig(
            server=Server.SOMFY,
            # Region-agnostic multi-site login. The endpoint here is a
            # placeholder; SomfyMultisiteAuthStrategy overrides it per selected
            # site once the region is resolved.
            name="Somfy",
            endpoint="https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/",
            manufacturer="Somfy",
            api_type=APIType.CLOUD,
        ),
```

- [ ] **Step 4: Run test to verify it passes**

Run: `devcontainer exec --workspace-folder . python -m pytest tests/test_auth.py::test_somfy_multisite_constants_and_server -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyoverkiz/enums/server.py pyoverkiz/const.py tests/test_auth.py
git commit -m "feat: add Server.SOMFY and Somfy multi-site constants"
```

---

## Task 2: Extract shared Somfy password-grant helper

**Files:**
- Modify: `pyoverkiz/auth/strategies.py`
- Test: `tests/test_auth.py`

**Rationale:** Both `SomfyAuthStrategy` and the new `SomfyMultisiteAuthStrategy` need the Somfy Accounts password grant. Extract the request into a module-level async function so neither strategy duplicates it (DRY). The function returns the raw token dict so multi-site can read `access_token` for the exchange.

**Interfaces:**
- Produces: module-level function in `pyoverkiz/auth/strategies.py`:
  ```python
  async def _somfy_password_token(
      session: ClientSession, username: str, password: str
  ) -> dict[str, Any]:
      """Somfy Accounts password grant -> raw token dict (has access_token, refresh_token)."""
  ```
  Raises `SomfyBadCredentialsError` on `error.invalid.grant`, `SomfyServiceError` when no `access_token`, and routes 5xx through `_raise_for_server_error`.
- Consumes: existing `SOMFY_API`, `SOMFY_CLIENT_ID`, `SOMFY_CLIENT_SECRET`, `_raise_for_server_error`.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_auth.py`:

```python
@pytest.mark.asyncio
async def test_somfy_password_token_returns_token_dict():
    """_somfy_password_token posts the password grant and returns the token dict."""
    from unittest.mock import AsyncMock, MagicMock

    from aiohttp import ClientSession

    from pyoverkiz.auth.strategies import _somfy_password_token

    resp = MagicMock()
    resp.status = 200
    resp.json = AsyncMock(
        return_value={"access_token": "sso-abc", "refresh_token": "r1"}
    )
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=None)
    session = MagicMock(spec=ClientSession)
    session.post = MagicMock(return_value=resp)

    token = await _somfy_password_token(session, "user", "pass")

    assert token["access_token"] == "sso-abc"


@pytest.mark.asyncio
async def test_somfy_password_token_bad_credentials():
    """error.invalid.grant maps to SomfyBadCredentialsError."""
    from unittest.mock import AsyncMock, MagicMock

    from aiohttp import ClientSession

    from pyoverkiz.auth.strategies import _somfy_password_token
    from pyoverkiz.exceptions import SomfyBadCredentialsError

    resp = MagicMock()
    resp.status = 200
    resp.json = AsyncMock(return_value={"message": "error.invalid.grant"})
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=None)
    session = MagicMock(spec=ClientSession)
    session.post = MagicMock(return_value=resp)

    with pytest.raises(SomfyBadCredentialsError):
        await _somfy_password_token(session, "user", "bad")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `devcontainer exec --workspace-folder . python -m pytest tests/test_auth.py::test_somfy_password_token_returns_token_dict tests/test_auth.py::test_somfy_password_token_bad_credentials -v`
Expected: FAIL — `ImportError` (`_somfy_password_token` not defined).

- [ ] **Step 3: Add the helper and refactor `SomfyAuthStrategy` to use it**

In `pyoverkiz/auth/strategies.py`, add a module-level function (place it near `_raise_for_server_error`, after that function):

```python
async def _somfy_password_token(
    session: ClientSession, username: str, password: str
) -> dict[str, Any]:
    """Perform the Somfy Accounts password grant and return the raw token dict.

    Shared by SomfyAuthStrategy (single-site) and SomfyMultisiteAuthStrategy
    (which feeds the returned access_token into the Keycloak token exchange).
    """
    form = FormData(
        {
            "grant_type": "password",
            "client_id": SOMFY_CLIENT_ID,
            "client_secret": SOMFY_CLIENT_SECRET,
            "username": username,
            "password": password,
        }
    )
    async with session.post(
        f"{SOMFY_API}/oauth/oauth/v2/token/jwt",
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ) as response:
        await _raise_for_server_error(response)
        token = await response.json()

        if token.get("message") == "error.invalid.grant":
            raise SomfyBadCredentialsError(token["message"])

        if not token.get("access_token"):
            raise SomfyServiceError("No Somfy access token provided.")

        return cast(dict[str, Any], token)
```

Then update `SomfyAuthStrategy._request_access_token` so the **password** path delegates to the helper while the **refresh** path stays as-is. Replace the body of `_request_access_token` with:

```python
    async def _request_access_token(
        self, *, grant_type: str, extra_fields: Mapping[str, str]
    ) -> None:
        if grant_type == "password":
            token = await _somfy_password_token(
                self.session,
                self.credentials.username,
                self.credentials.password,
            )
            self.context.update_from_token(token)
            return

        form = FormData(
            {
                "grant_type": grant_type,
                "client_id": SOMFY_CLIENT_ID,
                "client_secret": SOMFY_CLIENT_SECRET,
                **extra_fields,
            }
        )

        async with self.session.post(
            f"{SOMFY_API}/oauth/oauth/v2/token/jwt",
            data=form,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ) as response:
            await _raise_for_server_error(response)
            token = await response.json()

            if token.get("message") == "error.invalid.grant":
                raise SomfyBadCredentialsError(token["message"])

            access_token = token.get("access_token")
            if not access_token:
                raise SomfyServiceError("No Somfy access token provided.")

            self.context.update_from_token(token)
```

- [ ] **Step 4: Run tests to verify they pass (and nothing regressed)**

Run: `devcontainer exec --workspace-folder . python -m pytest tests/test_auth.py -k "somfy" -v`
Expected: PASS — new helper tests pass and existing Somfy tests (`test_somfy_token_502_raises_service_unavailable`, `test_build_auth_strategy_somfy`) still pass.

- [ ] **Step 5: Commit**

```bash
git add pyoverkiz/auth/strategies.py tests/test_auth.py
git commit -m "refactor: extract shared Somfy password-grant helper"
```

---

## Task 3: `SomfyMultisiteAuthStrategy` — login + token exchange

**Files:**
- Modify: `pyoverkiz/auth/strategies.py`
- Test: `tests/test_auth.py`

**Interfaces:**
- Consumes: `_somfy_password_token` (Task 2); `AuthContext`, `GatewayCandidate` (from `pyoverkiz.auth.base`); `UsernamePasswordCredentials`; constants from Task 1.
- Produces: class `SomfyMultisiteAuthStrategy(BaseAuthStrategy)` with:
  - `__init__(self, credentials: UsernamePasswordCredentials, session, server, ssl_context)`.
  - attrs: `self.context: AuthContext`, `self._sites: list[GatewayCandidate]`, `self._site_country: dict[str, str]` (gateway_id → country), `self._selected_site_oid: str | None`, `self._selected_gateway: str | None`, `self._endpoint: str | None`.
  - `async def _token_exchange(self, sso_access_token: str) -> None` — POST to `GINAITE_TOKEN_URL`, populate `self.context`. Raises `SomfyServiceError` on non-200.
  - `async def login(self) -> None` — password grant → token exchange → `discover_gateways()` → auto-select if exactly one.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_auth.py`. First a builder helper (place near `_build_rexel_strategy_with_token`):

```python
def _build_somfy_multisite_strategy():
    """Return a SomfyMultisiteAuthStrategy with a MagicMock session."""
    from unittest.mock import MagicMock

    from aiohttp import ClientSession

    from pyoverkiz.auth.credentials import UsernamePasswordCredentials
    from pyoverkiz.auth.strategies import SomfyMultisiteAuthStrategy
    from pyoverkiz.const import SUPPORTED_SERVERS
    from pyoverkiz.enums import Server

    session = MagicMock(spec=ClientSession)
    strategy = SomfyMultisiteAuthStrategy(
        credentials=UsernamePasswordCredentials("user", "pass"),
        session=session,
        server=SUPPORTED_SERVERS[Server.SOMFY],
        ssl_context=True,
    )
    return strategy, session


def _json_ctx(body, status=200):
    """A MagicMock aiohttp response context manager returning `body` as JSON."""
    from unittest.mock import AsyncMock, MagicMock

    resp = MagicMock()
    resp.status = status
    resp.json = AsyncMock(return_value=body)
    resp.text = AsyncMock(return_value=str(body))
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=resp)
    ctx.__aexit__ = AsyncMock(return_value=None)
    return ctx
```

Then the test:

```python
@pytest.mark.asyncio
async def test_somfy_multisite_token_exchange_populates_context():
    """_token_exchange stores the Ginaite access + refresh token."""
    strategy, session = _build_somfy_multisite_strategy()
    session.post = MagicMock(
        return_value=_json_ctx(
            {"access_token": "ginaite-1", "refresh_token": "r-1", "expires_in": 900}
        )
    )

    await strategy._token_exchange("sso-access")

    assert strategy.context.access_token == "ginaite-1"
    assert strategy.context.refresh_token == "r-1"


@pytest.mark.asyncio
async def test_somfy_multisite_token_exchange_error_raises():
    """A non-200 token exchange raises SomfyServiceError."""
    from pyoverkiz.exceptions import SomfyServiceError

    strategy, session = _build_somfy_multisite_strategy()
    session.post = MagicMock(return_value=_json_ctx({"error": "bad"}, status=400))

    with pytest.raises(SomfyServiceError):
        await strategy._token_exchange("sso-access")
```

(Add `from unittest.mock import MagicMock` at the top of these test functions if not already imported at module scope — the file already imports `MagicMock`/`AsyncMock`.)

- [ ] **Step 2: Run test to verify it fails**

Run: `devcontainer exec --workspace-folder . python -m pytest tests/test_auth.py::test_somfy_multisite_token_exchange_populates_context tests/test_auth.py::test_somfy_multisite_token_exchange_error_raises -v`
Expected: FAIL — `ImportError` (`SomfyMultisiteAuthStrategy` not defined).

- [ ] **Step 3: Implement the class skeleton, `_token_exchange`, and `login`**

Add the imports to the constants import block in `pyoverkiz/auth/strategies.py`:

```python
from pyoverkiz.const import (
    ...
    BOB_API_KEY,
    BOB_SITE_API,
    GINAITE_SUBJECT_ISSUER,
    GINAITE_SUBJECT_TOKEN_TYPE,
    GINAITE_TOKEN_EXCHANGE_GRANT,
    GINAITE_TOKEN_URL,
    SOMFY_CLIENT_ID,
    SOMFY_COUNTRY_REGION,
    SOMFY_REGION_ENDPOINT,
    ...
)
```

Add the class (after `SomfyAuthStrategy`):

```python
class SomfyMultisiteAuthStrategy(BaseAuthStrategy):
    """Somfy multi-site auth: Keycloak token exchange + BOB site directory.

    Reuses the Somfy Accounts password grant, exchanges the SSO token for a
    Ginaite (Keycloak) token, then lists the account's sites from the BOB
    directory. Selecting a site mints a site-scoped token whose Bearer drives
    the classic Overkiz enduser API directly (no gateway header needed).
    """

    def __init__(
        self,
        credentials: UsernamePasswordCredentials,
        session: ClientSession,
        server: ServerConfig,
        ssl_context: ssl.SSLContext | bool,
    ) -> None:
        """Create a Somfy multi-site strategy with a fresh auth context."""
        super().__init__(session, server, ssl_context)
        self.credentials = credentials
        self.context = AuthContext()
        self._sites: list[GatewayCandidate] = []
        self._site_country: dict[str, str] = {}
        self._selected_site_oid: str | None = None
        self._selected_gateway: str | None = None
        self._endpoint: str | None = None

    async def login(self) -> None:
        """Password grant -> token exchange -> discover, auto-select if single."""
        token = await _somfy_password_token(
            self.session, self.credentials.username, self.credentials.password
        )
        await self._token_exchange(token["access_token"])
        self._sites = await self.discover_gateways()
        if len(self._sites) == 1:
            self.select_gateway(self._sites[0].gateway_id)

    async def _token_exchange(self, sso_access_token: str) -> None:
        """Exchange a Somfy Accounts SSO token for a Ginaite token (public client)."""
        form = FormData(
            {
                "grant_type": GINAITE_TOKEN_EXCHANGE_GRANT,
                "client_id": SOMFY_CLIENT_ID,
                "subject_token": sso_access_token,
                "subject_issuer": GINAITE_SUBJECT_ISSUER,
                "subject_token_type": GINAITE_SUBJECT_TOKEN_TYPE,
            }
        )
        async with self.session.post(GINAITE_TOKEN_URL, data=form) as response:
            await _raise_for_server_error(response)
            if response.status != HTTPStatus.OK:
                raise SomfyServiceError(
                    f"Somfy token exchange failed: {response.status}"
                )
            self.context.update_from_token(await response.json())
```

Note: `discover_gateways`, `select_gateway`, `selected_gateway`, `endpoint`, `refresh_if_needed`, and `auth_headers` are added in Task 4. Until then this class is not selectable via the factory, so run only the two new tests in Step 4.

- [ ] **Step 4: Run tests to verify they pass**

Run: `devcontainer exec --workspace-folder . python -m pytest tests/test_auth.py::test_somfy_multisite_token_exchange_populates_context tests/test_auth.py::test_somfy_multisite_token_exchange_error_raises -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyoverkiz/auth/strategies.py tests/test_auth.py
git commit -m "feat: add SomfyMultisiteAuthStrategy login and token exchange"
```

---

## Task 4: Site discovery, selection, region resolution, headers, refresh

**Files:**
- Modify: `pyoverkiz/auth/strategies.py`
- Test: `tests/test_auth.py`

**Interfaces:**
- Consumes: everything from Task 3; `BOB_SITE_API`, `BOB_API_KEY`, `SOMFY_COUNTRY_REGION`, `SOMFY_REGION_ENDPOINT`.
- Produces (methods on `SomfyMultisiteAuthStrategy`):
  - `async def discover_gateways(self) -> list[GatewayCandidate]` — GET BOB `/sites`, flatten to candidates; records `self._site_country[gateway_id] = country`.
  - `def select_gateway(self, gateway_id: str) -> None` — sets `_selected_gateway`, looks up the site's `siteOID` (`home_id`) and country, resolves region → sets `self._endpoint`. Minting the site-scoped token happens lazily via `refresh_if_needed` on the next request (the current token is already valid, just not yet site-scoped) — so `select_gateway` also **invalidates** the context expiry to force a scoped refresh. See implementation.
  - `@property selected_gateway -> str | None`.
  - `@property endpoint -> str` — returns `self._endpoint` if set, else the server placeholder.
  - `async def refresh_if_needed(self) -> bool` — refresh with `?siteOID=<selected>`.
  - `async def auth_headers(self, path=None) -> Mapping[str, str]` — `{"Authorization": f"Bearer {token}"}` or `{}`.
  - `async def _refresh(self) -> None` — the refresh-grant request with `?siteOID`.
  - `def _region_for_country(self, country: str) -> str` — map lookup, raises `SomfyServiceError` on miss.

**Design note on scoping:** After `select_gateway`, the held token is the *global* Ginaite token, not yet scoped to the site. To force a site-scoped mint we set `self.context.expires_at` to now (so `is_expired()` is True) and rely on `refresh_if_needed()` (called by the client before requests) to mint the `?siteOID` token. This keeps a single refresh path.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_auth.py`:

```python
_BOB_SITES = {
    "totalCount": 2,
    "results": [
        {
            "siteOID": "site-a",
            "name": "Mick",
            "country": "NL",
            "currentUserRoles": [{"roleOID": "owner"}],
            "subSites": [
                {
                    "externalOID": "ext-a",
                    "type": "SETUP",
                    "gateways": [{"gatewayId": "2025-0000-0001", "type": 98}],
                }
            ],
        },
        {
            "siteOID": "site-b",
            "name": "Smientstraat",
            "country": "NL",
            "currentUserRoles": [{"roleOID": "owner"}],
            "subSites": [
                {
                    "externalOID": "ext-b",
                    "type": "SETUP",
                    "gateways": [{"gatewayId": "1225-0000-0002", "type": 29}],
                }
            ],
        },
    ],
}


@pytest.mark.asyncio
async def test_somfy_multisite_discover_flattens_sites():
    """discover_gateways returns one GatewayCandidate per gateway across sites."""
    strategy, session = _build_somfy_multisite_strategy()
    strategy.context.access_token = "ginaite-1"
    session.get = MagicMock(return_value=_json_ctx(_BOB_SITES))

    candidates = await strategy.discover_gateways()

    assert [c.gateway_id for c in candidates] == ["2025-0000-0001", "1225-0000-0002"]
    assert candidates[0].home_id == "site-a"
    assert candidates[0].label == "Mick"
    assert candidates[0].external_id == "ext-a"


@pytest.mark.asyncio
async def test_somfy_multisite_select_resolves_region_endpoint():
    """Selecting a gateway resolves its country to the EMEA endpoint."""
    strategy, session = _build_somfy_multisite_strategy()
    strategy.context.access_token = "ginaite-1"
    session.get = MagicMock(return_value=_json_ctx(_BOB_SITES))
    await strategy.discover_gateways()

    strategy.select_gateway("2025-0000-0001")

    assert strategy.selected_gateway == "2025-0000-0001"
    assert strategy._selected_site_oid == "site-a"
    assert strategy.endpoint == (
        "https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/"
    )


@pytest.mark.asyncio
async def test_somfy_multisite_select_unknown_country_raises():
    """A country absent from the region map raises SomfyServiceError."""
    from pyoverkiz.exceptions import SomfyServiceError

    strategy, session = _build_somfy_multisite_strategy()
    strategy.context.access_token = "ginaite-1"
    unknown = {
        "totalCount": 1,
        "results": [
            {
                "siteOID": "site-x",
                "name": "Mars",
                "country": "ZZ",
                "currentUserRoles": [{"roleOID": "owner"}],
                "subSites": [
                    {"externalOID": "ext-x", "gateways": [{"gatewayId": "gw-x"}]}
                ],
            }
        ],
    }
    session.get = MagicMock(return_value=_json_ctx(unknown))
    await strategy.discover_gateways()

    with pytest.raises(SomfyServiceError, match="ZZ"):
        strategy.select_gateway("gw-x")


@pytest.mark.asyncio
async def test_somfy_multisite_endpoint_defaults_to_placeholder_before_select():
    """Before selection, endpoint falls back to the server config placeholder."""
    strategy, _ = _build_somfy_multisite_strategy()
    assert strategy.endpoint == (
        "https://ha101-1.overkiz.com/enduser-mobile-web/enduserAPI/"
    )


@pytest.mark.asyncio
async def test_somfy_multisite_auth_headers():
    """auth_headers returns the Bearer token, or {} when absent (no gateway header)."""
    strategy, _ = _build_somfy_multisite_strategy()
    assert await strategy.auth_headers() == {}
    strategy.context.access_token = "ginaite-1"
    headers = await strategy.auth_headers()
    assert headers == {"Authorization": "Bearer ginaite-1"}
    assert "gatewayId" not in headers


@pytest.mark.asyncio
async def test_somfy_multisite_refresh_scopes_to_selected_site():
    """refresh_if_needed posts a refresh grant to the ?siteOID URL."""
    strategy, session = _build_somfy_multisite_strategy()
    strategy.context.access_token = "ginaite-1"
    strategy.context.refresh_token = "r-1"
    session.get = MagicMock(return_value=_json_ctx(_BOB_SITES))
    await strategy.discover_gateways()
    strategy.select_gateway("2025-0000-0001")  # forces expiry

    posted = _json_ctx({"access_token": "scoped-1", "refresh_token": "r-2"})
    session.post = MagicMock(return_value=posted)

    refreshed = await strategy.refresh_if_needed()

    assert refreshed is True
    assert strategy.context.access_token == "scoped-1"
    # The refresh URL must carry ?siteOID=<selected site oid>.
    called_url = session.post.call_args.args[0]
    assert "siteOID=site-a" in called_url
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `devcontainer exec --workspace-folder . python -m pytest tests/test_auth.py -k "somfy_multisite_discover or somfy_multisite_select or somfy_multisite_endpoint or somfy_multisite_auth_headers or somfy_multisite_refresh" -v`
Expected: FAIL — `AttributeError` (`discover_gateways` etc. not defined).

- [ ] **Step 3: Implement the methods**

Add to `SomfyMultisiteAuthStrategy` in `pyoverkiz/auth/strategies.py`:

```python
    async def discover_gateways(self) -> list[GatewayCandidate]:
        """List the account's sites from BOB, flattened to gateway candidates."""
        data = await self._bob_get("sites?withGateways=true&limit=20&offset=0")
        candidates: list[GatewayCandidate] = []
        self._site_country = {}
        for site in data.get("results", []):
            site_oid = str(site["siteOID"])
            label = site.get("name")
            country = site.get("country")
            for sub in site.get("subSites", []):
                external_id = sub.get("externalOID")
                for gateway in sub.get("gateways", []):
                    gateway_id = str(gateway["gatewayId"])
                    if country is not None:
                        self._site_country[gateway_id] = str(country)
                    candidates.append(
                        GatewayCandidate(
                            gateway_id=gateway_id,
                            home_id=site_oid,
                            label=label,
                            external_id=(
                                str(external_id) if external_id is not None else None
                            ),
                        )
                    )
        self._sites = candidates
        return candidates

    def select_gateway(self, gateway_id: str) -> None:
        """Scope subsequent requests to the given gateway's site and region."""
        site = next(
            (s for s in self._sites if s.gateway_id == gateway_id),
            None,
        )
        if site is None:
            raise SomfyServiceError(f"Unknown gateway id: {gateway_id}")

        country = self._site_country.get(gateway_id)
        if not country:
            raise SomfyServiceError(
                f"No country known for gateway {gateway_id}; cannot resolve region."
            )
        region = self._region_for_country(country)

        self._selected_gateway = gateway_id
        self._selected_site_oid = site.home_id
        self._endpoint = SOMFY_REGION_ENDPOINT[region]
        # Force the next request to mint a site-scoped token via refresh.
        self.context.expires_at = datetime.datetime.now(datetime.UTC)

    def _region_for_country(self, country: str) -> str:
        """Map an ISO country to an Overkiz region, or raise if unmapped."""
        region = SOMFY_COUNTRY_REGION.get(country.upper())
        if region is None:
            raise SomfyServiceError(
                f"No Overkiz region mapped for Somfy site country {country!r}."
            )
        return region

    @property
    def selected_gateway(self) -> str | None:
        """Return the currently selected gateway id, or None."""
        return self._selected_gateway

    @property
    def endpoint(self) -> str:
        """Return the resolved per-site endpoint, or the server placeholder."""
        return self._endpoint or self.server.endpoint

    async def refresh_if_needed(self) -> bool:
        """Mint/refresh a site-scoped token when expired."""
        if not self.context.is_expired() or not self.context.refresh_token:
            return False
        await self._refresh()
        return True

    async def _refresh(self) -> None:
        """Refresh grant scoped to the selected site (?siteOID)."""
        url = GINAITE_TOKEN_URL
        if self._selected_site_oid:
            url = f"{GINAITE_TOKEN_URL}?siteOID={self._selected_site_oid}"
        form = FormData(
            {
                "grant_type": "refresh_token",
                "client_id": SOMFY_CLIENT_ID,
                "refresh_token": cast(str, self.context.refresh_token),
            }
        )
        async with self.session.post(url, data=form) as response:
            await _raise_for_server_error(response)
            if response.status != HTTPStatus.OK:
                raise SomfyServiceError(f"Somfy token refresh failed: {response.status}")
            self.context.update_from_token(await response.json())

    async def auth_headers(self, path: str | None = None) -> Mapping[str, str]:
        """Return the Bearer header (site-scoped token), or {} before login."""
        if self.context.access_token:
            return {"Authorization": f"Bearer {self.context.access_token}"}
        return {}

    async def _bob_get(self, path: str) -> dict[str, Any]:
        """GET a BOB site-directory resource with Bearer + X-Api-Key."""
        async with self.session.get(
            f"{BOB_SITE_API}/{path}",
            headers={
                "Authorization": f"Bearer {self.context.access_token}",
                "X-Api-Key": BOB_API_KEY,
            },
            ssl=self._ssl,
        ) as response:
            await _raise_for_server_error(response)
            if response.status != HTTPStatus.OK:
                raise SomfyServiceError(f"BOB request failed: {response.status}")
            return cast(dict[str, Any], await response.json())
```

Ensure `datetime` is imported at the top of the module (add `import datetime` if absent).

- [ ] **Step 4: Run tests to verify they pass**

Run: `devcontainer exec --workspace-folder . python -m pytest tests/test_auth.py -k "somfy_multisite" -v`
Expected: PASS (all Task 3 + Task 4 multisite tests).

- [ ] **Step 5: Commit**

```bash
git add pyoverkiz/auth/strategies.py tests/test_auth.py
git commit -m "feat: add Somfy multi-site site discovery and region scoping"
```

---

## Task 5: Route `Server.SOMFY` in the factory

**Files:**
- Modify: `pyoverkiz/auth/factory.py`
- Test: `tests/test_auth.py`

**Interfaces:**
- Consumes: `SomfyMultisiteAuthStrategy` (Task 3/4), `Server.SOMFY` (Task 1).
- Produces: `build_auth_strategy(..., server=Server.SOMFY, credentials=UsernamePasswordCredentials)` returns a `SomfyMultisiteAuthStrategy`.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_auth.py`, inside `class TestAuthFactory`:

```python
    @pytest.mark.asyncio
    async def test_build_auth_strategy_somfy_multisite(self):
        """Server.SOMFY + username/password builds SomfyMultisiteAuthStrategy."""
        from pyoverkiz.auth.strategies import SomfyMultisiteAuthStrategy
        from pyoverkiz.const import SUPPORTED_SERVERS

        strategy = build_auth_strategy(
            server_config=SUPPORTED_SERVERS[Server.SOMFY],
            credentials=UsernamePasswordCredentials("user", "pass"),
            session=AsyncMock(spec=ClientSession),
            ssl_context=True,
        )

        assert isinstance(strategy, SomfyMultisiteAuthStrategy)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `devcontainer exec --workspace-folder . python -m pytest "tests/test_auth.py::TestAuthFactory::test_build_auth_strategy_somfy_multisite" -v`
Expected: FAIL — returns `SessionLoginStrategy` (fallthrough), not `SomfyMultisiteAuthStrategy`.

- [ ] **Step 3: Add the factory branch**

In `pyoverkiz/auth/factory.py`, import the strategy:

```python
from pyoverkiz.auth.strategies import (
    ...
    SomfyAuthStrategy,
    SomfyMultisiteAuthStrategy,
)
```

Add a branch after the `Server.SOMFY_EUROPE` branch:

```python
    if server == Server.SOMFY:
        return SomfyMultisiteAuthStrategy(
            _ensure_credentials(credentials, UsernamePasswordCredentials),
            session,
            server_config,
            ssl_context,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `devcontainer exec --workspace-folder . python -m pytest "tests/test_auth.py::TestAuthFactory::test_build_auth_strategy_somfy_multisite" -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyoverkiz/auth/factory.py tests/test_auth.py
git commit -m "feat: route Server.SOMFY to SomfyMultisiteAuthStrategy"
```

---

## Task 6: Full-suite verification, lint, and type checks

**Files:** none (verification only).

- [ ] **Step 1: Run the full test suite**

Run: `devcontainer exec --workspace-folder . python -m pytest -q`
Expected: PASS (no regressions).

- [ ] **Step 2: Run lint and format checks**

Run: `devcontainer exec --workspace-folder . ruff check pyoverkiz tests`
Run: `devcontainer exec --workspace-folder . ruff format --check pyoverkiz tests`
Expected: no errors. If `ruff format` reports changes, run it without `--check` and re-commit.

- [ ] **Step 3: Run type checks**

Run: `devcontainer exec --workspace-folder . mypy pyoverkiz`
Run: `devcontainer exec --workspace-folder . ty check pyoverkiz`
Expected: no errors.

- [ ] **Step 4: Commit any formatting fixes**

```bash
git add -A
git commit -m "chore: lint and format Somfy multi-site changes" || echo "nothing to commit"
```

---

## Self-Review Notes

- **Spec coverage:** Server model (Task 1), Path A login + token exchange (Task 3), discovery + region map + per-site scoping (Task 4), factory routing (Task 5), testing (all tasks) — all covered. Invitations and Path B are explicitly out of scope in the spec; no tasks. No `client.py` task — spec confirms none needed.
- **Region map:** `NL` verified live; other countries seeded from existing regional server groupings (flagged for the user to confirm before non-EMEA release).
- **Type consistency:** `discover_gateways`/`select_gateway`/`selected_gateway`/`endpoint`/`refresh_if_needed`/`auth_headers` match the `AuthStrategy` + `SupportsGatewaySelection` protocols in `pyoverkiz/auth/base.py`. Helper name `_somfy_password_token` used consistently in Tasks 2 and 3.
```
