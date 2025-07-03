"""
Custom exceptions for CSRF protection plugin
"""


class CSRFError(Exception):
    """Base exception for CSRF-related errors"""

    pass


class CSRFConfigurationError(CSRFError):
    """Raised when there's a configuration error"""

    pass


class CSRFValidationError(CSRFError):
    """Raised when CSRF token validation fails"""

    pass


class CSRFTokenError(CSRFError):
    """Raised when there's an issue with CSRF token generation or parsing"""

    pass


class CSRFModeError(CSRFError):
    """Raised when there's an invalid CSRF mode"""

    pass
