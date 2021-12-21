class BadCredentialsException(Exception):
    pass


class InvalidCommandException(Exception):
    pass


class NotAuthenticatedException(Exception):
    pass


class TooManyExecutionsException(Exception):
    pass


class TooManyRequestsException(Exception):
    pass


class MaintenanceException(Exception):
    pass


class InvalidEventListenerIdException(Exception):
    pass


class NoRegisteredEventListenerException(Exception):
    pass


# Nexity
class NexityBadCredentialsException(BadCredentialsException):
    pass


class NexityServiceException(Exception):
    pass


# CozyTouch
class CozyTouchBadCredentialsException(BadCredentialsException):
    pass


class CozyTouchServiceException(Exception):
    pass
