"""Credentials for authentication strategies."""

from __future__ import annotations

from abc import ABC
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field


class Credentials(ABC):  # noqa: B024 - marker class uses ABC to prevent direct instantiation
    """Abstract base class for auth credentials."""


@dataclass(slots=True)
class UsernamePasswordCredentials(Credentials):
    """Credentials using username and password."""

    username: str
    password: str = field(repr=False)


@dataclass(slots=True)
class TokenCredentials(Credentials):
    """Credentials using an (API) token."""

    token: str = field(repr=False)


@dataclass(slots=True)
class LocalTokenCredentials(TokenCredentials):
    """Credentials using a local API token."""


@dataclass(slots=True)
class SomfyTokenCredentials(Credentials):
    """Warm-start credentials for a previously-selected Somfy site.

    Skips the password grant, Keycloak token exchange, and site discovery on
    reload: the caller persists the Ginaite ``refresh_token`` plus the selected
    site's ``site_oid`` and ``region``, and pyoverkiz mints a site-scoped access
    token directly on the first request. ``gateway_id`` is optional bookkeeping
    (the id the user selected) and is surfaced via ``selected_gateway``.

    Ginaite rotates the refresh token on refresh, so supply an async
    ``on_token_refresh`` callback to re-persist the new refresh token; without
    it a rotated token is only kept in memory and a later reload would fail.
    """

    refresh_token: str = field(repr=False)
    site_oid: str
    region: str
    gateway_id: str | None = None
    on_token_refresh: Callable[[str], Awaitable[None]] | None = None


@dataclass(slots=True)
class RexelOAuthCodeCredentials(Credentials):
    """Credentials using Rexel OAuth2 authorization code with PKCE."""

    code: str = field(repr=False)
    redirect_uri: str
    code_verifier: str


@dataclass(slots=True)
class RexelTokenCredentials(Credentials):
    """Rexel credentials backed by an externally-managed access token.

    Use this when the OAuth2 lifecycle is owned outside pyoverkiz (for example
    Home Assistant's ``application_credentials`` platform). Supply either an
    async ``access_token_callback`` (called before each request, so the owner
    can refresh and persist tokens) or a static ``access_token`` for simple
    standalone or test use. ``gateway_id`` pre-selects a gateway on reload,
    skipping discovery.
    """

    access_token_callback: Callable[[], Awaitable[str]] | None = None
    access_token: str | None = field(default=None, repr=False)
    gateway_id: str | None = None

    def __post_init__(self) -> None:
        """Require at least one access-token source."""
        if not self.access_token_callback and not self.access_token:
            raise ValueError("Provide either access_token_callback or access_token.")
