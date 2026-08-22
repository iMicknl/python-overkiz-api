"""Base classes for authentication strategies."""

from __future__ import annotations

import datetime
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pyoverkiz.auth.credentials import SomfyTokenCredentials


@dataclass(slots=True)
class AuthContext:
    """Authentication context holding tokens and expiration."""

    access_token: str | None = field(default=None, repr=False)
    refresh_token: str | None = field(default=None, repr=False)
    expires_at: datetime.datetime | None = None

    def is_expired(self, *, skew_seconds: int = 5) -> bool:
        """Check if the access token is expired, considering a skew time."""
        if not self.expires_at:
            return False

        return datetime.datetime.now(
            datetime.UTC
        ) >= self.expires_at - datetime.timedelta(seconds=skew_seconds)

    def update_from_token(self, token: dict[str, Any]) -> None:
        """Update context from an OAuth token response."""
        self.access_token = str(token["access_token"])
        self.refresh_token = (
            str(token["refresh_token"]) if "refresh_token" in token else None
        )
        expires_in = token.get("expires_in")
        if expires_in is not None:
            self.expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
                seconds=int(expires_in)
            )


class AuthStrategy(Protocol):
    """Protocol for authentication strategies."""

    async def login(self) -> None:
        """Perform login to obtain tokens."""

    async def refresh_if_needed(self) -> bool:
        """Refresh tokens if they are expired. Return True if refreshed."""

    async def auth_headers(self, path: str | None = None) -> Mapping[str, str]:
        """Generate authentication headers for requests."""

    @property
    def endpoint(self) -> str:
        """Return the base API endpoint for requests."""

    async def close(self) -> None:
        """Clean up any resources held by the strategy."""


@dataclass(slots=True)
class GatewayCandidate:
    """A selectable Overkiz gateway behind a multi-account directory."""

    gateway_id: str
    home_id: str | None = None
    label: str | None = None
    external_id: str | None = None
    country: str | None = None
    # Somfy only. Reported, not acted on: a site the account was merely invited
    # to is listed like any other, and even the most limited access level keeps
    # control of some devices, so such a site is expected to work in a reduced
    # form rather than not at all. Filtering would also need an allowlist, and
    # only `owner` and `secondary` are fixed values -- every custom or installer
    # role is an opaque id, so unrecognised must not mean unusable. Callers get
    # the roles to explain the reduction to a user instead.
    roles: list[str] = field(default_factory=list)


@runtime_checkable
class SupportsGatewaySelection(Protocol):
    """Optional capability: discover and select among multiple gateways."""

    async def discover_gateways(self) -> list[GatewayCandidate]:
        """Return all selectable gateways for the authenticated account."""

    def select_gateway(self, gateway_id: str) -> None:
        """Select the gateway to scope subsequent requests to."""

    @property
    def selected_gateway(self) -> str | None:
        """Return the currently selected gateway id, or None."""


@runtime_checkable
class SupportsSessionResume(Protocol):
    """Optional capability: snapshot the session for later resume without re-login."""

    def to_credentials(
        self,
        on_token_refresh: Callable[[str], Awaitable[None]] | None = None,
    ) -> SomfyTokenCredentials:
        """Return resume credentials for the current session."""
