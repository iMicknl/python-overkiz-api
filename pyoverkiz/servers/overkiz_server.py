from __future__ import annotations

from abc import ABC, abstractmethod
from json import JSONDecodeError
from typing import Any

from aiohttp import ClientResponse, ClientSession
from attr import define

from pyoverkiz.exceptions import (
    AccessDeniedToGatewayException,
    BadCredentialsException,
    InvalidCommandException,
    InvalidEventListenerIdException,
    InvalidTokenException,
    MaintenanceException,
    MissingAuthorizationTokenException,
    NoRegisteredEventListenerException,
    NotAuthenticatedException,
    NotSuchTokenException,
    SessionAndBearerInSameRequestException,
    TooManyAttemptsBannedException,
    TooManyConcurrentRequestsException,
    TooManyExecutionsException,
    TooManyRequestsException,
    UnknownObjectException,
    UnknownUserException,
)
from pyoverkiz.types import JSON


@define(kw_only=True)
class OverkizServer(ABC):
    """Class to describe an Overkiz server."""

    name: str
    endpoint: str
    manufacturer: str
    session: ClientSession

    configuration_url: str | None

    @abstractmethod
    async def login(self, username: str, password: str) -> bool:
        """Login to the server."""

    @property
    def _headers(self) -> dict[str, str]:
        return {}

    async def get(self, path: str) -> Any:
        """Make a GET request to the OverKiz API"""

        async with self.session.get(
            f"{self.endpoint}{path}",
            headers=self._headers,
        ) as response:
            await self.check_response(response)
            return await response.json()

    async def post(
        self, path: str, payload: JSON | None = None, data: JSON | None = None
    ) -> Any:
        """Make a POST request to the OverKiz API"""

        async with self.session.post(
            f"{self.endpoint}{path}",
            data=data,
            json=payload,
            headers=self._headers,
        ) as response:
            await self.check_response(response)
            return await response.json()

    async def delete(self, path: str) -> None:
        """Make a DELETE request to the OverKiz API"""

        async with self.session.delete(
            f"{self.endpoint}{path}",
            headers=self._headers,
        ) as response:
            await self.check_response(response)

    @staticmethod
    async def check_response(response: ClientResponse) -> None:
        """Check the response returned by the OverKiz API"""

        # pylint: disable=too-many-branches

        if response.status in [200, 204]:
            return

        try:
            result = await response.json(content_type=None)
        except JSONDecodeError as error:
            result = await response.text()
            if "Server is down for maintenance" in result:
                raise MaintenanceException("Server is down for maintenance") from error
            raise Exception(
                f"Unknown error while requesting {response.url}. {response.status} - {result}"
            ) from error

        if result.get("errorCode"):
            message = result.get("error")

            # {"errorCode": "AUTHENTICATION_ERROR",
            # "error": "Too many requests, try again later : login with xxx@xxx.tld"}
            if "Too many requests" in message:
                raise TooManyRequestsException(message)

            # {"errorCode": "AUTHENTICATION_ERROR", "error": "Bad credentials"}
            if message == "Bad credentials":
                raise BadCredentialsException(message)

            # {"errorCode": "RESOURCE_ACCESS_DENIED", "error": "Not authenticated"}
            if message == "Not authenticated":
                raise NotAuthenticatedException(message)

            # {"error":"Missing authorization token.","errorCode":"RESOURCE_ACCESS_DENIED"}
            if message == "Missing authorization token.":
                raise MissingAuthorizationTokenException(message)

            # {"error": "Server busy, please try again later. (Too many executions)"}
            if message == "Server busy, please try again later. (Too many executions)":
                raise TooManyExecutionsException(message)

            # {"error": "UNSUPPORTED_OPERATION", "error": "No such command : ..."}
            if "No such command" in message:
                raise InvalidCommandException(message)

            # {'errorCode': 'UNSPECIFIED_ERROR', 'error': 'Invalid event listener id : ...'}
            if "Invalid event listener id" in message:
                raise InvalidEventListenerIdException(message)

            # {'errorCode': 'UNSPECIFIED_ERROR', 'error': 'No registered event listener'}
            if message == "No registered event listener":
                raise NoRegisteredEventListenerException(message)

            # {"errorCode": "RESOURCE_ACCESS_DENIED",  "error": "too many concurrent requests"}
            if message == "too many concurrent requests":
                raise TooManyConcurrentRequestsException(message)

            if message == "Cannot use JSESSIONID and bearer token in same request":
                raise SessionAndBearerInSameRequestException(message)

            if (
                message
                == "Too many attempts with an invalid token, temporarily banned."
            ):
                raise TooManyAttemptsBannedException(message)

            if "Invalid token : " in message:
                raise InvalidTokenException(message)

            if "Not such token with UUID: " in message:
                raise NotSuchTokenException(message)

            if "Unknown user :" in message:
                raise UnknownUserException(message)

            # {"error":"Unknown object.","errorCode":"UNSPECIFIED_ERROR"}
            if message == "Unknown object.":
                raise UnknownObjectException(message)

            # {'errorCode': 'RESOURCE_ACCESS_DENIED', 'error': 'Access denied to gateway #1234-5678-1234 for action ADD_TOKEN'}
            if "Access denied to gateway" in message:
                raise AccessDeniedToGatewayException(message)

        raise Exception(message if message else result)
