"""AegisAI common utilities package."""

from app.core.common.exceptions import (
    AegisException,
    ConflictException,
    EntityNotFoundException,
    ForbiddenException,
    RateLimitException,
    ServiceUnavailableException,
    SimulationException,
    UnauthorizedException,
    ValidationException,
)
from app.core.common.logging import logger, setup_logging
from app.core.common.response import ApiResponse

__all__ = [
    "AegisException",
    "ConflictException",
    "EntityNotFoundException",
    "ForbiddenException",
    "RateLimitException",
    "ServiceUnavailableException",
    "SimulationException",
    "UnauthorizedException",
    "ValidationException",
    "logger",
    "setup_logging",
    "ApiResponse",
]
