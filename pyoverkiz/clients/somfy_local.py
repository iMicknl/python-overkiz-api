from __future__ import annotations

from typing import Any

from pyoverkiz.clients.overkiz import OverkizClient
from pyoverkiz.types import JSON


class SomfyLocalClient(OverkizClient):
    async def _login(self, username: str, password: str) -> bool:
        """There is no login for Somfy Local"""
        return True

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.password}"}

    async def get(
        self,
        path: str,
        _ssl: bool = False,
    ) -> Any:
        """Make a GET request to the OverKiz API"""

        return await super().get(path, ssl=False)

    async def post(
        self,
        path: str,
        payload: JSON | None = None,
        data: JSON | None = None,
        _ssl: bool = False,
    ) -> Any:
        """Make a POST request to the OverKiz API"""
        return await super().post(path, payload=payload, data=data, ssl=False)

    async def delete(
        self,
        path: str,
        _ssl: bool = False,
    ) -> None:
        """Make a DELETE request to the OverKiz API"""
        return await super().delete(path, ssl=False)
