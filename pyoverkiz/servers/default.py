from pyoverkiz.servers.overkiz_server import OverkizServer


class NexityServer(OverkizServer):
    async def login(self, username: str, password: str) -> bool:
        """
        Authenticate and create an API session allowing access to the other operations.
        Caller must provide one of [userId+userPassword, userId+ssoToken, accessToken, jwt]
        """

        payload = {"userId": username, "userPassword": password}

        response = await self.post("login", data=payload)

        if response.get("success"):
            return True

        return False
