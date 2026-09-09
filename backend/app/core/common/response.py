"""
AegisAI Standardized API Response Envelope.

Every API endpoint returns an ApiResponse[T] wrapper to guarantee
consistent response contracts across all modules and future microservices.

Schema:
    {
        "success": true,
        "status_code": 200,
        "message": "Request completed successfully.",
        "data": { ... },
        "error": null,
        "timestamp": "2026-08-22T17:00:00+00:00"
    }
"""

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """
    Standardized REST API response wrapper for all AegisAI endpoints.
    Ensures consistent API contracts across all modules and microservices.

    Generic parameter T represents the shape of the `data` payload.
    Use ApiResponse[None] for endpoints that return no data body.
    """

    success: bool = True
    status_code: int = 200
    message: str = "Request completed successfully."
    data: T | None = None
    error: dict[str, Any] | None = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @classmethod
    def ok(
        cls,
        data: T,
        message: str = "Request completed successfully.",
        status_code: int = 200,
    ) -> "ApiResponse[T]":
        """Construct a successful response envelope."""
        return cls(
            success=True,
            status_code=status_code,
            message=message,
            data=data,
            error=None,
        )

    @classmethod
    def created(cls, data: T, message: str = "Resource created successfully.") -> "ApiResponse[T]":
        """Construct a 201 Created response envelope."""
        return cls.ok(data=data, message=message, status_code=201)

    @classmethod
    def fail(
        cls,
        message: str,
        status_code: int = 400,
        error_details: dict[str, Any] | None = None,
    ) -> "ApiResponse[None]":
        """Construct an error response envelope."""
        return cls(
            success=False,
            status_code=status_code,
            message=message,
            data=None,
            error=error_details or {"detail": message},
        )

    @classmethod
    def paginated(
        cls,
        data: list[Any],
        total: int,
        page: int,
        page_size: int,
        message: str = "Data retrieved successfully.",
    ) -> "ApiResponse[dict[str, Any]]":
        """Construct a paginated list response."""
        return cls(
            success=True,
            status_code=200,
            message=message,
            data={
                "items": data,
                "total": total,
                "page": page,
                "page_size": page_size,
                "pages": max(1, (total + page_size - 1) // page_size),
            },
            error=None,
        )
