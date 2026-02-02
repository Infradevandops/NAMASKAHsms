"""Custom exception classes for Namaskah SMS Platform."""


class NamaskahException(Exception):

    """Base exception for all Namaskah errors."""


class TextVerifiedAPIError(NamaskahException):

    """TextVerified API communication error."""


class InsufficientCreditsError(NamaskahException):

    """User has insufficient credits for operation."""


class InvalidInputError(NamaskahException):

    """Invalid input provided."""


class ProviderError(NamaskahException):

    """SMS provider error."""


class VerificationError(NamaskahException):

    """Verification operation error."""


class RentalError(NamaskahException):

    """Rental operation error."""


class PaymentError(NamaskahException):

    """Payment processing error."""


class AuthenticationError(NamaskahException):

    """Authentication error."""


class AuthorizationError(NamaskahException):

    """Authorization error."""


class ResourceNotFoundError(NamaskahException):

    """Resource not found."""


class DuplicateResourceError(NamaskahException):

    """Resource already exists."""


class RateLimitError(NamaskahException):

    """Rate limit exceeded."""


class ServiceUnavailableError(NamaskahException):

    """Service temporarily unavailable."""