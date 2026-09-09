"""
AegisAI AI Module — FastAPI Dependencies.
"""

from functools import lru_cache

from app.modules.ai.service import AIDecisionService


@lru_cache
def get_ai_service() -> AIDecisionService:
    """Provides a singleton instance of the AI decision service."""
    return AIDecisionService()
