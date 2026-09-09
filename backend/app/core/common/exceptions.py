"""
AegisAI Domain Exception Hierarchy.

All custom exceptions extend AegisException, which carries a standardized
HTTP status code and optional detail dict. The ErrorHandlerMiddleware
intercepts these at the boundary and serializes them into ApiResponse format.

Exception hierarchy:
    AegisException
    ├── EntityNotFoundException     (404)
    ├── UnauthorizedException       (401)
    ├── ForbiddenException          (403)
    ├── ConflictException           (409)
    ├── ValidationException         (422)
    ├── RateLimitException          (429)
    ├── ServiceUnavailableException (503)
    └── SimulationException         (500)
"""

from typing import Any

from fastapi import status


class AegisException(Exception):  # noqa: N818
    """
    Base domain exception for the AegisAI platform.
    All application-level errors must derive from this class.
    """

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
        error_code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details: dict[str, Any] = details or {}
        if error_code:
            self.details["error_code"] = error_code
        self.error_code = error_code


# Backward compatibility alias
AppException = AegisException


class EntityNotFoundException(AegisException):
    """Raised when a requested domain entity is not found in the persistence layer."""

    def __init__(self, entity_name: str, entity_id: Any) -> None:
        super().__init__(
            message=f"{entity_name} with identifier '{entity_id}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"entity_name": entity_name, "entity_id": str(entity_id)},
        )


class UnauthorizedException(AegisException):
    """Raised when authentication credentials are missing or invalid."""

    def __init__(self, message: str = "Could not validate authorization credentials.") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details={"hint": "Provide a valid Bearer token in the Authorization header."},
        )


class ForbiddenException(AegisException):
    """Raised when a user lacks required RBAC permissions for the requested action."""

    def __init__(self, message: str = "Access forbidden: insufficient role permissions.") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ConflictException(AegisException):
    """Raised when a resource state conflict occurs (e.g., duplicate email, double-dispatch)."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details or {},
        )


class ValidationException(AegisException):
    """Raised when business-level validation rules are violated (beyond Pydantic schema)."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details or {},
        )


class RateLimitException(AegisException):
    """Raised when a client exceeds the configured request rate limit."""

    def __init__(
        self, message: str = "Rate limit exceeded. Please slow down your requests."
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"hint": "Retry after the rate limit window resets."},
        )


class ServiceUnavailableException(AegisException):
    """Raised when a downstream service (Ollama, OSRM, RabbitMQ) is unreachable."""

    def __init__(self, service_name: str, reason: str = "") -> None:
        reason_msg = f": {reason}" if reason else "."
        super().__init__(
            message=f"Service '{service_name}' is currently unavailable{reason_msg}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"service": service_name},
        )


class SimulationException(AegisException):
    """Raised during Digital Twin simulation execution errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details or {},
        )
