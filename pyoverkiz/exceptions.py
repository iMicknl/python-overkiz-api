class BaseOverkizException(Exception):
    pass


class OverkizException(BaseOverkizException):
    pass


class BadCredentialsException(BaseOverkizException):
    pass


class InvalidCommandException(BaseOverkizException):
    pass


class NotAuthenticatedException(BaseOverkizException):
    pass


class TooManyExecutionsException(BaseOverkizException):
    pass


class ExecutionQueueFullException(BaseOverkizException):
    pass


class TooManyRequestsException(BaseOverkizException):
    pass


class TooManyConcurrentRequestsException(BaseOverkizException):
    pass


class ServiceUnavailableException(BaseOverkizException):
    pass


class MaintenanceException(ServiceUnavailableException):
    pass


class MissingAuthorizationTokenException(BaseOverkizException):
    pass


class InvalidEventListenerIdException(BaseOverkizException):
    pass


class NoRegisteredEventListenerException(BaseOverkizException):
    pass


class SessionAndBearerInSameRequestException(BaseOverkizException):
    pass


class TooManyAttemptsBannedException(BaseOverkizException):
    pass


class InvalidTokenException(BaseOverkizException):
    pass


class NotSuchTokenException(BaseOverkizException):
    pass


class UnknownUserException(BaseOverkizException):
    pass


class UnknownObjectException(BaseOverkizException):
    pass


class AccessDeniedToGatewayException(BaseOverkizException):
    pass


# Nexity
class NexityBadCredentialsException(BadCredentialsException):
    pass


class NexityServiceException(BaseOverkizException):
    pass


# CozyTouch
class CozyTouchBadCredentialsException(BadCredentialsException):
    pass


class CozyTouchServiceException(BaseOverkizException):
    pass


# Somfy
class SomfyBadCredentialsException(BadCredentialsException):
    pass


class SomfyServiceException(BaseOverkizException):
    pass
