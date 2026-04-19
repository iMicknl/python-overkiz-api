"""Dispatch logic for mapping Overkiz API error responses to specific errors."""

from __future__ import annotations

from json import JSONDecodeError

from aiohttp import ClientResponse

from pyoverkiz.exceptions import (
    AccessDeniedToGatewayError,
    ActionGroupSetupNotFoundError,
    ApplicationNotAllowedError,
    BadCredentialsError,
    BaseOverkizError,
    DuplicateActionOnDeviceError,
    ExecutionQueueFullError,
    InvalidCommandError,
    InvalidEventListenerIdError,
    InvalidTokenError,
    MaintenanceError,
    MissingAPIKeyError,
    MissingAuthorizationTokenError,
    NoRegisteredEventListenerError,
    NoSuchResourceError,
    NoSuchTokenError,
    NotAuthenticatedError,
    OverkizError,
    ResourceAccessDeniedError,
    ServiceUnavailableError,
    SessionAndBearerInSameRequestError,
    TooManyAttemptsBannedError,
    TooManyConcurrentRequestsError,
    TooManyExecutionsError,
    TooManyRequestsError,
    UnknownObjectError,
    UnknownUserError,
)

# Primary dispatch: (errorCode, message_substring) -> error class.
# Checked in order; first match wins. Use errorCode as the primary key to
# reduce brittleness across cloud vs. local API variants.
_ERROR_CODE_MESSAGE_MAP: list[tuple[str, str | None, type[BaseOverkizError]]] = [
    # --- errorCode is the sole discriminator ---
    ("DUPLICATE_FIELD_OR_VALUE", None, DuplicateActionOnDeviceError),
    ("INVALID_FIELD_VALUE", None, ActionGroupSetupNotFoundError),
    ("INVALID_API_CALL", None, NoSuchResourceError),
    ("EXEC_QUEUE_FULL", None, ExecutionQueueFullError),
    # --- errorCode + message substring ---
    ("AUTHENTICATION_ERROR", "Too many requests", TooManyRequestsError),
    ("AUTHENTICATION_ERROR", "Bad credentials", BadCredentialsError),
    ("AUTHENTICATION_ERROR", "API key is required", MissingAPIKeyError),
    ("AUTHENTICATION_ERROR", "No such user account", UnknownUserError),
    ("RESOURCE_ACCESS_DENIED", "Not authenticated", NotAuthenticatedError),
    (
        "RESOURCE_ACCESS_DENIED",
        "Missing authorization token",
        MissingAuthorizationTokenError,
    ),
    (
        "RESOURCE_ACCESS_DENIED",
        "too many concurrent requests",
        TooManyConcurrentRequestsError,
    ),
    ("RESOURCE_ACCESS_DENIED", "Too many executions", TooManyExecutionsError),
    (
        "RESOURCE_ACCESS_DENIED",
        "Access denied to gateway",
        AccessDeniedToGatewayError,
    ),
    (
        "RESOURCE_ACCESS_DENIED",
        "cannot be accessed through this application",
        ApplicationNotAllowedError,
    ),
    ("UNSUPPORTED_OPERATION", "No such command", InvalidCommandError),
    (
        "UNSPECIFIED_ERROR",
        "Invalid event listener id",
        InvalidEventListenerIdError,
    ),
    (
        "UNSPECIFIED_ERROR",
        "No registered event listener",
        NoRegisteredEventListenerError,
    ),
    ("UNSPECIFIED_ERROR", "Unknown object", UnknownObjectError),
]

# Message-only fallback patterns for responses where the errorCode alone is
# not enough or may vary across API versions.
_MESSAGE_FALLBACK_MAP: list[tuple[str, type[BaseOverkizError]]] = [
    ("Too many executions", TooManyExecutionsError),
    (
        "Cannot use JSESSIONID and bearer token",
        SessionAndBearerInSameRequestError,
    ),
    ("Too many attempts with an invalid token", TooManyAttemptsBannedError),
    ("Invalid token", InvalidTokenError),
    ("Not such token with UUID", NoSuchTokenError),
    ("Unknown user", UnknownUserError),
    ("No such command", InvalidCommandError),
    ("No registered event listener", NoRegisteredEventListenerError),
    ("Unknown object", UnknownObjectError),
    ("Access denied to gateway", AccessDeniedToGatewayError),
]

# Fallback when errorCode is recognized but no message pattern matched.
_ERROR_CODE_FALLBACK_MAP: dict[str, type[BaseOverkizError]] = {
    "AUTHENTICATION_ERROR": BadCredentialsError,
    "RESOURCE_ACCESS_DENIED": ResourceAccessDeniedError,
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
            raise MaintenanceError("Server is down for maintenance") from error

        if response.status == 503:  # noqa: PLR2004
            raise ServiceUnavailableError(result) from error

        raise OverkizError(
            f"Unknown error while requesting {response.url}. {response.status} - {result}"
        ) from error

    error_code = result.get("errorCode", "")

    if error_code:
        # Error messages between cloud and local servers differ slightly in quoting and punctuation.
        # Normalise so substring matching works across both variants.
        message = message.strip('".') if (message := result.get("error")) else ""

        # 1. Primary dispatch: match on errorCode (+ optional message substring)
        for code, pattern, error_class in _ERROR_CODE_MESSAGE_MAP:
            if error_code == code and (pattern is None or pattern in message):
                raise error_class(message)

        # 2. Message-only fallback for patterns that may appear under varying errorCodes
        for pattern, error_class in _MESSAGE_FALLBACK_MAP:
            if pattern in message:
                raise error_class(message)

        # 3. errorCode category fallback (known code, unknown message)
        if error_code in _ERROR_CODE_FALLBACK_MAP:
            raise _ERROR_CODE_FALLBACK_MAP[error_code](message or str(result))

    # Undefined Overkiz error
    raise OverkizError(result)
