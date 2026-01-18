"""Custom exceptions for Namaskah application."""


class NamaskahException(Exception):
    """Base exception for Namaskah application."""

    pass


class AuthenticationError(NamaskahException):
    """Raised when authentication fails."""

    pass


class AuthorizationError(NamaskahException):
    """Raised when user is not authorized to perform action."""

    pass


class ValidationError(NamaskahException):
    """Raised when validation fails."""

    pass


class ExternalServiceError(NamaskahException):
    """Raised when external service fails."""

    pass


class PaymentError(NamaskahException):
    """Raised when payment processing fails."""

    pass


class InsufficientCreditsError(NamaskahException):
    """Raised when user has insufficient credits."""

    pass
