from __future__ import annotations

from attr import field

from pyoverkiz.clients.overkiz import OverkizClient


class SomfyLocalClient(OverkizClient):

    _ssl: bool = field(default=False, init=False)

    async def _login(self, _username: str, _password: str) -> bool:
        """There is no login needed for Somfy Local API"""
        raise NotImplementedError("There is no login needed for the Somfy Local API")

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.password}"}
