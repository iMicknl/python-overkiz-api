from attr import define, field

from pyoverkiz.clients.overkiz import OverkizClient


@define(kw_only=True)
class DefaultClient(OverkizClient):

    username: str
    password: str = field(repr=lambda _: "***")

    async def _login(self) -> bool:
        """
        Authenticate and create an API session allowing access to the other operations.
        Caller must provide one of [userId+userPassword, userId+ssoToken, accessToken, jwt]
        """
        payload = {"userId": self.username, "userPassword": self.password}
        response = await self.post("login", data=payload)
        return "success" in response
