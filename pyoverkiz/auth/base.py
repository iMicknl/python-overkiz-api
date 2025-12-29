"""Base classes for authentication strategies."""

from __future__ import annotations

import datetime
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class AuthContext:
    """Authentication context holding tokens and expiration."""

    access_token: str | None = None
    refresh_token: str | None = None
    expires_at: datetime.datetime | None = None

    def is_expired(self, *, skew_seconds: int = 5) -> bool:
        """Check if the access token is expired, considering a skew time."""
        if not self.expires_at:
            return False

        return datetime.datetime.now() >= self.expires_at - datetime.timedelta(
            seconds=skew_seconds
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
