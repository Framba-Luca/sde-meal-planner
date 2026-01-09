class AuthServiceError(Exception):
    """Base Class for Authentication Service exceptions"""
    pass

class ServiceUnavailable(AuthServiceError):
    """Called when an external service (DB, Google) doesn't respond back"""
    pass

class UserAlreadyExists(AuthServiceError):
    """Exception raised when trying to register an already existing user"""
    pass

class InvalidCredentials(AuthServiceError):
    """Exception raised when credentials are invalid"""
    pass