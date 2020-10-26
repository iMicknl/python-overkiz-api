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
