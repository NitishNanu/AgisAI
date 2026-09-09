"""
AegisAI Analytics Module — ORM Models.

Provides persistent storage for analytics reports and system KPI snapshots.

Models:
  - AnalyticsReport: Stores a point-in-time snapshot of cross-module metrics,
    generated on-demand via the POST /analytics/reports endpoint. Used for
    historical trending and executive reporting.
  - SystemMetricSnapshot: Lightweight time-series record capturing key
    operational KPIs at each simulation tick. Powers chart endpoints.
"""

from sqlalchemy import Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.base import Base, TimestampMixin


class AnalyticsReport(Base, TimestampMixin):
    """
    Full platform analytics report snapshot.

    Generated on-demand and persisted for historical comparison.
    Each row captures the complete state of platform KPIs at the time
    of report generation.
    """

    __tablename__ = "analytics_reports"

    __table_args__ = (
        Index("ix_analytics_reports_created_at", "created_at"),
        Index("ix_analytics_reports_environment", "environment"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)

    # Report metadata
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    environment: Mapped[str] = mapped_column(String(50), nullable=False, default="production")

    # Incident KPIs
    total_incidents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active_incidents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    resolved_incidents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    critical_incidents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Resource KPIs
    total_rescue_teams: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_rescue_teams: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dispatched_rescue_teams: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Hospital KPIs
    total_hospitals: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    operational_hospitals: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_hospital_beds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_icu_beds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Shelter KPIs
    total_shelters: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_shelter_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Performance KPIs
    average_response_time_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    system_health_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Serialized JSON breakdown (stored as text for portability)
    incident_type_breakdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    incident_severity_breakdown: Mapped[str | None] = mapped_column(Text, nullable=True)


class SystemMetricSnapshot(Base, TimestampMixin):
    """
    Lightweight time-series KPI snapshot.

    Captured periodically (e.g., every simulation tick or on a cron schedule)
    for powering real-time charts and trend analysis.
    """

    __tablename__ = "system_metric_snapshots"

    __table_args__ = (
        Index("ix_system_metric_snapshots_created_at", "created_at"),
        Index("ix_system_metric_snapshots_metric_name", "metric_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)

    metric_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="e.g., 'active_incidents', 'available_teams', 'shelter_utilization_pct'",
    )

    metric_value: Mapped[float] = mapped_column(Float, nullable=False)

    unit: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="e.g., 'count', 'percent', 'minutes'",
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="analytics_service",
        doc="Which service produced this metric.",
    )
