"""
AegisAI Decision Engine Package.

Provides mathematical optimization, multi-criteria scoring, hard constraint verification,
state aggregation, and deterministic explainability for emergency response decision intelligence.
"""

from app.modules.ai.decision_engine.engine import DecisionEngine
from app.modules.ai.decision_engine.state import StateAggregator

__all__ = ["DecisionEngine", "StateAggregator"]
