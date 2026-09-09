"""
AegisAI AI Module — Repository Layer.

Handles database persistence for AI decisions, candidates, events, and feedback.
"""

from collections.abc import Sequence

import structlog
from sqlalchemy.orm import Session

from app.modules.ai.enums import DecisionStatus
from app.modules.ai.models import (
    AIDecision,
    AIDecisionEvent,
    AIDecisionFeedback,
)

logger = structlog.get_logger("aegis_ai.ai.repository")


class AIDecisionRepository:
    """Persistence operations for AI decisions."""

    @staticmethod
    def create_decision(db: Session, decision_dict: dict) -> AIDecision:
        """Persist a new AI decision entity."""
        decision = AIDecision(
            decision_type=decision_dict["decision_type"],
            action=decision_dict["action"],
            incident_id=decision_dict.get("incident_id"),
            resource_id=decision_dict.get("resource_id"),
            destination_id=decision_dict.get("destination_id"),
            priority=decision_dict.get("priority", "MEDIUM"),
            score=decision_dict.get("score", 0.0),
            confidence=decision_dict.get("confidence", 0.0),
            reasoning=decision_dict.get("reasoning", []),
            constraints=decision_dict.get("constraints", {}),
            expected_impact=decision_dict.get("expected_impact", {}),
            alternatives=decision_dict.get("alternatives", []),
            status=decision_dict.get("status", DecisionStatus.REVIEW_REQUIRED.value),
            policy_name=decision_dict.get("policy_name", "OPTIMIZED"),
            policy_version=decision_dict.get("policy_version", "1.0.0"),
            model_name=decision_dict.get("model_name", "llama3.2:3b"),
            model_version=decision_dict.get("model_version", "1.0.0"),
            simulation_id=decision_dict.get("simulation_id"),
            input_state_snapshot=decision_dict.get("input_state_snapshot"),
        )
        db.add(decision)
        db.commit()
        db.refresh(decision)
        return decision

    @staticmethod
    def get_by_id(db: Session, decision_id: int) -> AIDecision | None:
        """Fetch decision by integer primary key."""
        return db.query(AIDecision).filter(AIDecision.id == decision_id).first()

    @staticmethod
    def get_by_uuid(db: Session, decision_uuid: str) -> AIDecision | None:
        """Fetch decision by UUID string."""
        return db.query(AIDecision).filter(AIDecision.decision_uuid == decision_uuid).first()

    @staticmethod
    def get_by_id_or_uuid(db: Session, identifier: str | int) -> AIDecision | None:
        """Fetch decision by ID if numeric, otherwise by UUID."""
        if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
            return AIDecisionRepository.get_by_id(db, int(identifier))
        return AIDecisionRepository.get_by_uuid(db, identifier)

    @staticmethod
    def list_decisions(
        db: Session,
        status: str | None = None,
        decision_type: str | None = None,
        incident_id: int | None = None,
        simulation_id: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[AIDecision], int]:
        """List decisions with optional filters and pagination."""
        query = db.query(AIDecision)
        if status:
            query = query.filter(AIDecision.status == status.upper())
        if decision_type:
            query = query.filter(AIDecision.decision_type == decision_type.upper())
        if incident_id:
            query = query.filter(AIDecision.incident_id == incident_id)
        if simulation_id:
            query = query.filter(AIDecision.simulation_id == simulation_id)

        total = query.count()
        items = query.order_by(AIDecision.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def save_event(
        db: Session,
        decision_id: int,
        event_type: str,
        user_id: int | None = None,
        payload: dict | None = None,
    ) -> AIDecisionEvent:
        """Record lifecycle event audit entry."""
        event = AIDecisionEvent(
            decision_id=decision_id,
            event_type=event_type,
            user_id=user_id,
            payload=payload or {},
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def save_feedback(
        db: Session,
        decision_id: int,
        user_id: int,
        feedback_type: str,
        actual_outcome: dict,
        comments: str | None = None,
    ) -> AIDecisionFeedback:
        """Persist commander feedback and mission outcome."""
        feedback = AIDecisionFeedback(
            decision_id=decision_id,
            user_id=user_id,
            feedback_type=feedback_type,
            actual_outcome=actual_outcome,
            comments=comments,
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return feedback
