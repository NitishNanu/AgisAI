"""
AegisAI AI Module — Real-Time Event Publisher.

Publishes AI Decision lifecycle events over WebSockets and RabbitMQ.
"""

from typing import Any

import structlog

from app.core.websocket.manager import ws_manager

logger = structlog.get_logger("aegis_ai.modules.ai.events")


class AIDecisionEventPublisher:
    """Helper for publishing decision events across channels."""

    @staticmethod
    async def publish_decision_generated(decision_data: dict[str, Any]) -> None:
        """Broadcast when a new decision recommendation is generated."""
        logger.info("event_ai_decision_generated", decision_id=decision_data.get("id"))
        await ws_manager.broadcast_to_channel(
            channel="simulation",
            event_type="AI_DECISION_GENERATED",
            data=decision_data,
        )
        await ws_manager.broadcast_to_channel(
            channel="missions",
            event_type="AI_DECISION_GENERATED",
            data=decision_data,
        )

    @staticmethod
    async def publish_decision_approved(decision_data: dict[str, Any]) -> None:
        """Broadcast when a commander approves a decision."""
        logger.info("event_ai_decision_approved", decision_id=decision_data.get("id"))
        await ws_manager.broadcast_to_channel(
            channel="missions",
            event_type="AI_DECISION_APPROVED",
            data=decision_data,
        )

    @staticmethod
    async def publish_decision_rejected(decision_data: dict[str, Any]) -> None:
        """Broadcast when a commander rejects a decision."""
        logger.info("event_ai_decision_rejected", decision_id=decision_data.get("id"))
        await ws_manager.broadcast_to_channel(
            channel="missions",
            event_type="AI_DECISION_REJECTED",
            data=decision_data,
        )

    @staticmethod
    async def publish_decision_executed(decision_data: dict[str, Any]) -> None:
        """Broadcast when a decision action is successfully executed into a live mission."""
        logger.info("event_ai_decision_executed", decision_id=decision_data.get("id"))
        await ws_manager.broadcast_to_channel(
            channel="missions",
            event_type="AI_DECISION_EXECUTED",
            data=decision_data,
        )

    @staticmethod
    async def publish_decision_failed(decision_id: int, reason: str) -> None:
        """Broadcast when decision execution or solver encounters a critical error."""
        logger.warning("event_ai_decision_failed", decision_id=decision_id, reason=reason)
        await ws_manager.broadcast_to_channel(
            channel="missions",
            event_type="AI_DECISION_FAILED",
            data={"decision_id": decision_id, "error": reason},
        )
