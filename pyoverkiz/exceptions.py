"""Errors defined for Overkiz API and its integrations."""


class BaseOverkizError(Exception):
    """Base error for Overkiz errors."""


class OverkizError(BaseOverkizError):
    """Raised when an undefined error occurs while communicating with the Overkiz API."""


class BadCredentialsError(BaseOverkizError):
    """Raised when invalid credentials are provided."""


class InvalidCommandError(BaseOverkizError):
    """Raised when an invalid command is provided."""


class DuplicateActionOnDeviceError(BaseOverkizError):
    """Raised when another action already exists for the same device."""


class ActionGroupSetupNotFoundError(BaseOverkizError):
    """Raised when an action group setup cannot be determined for a gateway."""


class NoSuchResourceError(BaseOverkizError):
    """Raised when an invalid API call is made."""


class ResourceAccessDeniedError(BaseOverkizError):
    """Raised when the API returns a RESOURCE_ACCESS_DENIED error."""


class NotAuthenticatedError(ResourceAccessDeniedError):
    """Raised when the user is not authenticated."""


class TooManyExecutionsError(BaseOverkizError):
    """Raised when too many executions are requested."""


class ExecutionQueueFullError(BaseOverkizError):
    """Raised when the execution queue is full."""


class TooManyRequestsError(BaseOverkizError):
    """Raised when too many requests are made."""


class TooManyConcurrentRequestsError(BaseOverkizError):
    """Raised when too many concurrent requests are made."""


class ServiceUnavailableError(BaseOverkizError):
    """Raised when the service is unavailable."""


class MaintenanceError(ServiceUnavailableError):
    """Raised when the service is under maintenance."""


class MissingAPIKeyError(BaseOverkizError):
    """Raised when the API key is missing."""


class MissingAuthorizationTokenError(ResourceAccessDeniedError):
    """Raised when the authorization token is missing."""


class InvalidEventListenerIdError(BaseOverkizError):
    """Raised when an invalid event listener ID is provided."""


class NoRegisteredEventListenerError(BaseOverkizError):
    """Raised when no event listener is registered."""


class SessionAndBearerInSameRequestError(BaseOverkizError):
    """Raised when both session and bearer are provided in the same request."""


class TooManyAttemptsBannedError(BaseOverkizError):
    """Raised when too many attempts are made and the user is (temporarily) banned."""


class InvalidTokenError(BaseOverkizError):
    """Raised when an invalid token is provided."""


class NoSuchTokenError(BaseOverkizError):
    """Raised when an invalid token is provided."""


class UnknownUserError(BaseOverkizError):
    """Raised when an unknown user is provided."""


class UnknownObjectError(BaseOverkizError):
    """Raised when an unknown object is provided."""


class AccessDeniedToGatewayError(ResourceAccessDeniedError):
    """Raised when access is denied to the gateway.

    This often happens when the user is not the owner of the gateway.
    """


class ApplicationNotAllowedError(ResourceAccessDeniedError):
    """Raised when the setup cannot be accessed through the application."""


# Nexity
class NexityBadCredentialsError(BadCredentialsError):
    """Raised when invalid credentials are provided to Nexity authentication API."""


class NexityServiceError(BaseOverkizError):
    """Raised when an error occurs while communicating with the Nexity API."""


# CozyTouch
class CozyTouchBadCredentialsError(BadCredentialsError):
    """Raised when invalid credentials are provided to CozyTouch authentication API."""


class CozyTouchServiceError(BaseOverkizError):
    """Raised when an error occurs while communicating with the CozyTouch API."""


# Somfy
class SomfyBadCredentialsError(BadCredentialsError):
    """Raised when invalid credentials are provided to Somfy authentication API."""


class SomfyServiceError(BaseOverkizError):
    """Raised when an error occurs while communicating with the Somfy API."""
