from __future__ import annotations

import datetime
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class AuthContext:
    access_token: str | None = None
    refresh_token: str | None = None
    expires_at: datetime.datetime | None = None

    def is_expired(self, *, skew_seconds: int = 5) -> bool:
        if not self.expires_at:
            return False

        return datetime.datetime.now() >= self.expires_at - datetime.timedelta(
            seconds=skew_seconds
        )


class AuthStrategy(Protocol):
    async def login(self) -> None: ...

    async def refresh_if_needed(self) -> bool: ...

    def auth_headers(self, path: str | None = None) -> Mapping[str, str]: ...

    async def close(self) -> None: ...
