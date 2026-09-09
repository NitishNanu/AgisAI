"""
AegisAI Database Migration â€” AI Decision Engine Tables.

Revision ID: 002_ai_decision_engine
Revises: 001_initial_schema
Create Date: 2026-09-03
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "002_ai_decision_engine"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. ai_decisions table
    op.create_table(
        "ai_decisions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("decision_uuid", sa.String(length=36), nullable=False),
        sa.Column("simulation_id", sa.String(length=100), nullable=True),
        sa.Column("incident_id", sa.Integer(), nullable=True),
        sa.Column("decision_type", sa.String(length=50), nullable=False),
        sa.Column("action", sa.JSON(), nullable=False),
        sa.Column("resource_id", sa.Integer(), nullable=True),
        sa.Column("destination_id", sa.Integer(), nullable=True),
        sa.Column("priority", sa.String(length=20), server_default="MEDIUM", nullable=False),
        sa.Column("score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("reasoning", sa.JSON(), nullable=False),
        sa.Column("constraints", sa.JSON(), nullable=False),
        sa.Column("expected_impact", sa.JSON(), nullable=False),
        sa.Column("alternatives", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="REVIEW_REQUIRED", nullable=False),
        sa.Column("policy_name", sa.String(length=100), server_default="OPTIMIZED", nullable=False),
        sa.Column("policy_version", sa.String(length=30), server_default="1.0.0", nullable=False),
        sa.Column(
            "model_name", sa.String(length=100), server_default="llama3.2:3b", nullable=False
        ),
        sa.Column("model_version", sa.String(length=30), server_default="1.0.0", nullable=False),
        sa.Column("input_state_snapshot", sa.JSON(), nullable=True),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("modification_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["resource_id"], ["rescue_teams.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("decision_uuid", name="uq_ai_decisions_uuid"),
    )
    op.create_index("ix_ai_decisions_id", "ai_decisions", ["id"], unique=False)
    op.create_index("ix_ai_decisions_uuid", "ai_decisions", ["decision_uuid"], unique=True)
    op.create_index("ix_ai_decisions_status", "ai_decisions", ["status"], unique=False)
    op.create_index("ix_ai_decisions_type", "ai_decisions", ["decision_type"], unique=False)
    op.create_index("ix_ai_decisions_incident", "ai_decisions", ["incident_id"], unique=False)
    op.create_index("ix_ai_decisions_simulation", "ai_decisions", ["simulation_id"], unique=False)

    # 2. ai_decision_candidates table
    op.create_table(
        "ai_decision_candidates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("decision_id", sa.Integer(), nullable=False),
        sa.Column("resource_id", sa.Integer(), nullable=True),
        sa.Column("hospital_id", sa.Integer(), nullable=True),
        sa.Column("eta_minutes", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("distance_km", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("is_selected", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("rejection_reason", sa.String(length=500), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["decision_id"], ["ai_decisions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitals.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["resource_id"], ["rescue_teams.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_candidates_decision", "ai_decision_candidates", ["decision_id"], unique=False
    )
    op.create_index(
        "ix_ai_candidates_resource", "ai_decision_candidates", ["resource_id"], unique=False
    )

    # 3. ai_decision_feedback table
    op.create_table(
        "ai_decision_feedback",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("decision_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("feedback_type", sa.String(length=30), nullable=False),
        sa.Column("actual_outcome", sa.JSON(), nullable=False),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["decision_id"], ["ai_decisions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_feedback_decision", "ai_decision_feedback", ["decision_id"], unique=False
    )
    op.create_index("ix_ai_feedback_user", "ai_decision_feedback", ["user_id"], unique=False)

    # 4. ai_decision_events table
    op.create_table(
        "ai_decision_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("decision_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["decision_id"], ["ai_decisions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_events_decision", "ai_decision_events", ["decision_id"], unique=False)
    op.create_index("ix_ai_events_created", "ai_decision_events", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_table("ai_decision_events")
    op.drop_table("ai_decision_feedback")
    op.drop_table("ai_decision_candidates")
    op.drop_table("ai_decisions")
