from __future__ import annotations

from attr import define, field

from pyoverkiz.clients.overkiz import OverkizClient


@define(kw_only=True)
class SomfyLocalClient(OverkizClient):

    _ssl: bool = field(default=False, init=False)
    token: str = field(repr=lambda _: "***")

    async def _login(self) -> bool:
        """There is no login needed for Somfy Local API"""
        raise NotImplementedError("There is no login needed for the Somfy Local API")

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}
