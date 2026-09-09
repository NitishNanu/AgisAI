"""
AegisAI AI Module — Custom Exceptions.
"""

from app.core.common.exceptions import AppException


class DecisionNotFoundException(AppException):
    """Raised when an AI decision cannot be located."""

    def __init__(self, identifier: str | int) -> None:
        super().__init__(
            message=f"AI Decision '{identifier}' was not found.",
            status_code=404,
            error_code="AI_DECISION_NOT_FOUND",
        )


class DecisionStateTransitionException(AppException):
    """Raised when an invalid lifecycle state transition is attempted on a decision."""

    def __init__(self, current_status: str, target_status: str) -> None:
        super().__init__(
            message=f"Cannot transition AI decision from '{current_status}' to '{target_status}'.",
            status_code=400,
            error_code="INVALID_DECISION_TRANSITION",
        )


class DecisionExecutionException(AppException):
    """Raised when execution of an approved decision fails."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            message=f"Failed to execute AI decision: {reason}",
            status_code=409,
            error_code="DECISION_EXECUTION_FAILED",
        )


class OptimizationFailedException(AppException):
    """Raised when mathematical optimization fails and fallback is required."""

    def __init__(
        self, message: str = "Optimization engine could not find a feasible solution"
    ) -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_code="OPTIMIZATION_FAILED",
        )
