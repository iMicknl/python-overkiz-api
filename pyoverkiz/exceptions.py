class BaseOverkizException(Exception):
    """Base exception for Overkiz errors."""


class OverkizException(BaseOverkizException):
    """Raised when an undefined error occurs while communicating with the Overkiz API."""


class BadCredentialsException(BaseOverkizException):
    """Raised when invalid credentials are provided."""


class InvalidCommandException(BaseOverkizException):
    """Raised when an invalid command is provided."""


class NoSuchResourceException(BaseOverkizException):
    """Raised when an invalid API call is made."""


class NotAuthenticatedException(BaseOverkizException):
    """Raised when the user is not authenticated."""


class TooManyExecutionsException(BaseOverkizException):
    """Raised when too many executions are requested."""


class ExecutionQueueFullException(BaseOverkizException):
    """Raised when the execution queue is full."""


class TooManyRequestsException(BaseOverkizException):
    """Raised when too many requests are made."""


class TooManyConcurrentRequestsException(BaseOverkizException):
    """Raised when too many concurrent requests are made."""


class ServiceUnavailableException(BaseOverkizException):
    """Raised when the service is unavailable."""


class MaintenanceException(ServiceUnavailableException):
    """Raised when the service is under maintenance."""


class MissingAuthorizationTokenException(BaseOverkizException):
    """Raised when the authorization token is missing."""


class InvalidEventListenerIdException(BaseOverkizException):
    """Raised when an invalid event listener ID is provided."""


class NoRegisteredEventListenerException(BaseOverkizException):
    """Raised when no event listener is registered."""


class SessionAndBearerInSameRequestException(BaseOverkizException):
    """Raised when both session and bearer are provided in the same request."""


class TooManyAttemptsBannedException(BaseOverkizException):
    """Raised when too many attempts are made and the user is (temporarily) banned."""


class InvalidTokenException(BaseOverkizException):
    """Raised when an invalid token is provided."""


class NotSuchTokenException(BaseOverkizException):
    """Raised when an invalid token is provided."""


class UnknownUserException(BaseOverkizException):
    """Raised when an unknown user is provided."""


class UnknownObjectException(BaseOverkizException):
    """Raised when an unknown object is provided."""


class AccessDeniedToGatewayException(BaseOverkizException):
    """Raised when access is denied to the gateway. This often happens when the user is not the owner of the gateway."""


# Nexity
class NexityBadCredentialsException(BadCredentialsException):
    """Raised when invalid credentials are provided to Nexity authentication API."""


class NexityServiceException(BaseOverkizException):
    """Raised when an error occurs while communicating with the Nexity API."""


# CozyTouch
class CozyTouchBadCredentialsException(BadCredentialsException):
    """Raised when invalid credentials are provided to CozyTouch authentication API."""


class CozyTouchServiceException(BaseOverkizException):
    """Raised when an error occurs while communicating with the CozyTouch API."""


# Somfy
class SomfyBadCredentialsException(BadCredentialsException):
    """Raised when invalid credentials are provided to Somfy authentication API."""


class SomfyServiceException(BaseOverkizException):
    """Raised when an error occurs while communicating with the Somfy API."""
