from pyoverkiz.clients.overkiz import OverkizClient


class DefaultClient(OverkizClient):
    async def _login(self, username: str, password: str) -> bool:
        """
        Authenticate and create an API session allowing access to the other operations.
        Caller must provide one of [userId+userPassword, userId+ssoToken, accessToken, jwt]
        """
        payload = {"userId": username, "userPassword": password}
        response = await self.post("login", data=payload)
        return "success" in response
