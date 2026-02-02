"""Custom exceptions for Namaskah application."""


class NamaskahException(Exception):

    """Base exception for Namaskah application."""


class AuthenticationError(NamaskahException):

    """Raised when authentication fails."""


class AuthorizationError(NamaskahException):

    """Raised when user is not authorized to perform action."""


class ValidationError(NamaskahException):

    """Raised when validation fails."""


class ExternalServiceError(NamaskahException):

    """Raised when external service fails."""


class PaymentError(NamaskahException):

    """Raised when payment processing fails."""


class InsufficientCreditsError(NamaskahException):

    """Raised when user has insufficient credits."""