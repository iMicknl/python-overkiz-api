"""Dispatch logic for mapping Overkiz API error responses to specific exceptions."""

from __future__ import annotations

from json import JSONDecodeError

from aiohttp import ClientResponse

from pyoverkiz.exceptions import (
    AccessDeniedToGatewayException,
    ActionGroupSetupNotFoundException,
    ApplicationNotAllowedException,
    BadCredentialsException,
    BaseOverkizException,
    DuplicateActionOnDeviceException,
    ExecutionQueueFullException,
    InvalidCommandException,
    InvalidEventListenerIdException,
    InvalidTokenException,
    MaintenanceException,
    MissingAPIKeyException,
    MissingAuthorizationTokenException,
    NoRegisteredEventListenerException,
    NoSuchResourceException,
    NotAuthenticatedException,
    NotSuchTokenException,
    OverkizException,
    ResourceAccessDeniedException,
    ServiceUnavailableException,
    SessionAndBearerInSameRequestException,
    TooManyAttemptsBannedException,
    TooManyConcurrentRequestsException,
    TooManyExecutionsException,
    TooManyRequestsException,
    UnknownObjectException,
    UnknownUserException,
)

# Primary dispatch: (errorCode, message_substring) -> exception class.
# Checked in order; first match wins. Use errorCode as the primary key to
# reduce brittleness across cloud vs. local API variants.
_ERROR_CODE_MESSAGE_MAP: list[tuple[str, str | None, type[BaseOverkizException]]] = [
    # --- errorCode is the sole discriminator ---
    ("DUPLICATE_FIELD_OR_VALUE", None, DuplicateActionOnDeviceException),
    ("INVALID_FIELD_VALUE", None, ActionGroupSetupNotFoundException),
    ("INVALID_API_CALL", None, NoSuchResourceException),
    ("EXEC_QUEUE_FULL", None, ExecutionQueueFullException),
    # --- errorCode + message substring ---
    ("AUTHENTICATION_ERROR", "Too many requests", TooManyRequestsException),
    ("AUTHENTICATION_ERROR", "Bad credentials", BadCredentialsException),
    ("AUTHENTICATION_ERROR", "API key is required", MissingAPIKeyException),
    ("AUTHENTICATION_ERROR", "No such user account", UnknownUserException),
    ("RESOURCE_ACCESS_DENIED", "Not authenticated", NotAuthenticatedException),
    (
        "RESOURCE_ACCESS_DENIED",
        "Missing authorization token",
        MissingAuthorizationTokenException,
    ),
    (
        "RESOURCE_ACCESS_DENIED",
        "too many concurrent requests",
        TooManyConcurrentRequestsException,
    ),
    ("RESOURCE_ACCESS_DENIED", "Too many executions", TooManyExecutionsException),
    (
        "RESOURCE_ACCESS_DENIED",
        "Access denied to gateway",
        AccessDeniedToGatewayException,
    ),
    (
        "RESOURCE_ACCESS_DENIED",
        "cannot be accessed through this application",
        ApplicationNotAllowedException,
    ),
    ("UNSUPPORTED_OPERATION", "No such command", InvalidCommandException),
    (
        "UNSPECIFIED_ERROR",
        "Invalid event listener id",
        InvalidEventListenerIdException,
    ),
    (
        "UNSPECIFIED_ERROR",
        "No registered event listener",
        NoRegisteredEventListenerException,
    ),
    ("UNSPECIFIED_ERROR", "Unknown object", UnknownObjectException),
]

# Message-only fallback patterns for responses where the errorCode alone is
# not enough or may vary across API versions.
_MESSAGE_FALLBACK_MAP: list[tuple[str, type[BaseOverkizException]]] = [
    ("Too many executions", TooManyExecutionsException),
    (
        "Cannot use JSESSIONID and bearer token",
        SessionAndBearerInSameRequestException,
    ),
    ("Too many attempts with an invalid token", TooManyAttemptsBannedException),
    ("Invalid token", InvalidTokenException),
    ("Not such token with UUID", NotSuchTokenException),
    ("Unknown user", UnknownUserException),
    ("No such command", InvalidCommandException),
    ("No registered event listener", NoRegisteredEventListenerException),
    ("Unknown object", UnknownObjectException),
    ("Access denied to gateway", AccessDeniedToGatewayException),
]

# Fallback when errorCode is recognized but no message pattern matched.
_ERROR_CODE_FALLBACK_MAP: dict[str, type[BaseOverkizException]] = {
    "AUTHENTICATION_ERROR": BadCredentialsException,
    "RESOURCE_ACCESS_DENIED": ResourceAccessDeniedException,
}


async def check_response(response: ClientResponse) -> None:
    """Check the response returned by the OverKiz API."""
    if response.status in [200, 204]:
        return

    try:
        result = await response.json(content_type=None)
    except JSONDecodeError as error:
        result = await response.text()

        if "is down for maintenance" in result:
            raise MaintenanceException("Server is down for maintenance") from error

        if response.status == 503:
            raise ServiceUnavailableException(result) from error

        raise OverkizException(
            f"Unknown error while requesting {response.url}. {response.status} - {result}"
        ) from error

    error_code = result.get("errorCode", "")

    if error_code:
        # Error messages between cloud and local Overkiz servers can be slightly different.
        # To make it easier to have a strict match for these errors, we remove the double quotes and the period at the end.

        # An error message can have an empty (None) message
        message = message.strip('".') if (message := result.get("error")) else ""

        # 1. Primary dispatch: match on errorCode (+ optional message substring)
        for code, pattern, exc_class in _ERROR_CODE_MESSAGE_MAP:
            if error_code == code and (pattern is None or pattern in message):
                raise exc_class(message)

        # 2. Message-only fallback for patterns that may appear under varying errorCodes
        for pattern, exc_class in _MESSAGE_FALLBACK_MAP:
            if pattern in message:
                raise exc_class(message)

        # 3. errorCode category fallback (known code, unknown message)
        if error_code in _ERROR_CODE_FALLBACK_MAP:
            raise _ERROR_CODE_FALLBACK_MAP[error_code](message or str(result))

    # Undefined Overkiz exception
    raise OverkizException(result)
