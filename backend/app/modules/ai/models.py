"""
AegisAI AI Module — ORM Models.

Defines persistence for AI Decision Intelligence:
- AIDecision: Core emergency response recommendation entity.
- AIDecisionCandidate: Evaluated alternatives and rejected candidates.
- AIDecisionFeedback: Human-in-the-loop feedback and outcome tracking for ML/RL.
- AIDecisionEvent: Audit trail of lifecycle transitions and executions.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.base import Base, TimestampMixin
from app.modules.ai.enums import DecisionPriority, DecisionStatus, DecisionType, FeedbackType

# Build check constraints
_DECISION_TYPES = "(" + ",".join(f"'{t.value}'" for t in DecisionType) + ")"
_DECISION_STATUSES = "(" + ",".join(f"'{s.value}'" for s in DecisionStatus) + ")"
_PRIORITIES = "(" + ",".join(f"'{p.value}'" for p in DecisionPriority) + ")"
_FEEDBACK_TYPES = "(" + ",".join(f"'{f.value}'" for f in FeedbackType) + ")"


class AIDecision(Base, TimestampMixin):
    """
    AI-generated decision entity representing an optimized emergency management action.
    """

    __tablename__ = "ai_decisions"

    __table_args__ = (
        CheckConstraint(f"decision_type IN {_DECISION_TYPES}", name="ck_ai_decisions_type"),
        CheckConstraint(f"status IN {_DECISION_STATUSES}", name="ck_ai_decisions_status"),
        CheckConstraint(f"priority IN {_PRIORITIES}", name="ck_ai_decisions_priority"),
        CheckConstraint("score >= 0.0 AND score <= 1.0", name="ck_ai_decisions_score"),
        CheckConstraint(
            "confidence >= 0.0 AND confidence <= 1.0", name="ck_ai_decisions_confidence"
        ),
        Index("ix_ai_decisions_status", "status"),
        Index("ix_ai_decisions_type", "decision_type"),
        Index("ix_ai_decisions_incident", "incident_id"),
        Index("ix_ai_decisions_uuid", "decision_uuid", unique=True),
        Index("ix_ai_decisions_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)

    decision_uuid: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        default=lambda: str(uuid.uuid4()),
        unique=True,
    )

    simulation_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    incident_id: Mapped[int | None] = mapped_column(
        ForeignKey("incidents.id", ondelete="SET NULL"),
        nullable=True,
    )

    decision_type: Mapped[str] = mapped_column(String(50), nullable=False)

    action: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    resource_id: Mapped[int | None] = mapped_column(
        ForeignKey("rescue_teams.id", ondelete="SET NULL"),
        nullable=True,
    )

    destination_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DecisionPriority.MEDIUM.value,
        server_default=DecisionPriority.MEDIUM.value,
    )

    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    reasoning: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    constraints: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    expected_impact: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    alternatives: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=DecisionStatus.REVIEW_REQUIRED.value,
        server_default=DecisionStatus.REVIEW_REQUIRED.value,
    )

    policy_name: Mapped[str] = mapped_column(String(100), nullable=False, default="OPTIMIZED")

    policy_version: Mapped[str] = mapped_column(String(30), nullable=False, default="1.0.0")

    model_name: Mapped[str] = mapped_column(String(100), nullable=False, default="llama3.2:3b")

    model_version: Mapped[str] = mapped_column(String(30), nullable=False, default="1.0.0")

    input_state_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    approved_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    modification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    incident = relationship("Incident", foreign_keys=[incident_id], lazy="joined")
    resource = relationship("RescueTeam", foreign_keys=[resource_id], lazy="joined")
    approver = relationship("User", foreign_keys=[approved_by], lazy="joined")
    candidates = relationship(
        "AIDecisionCandidate", back_populates="decision", cascade="all, delete-orphan"
    )
    feedback_items = relationship(
        "AIDecisionFeedback", back_populates="decision", cascade="all, delete-orphan"
    )
    events = relationship(
        "AIDecisionEvent", back_populates="decision", cascade="all, delete-orphan"
    )


class AIDecisionCandidate(Base, TimestampMixin):
    """
    Evaluated alternative candidate generated during decision optimization.
    """

    __tablename__ = "ai_decision_candidates"

    __table_args__ = (
        Index("ix_ai_candidates_decision", "decision_id"),
        Index("ix_ai_candidates_resource", "resource_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)

    decision_id: Mapped[int] = mapped_column(
        ForeignKey("ai_decisions.id", ondelete="CASCADE"),
        nullable=False,
    )

    resource_id: Mapped[int | None] = mapped_column(
        ForeignKey("rescue_teams.id", ondelete="SET NULL"),
        nullable=True,
    )

    hospital_id: Mapped[int | None] = mapped_column(
        ForeignKey("hospitals.id", ondelete="SET NULL"),
        nullable=True,
    )

    eta_minutes: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    distance_km: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    is_selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Relationships
    decision = relationship("AIDecision", back_populates="candidates")
    resource = relationship("RescueTeam", foreign_keys=[resource_id], lazy="joined")
    hospital = relationship("Hospital", foreign_keys=[hospital_id], lazy="joined")


class AIDecisionFeedback(Base, TimestampMixin):
    """
    Human commander feedback and recorded actual outcomes for AI decisions.
    """

    __tablename__ = "ai_decision_feedback"

    __table_args__ = (
        CheckConstraint(f"feedback_type IN {_FEEDBACK_TYPES}", name="ck_ai_feedback_type"),
        Index("ix_ai_feedback_decision", "decision_id"),
        Index("ix_ai_feedback_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)

    decision_id: Mapped[int] = mapped_column(
        ForeignKey("ai_decisions.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    feedback_type: Mapped[str] = mapped_column(String(30), nullable=False)

    actual_outcome: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    decision = relationship("AIDecision", back_populates="feedback_items")
    user = relationship("User", foreign_keys=[user_id], lazy="joined")


class AIDecisionEvent(Base, TimestampMixin):
    """
    Audit log of lifecycle events for an AI decision.
    """

    __tablename__ = "ai_decision_events"

    __table_args__ = (
        Index("ix_ai_events_decision", "decision_id"),
        Index("ix_ai_events_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)

    decision_id: Mapped[int] = mapped_column(
        ForeignKey("ai_decisions.id", ondelete="CASCADE"),
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(String(50), nullable=False)

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Relationships
    decision = relationship("AIDecision", back_populates="events")
    user = relationship("User", foreign_keys=[user_id], lazy="joined")
