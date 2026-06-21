"""Custom exceptions for AyushBot Cloud API."""

import uuid
from datetime import datetime


class APIException(Exception):
    """Base API exception with structured error response."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
    ):
        """Initialize API exception.

        Args:
            message: Human-readable error message
            status_code: HTTP status code
            error_code: Machine-readable error code
        """
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.request_id = str(uuid.uuid4())
        self.timestamp = datetime.utcnow().isoformat()
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Convert exception to error response dictionary."""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "status_code": self.status_code,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
        }


class NotFoundError(APIException):
    """Resource not found (404)."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            message,
            status_code=404,
            error_code="NOT_FOUND",
        )


class UnauthorizedError(APIException):
    """Unauthorized access (401)."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            message,
            status_code=401,
            error_code="UNAUTHORIZED",
        )


class ForbiddenError(APIException):
    """Forbidden access (403)."""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(
            message,
            status_code=403,
            error_code="FORBIDDEN",
        )


class BadRequestError(APIException):
    """Bad request (400)."""

    def __init__(self, message: str = "Bad request"):
        super().__init__(
            message,
            status_code=400,
            error_code="BAD_REQUEST",
        )


class ConflictError(APIException):
    """Resource conflict (409)."""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(
            message,
            status_code=409,
            error_code="CONFLICT",
        )


class RateLimitError(APIException):
    """Rate limit exceeded (429)."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message,
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
        )


class InternalServerError(APIException):
    """Internal server error (500)."""

    def __init__(self, message: str = "Internal server error"):
        super().__init__(
            message,
            status_code=500,
            error_code="INTERNAL_SERVER_ERROR",
        )
