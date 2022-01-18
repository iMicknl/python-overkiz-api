from pyoverkiz.client import OverkizClient


class SimpleClient(OverkizClient):
    async def login(
        self,
        register_event_listener: bool | None = True,
    ) -> bool:
        """
        Authenticate and create an API session allowing access to the other operations.
        Caller must provide one of [userId+userPassword, userId+ssoToken, accessToken, jwt]
        """

        payload = {"userId": self.username, "userPassword": self.password}
        response = await self.__post("login", data=payload)

        if response.get("success"):
            if register_event_listener:
                await self.register_event_listener()
            return True

        return False
