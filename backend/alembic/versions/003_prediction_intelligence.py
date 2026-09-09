"""
AegisAI Alembic Migration 003 â€” Prediction Intelligence Schema.

Revision ID: 003_prediction_intelligence
Revises: 002_ai_decision_engine
Create Date: 2026-09-03
"""

import sqlalchemy as sa

from alembic import op

revision = "003_prediction_intelligence"
down_revision = "002_ai_decision_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create prediction_records table."""
    op.create_table(
        "prediction_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("prediction_type", sa.String(length=64), nullable=False),
        sa.Column("simulation_id", sa.String(length=128), nullable=True),
        sa.Column("incident_id", sa.Integer(), nullable=True),
        sa.Column("model_name", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=32), nullable=False),
        sa.Column("forecast_horizon_minutes", sa.Integer(), nullable=False),
        sa.Column("predicted_value", sa.JSON(), nullable=False),
        sa.Column("actual_value", sa.JSON(), nullable=True),
        sa.Column("error_rate", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("prediction_source", sa.String(length=32), nullable=False),
        sa.Column("input_snapshot", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["incidents.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_prediction_records_id"),
        "prediction_records",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_prediction_records_prediction_type"),
        "prediction_records",
        ["prediction_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_prediction_records_simulation_id"),
        "prediction_records",
        ["simulation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_prediction_records_incident_id"),
        "prediction_records",
        ["incident_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_prediction_records_created_at"),
        "prediction_records",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop prediction_records table."""
    op.drop_index(
        op.f("ix_prediction_records_created_at"),
        table_name="prediction_records",
    )
    op.drop_index(
        op.f("ix_prediction_records_incident_id"),
        table_name="prediction_records",
    )
    op.drop_index(
        op.f("ix_prediction_records_simulation_id"),
        table_name="prediction_records",
    )
    op.drop_index(
        op.f("ix_prediction_records_prediction_type"),
        table_name="prediction_records",
    )
    op.drop_index(
        op.f("ix_prediction_records_id"),
        table_name="prediction_records",
    )
    op.drop_table("prediction_records")
