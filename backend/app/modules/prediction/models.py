"""
AegisAI Prediction Module — SQLAlchemy Models.

Defines persistence for historical predictions, forecasts, and evaluated outcomes.
Compatible with Python 3.10 and SQLAlchemy 2.0.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.base import Base


class PredictionRecord(Base):
    """
    Persisted record of an AI / Simulation forecast.

    Stores input snapshots, predicted values at specific time horizons,
    confidence ratings, and observed actual outcomes for MAE/MAPE calculation.
    """

    __tablename__ = "prediction_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prediction_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # CASUALTY_SURGE | HOSPITAL_LOAD | RESOURCE_DEMAND | SPREAD_RADIUS | DISASTER_RISK
    simulation_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    incident_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    model_name: Mapped[str] = mapped_column(
        String(64), nullable=False, default="AegisAI-PredictiveEngine-v1"
    )
    model_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.2.0")
    forecast_horizon_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=15
    )  # 5, 15, 30, 60
    predicted_value: Mapped[dict] = mapped_column(JSON, nullable=False)
    actual_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    prediction_source: Mapped[str] = mapped_column(
        String(32), nullable=False, default="SIMULATION"
    )  # SIMULATION | ML_MODEL | AI_MODEL | HISTORICAL | FALLBACK
    input_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    incident = relationship("Incident", foreign_keys=[incident_id], lazy="select")
