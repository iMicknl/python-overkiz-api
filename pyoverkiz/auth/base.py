"""Base classes for authentication strategies."""

from __future__ import annotations

import datetime
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol


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

    def auth_headers(self, path: str | None = None) -> Mapping[str, str]:
        """Generate authentication headers for requests."""

    async def close(self) -> None:
        """Clean up any resources held by the strategy."""
