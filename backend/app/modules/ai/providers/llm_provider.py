"""
AegisAI AI Module — LLM Provider Interface.
"""

from typing import Any, Protocol

from app.modules.ai.schemas import LLMExplanationResponse


class LLMProvider(Protocol):
    """Protocol for LLM-based narrative generation."""

    model_name: str
    model_version: str

    async def generate_briefing(
        self,
        decision_data: dict[str, Any],
    ) -> LLMExplanationResponse:
        """
        Generates a human-readable operational tactical briefing from structured facts.
        """
        ...
