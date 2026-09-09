"""
AegisAI Incident Module â€” ORM Model.

Defines the `incidents` table (replaces the legacy `disasters` table)
with full production-grade constraints, geospatial indexing, and proper
foreign key relationships.
"""

from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.base import Base, TimestampMixin
from app.modules.incident.enums import DisasterType, IncidentStatus, SeverityLevel

# Build check constraint values from enum members
_DISASTER_TYPES = "(" + ",".join(f"'{t.value}'" for t in DisasterType) + ")"
_SEVERITIES = "(" + ",".join(f"'{s.value}'" for s in SeverityLevel) + ")"
_STATUSES = "(" + ",".join(f"'{s.value}'" for s in IncidentStatus) + ")"


class Incident(Base, TimestampMixin):
    """
    Emergency incident entity â€” the core domain object of AegisAI.

    Each incident represents a real or simulated disaster event with:
    - Geospatial coordinates for mapping and proximity queries
    - Classification (type + severity) for resource matching
    - Operational status tracking through the incident lifecycle
    - Reporter attribution for audit trail
    """

    __tablename__ = "incidents"

    __table_args__ = (
        # DB-level enum enforcement â€” defense in depth beyond Pydantic validation
        CheckConstraint(f"disaster_type IN {_DISASTER_TYPES}", name="ck_incidents_type"),
        CheckConstraint(f"severity IN {_SEVERITIES}", name="ck_incidents_severity"),
        CheckConstraint(f"status IN {_STATUSES}", name="ck_incidents_status"),
        CheckConstraint("latitude >= -90 AND latitude <= 90", name="ck_incidents_lat"),
        CheckConstraint("longitude >= -180 AND longitude <= 180", name="ck_incidents_lon"),
        # Partial index for active incidents â€” most common query pattern
        Index("ix_incidents_status", "status"),
        Index("ix_incidents_type", "disaster_type"),
        Index("ix_incidents_severity", "severity"),
        Index("ix_incidents_reported_by", "reported_by"),
        Index("ix_incidents_lat_lon", "latitude", "longitude"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    disaster_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=SeverityLevel.LOW.value,
        server_default=SeverityLevel.LOW.value,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=IncidentStatus.ACTIVE.value,
        server_default=IncidentStatus.ACTIVE.value,
    )

    latitude: Mapped[float] = mapped_column(Float, nullable=False)

    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # PostGIS geography column for accurate distance calculations
    # Nullable during migration from legacy schema; populated on create
    location = mapped_column(
        # geoalchemy2 Geography type for PostGIS
        # Defined as raw string to avoid import errors if geoalchemy2 unavailable
        __import__("geoalchemy2", fromlist=["Geography"]).Geography(
            geometry_type="POINT",
            srid=4326,
            spatial_index=True,
        ),
        nullable=True,  # nullable for test environments without PostGIS
    )

    # Affected radius in meters — updated as the incident spreads
    affected_radius_meters: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Estimated number of people affected (broad population count)
    estimated_affected_people: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=0, server_default="0"
    )

    # ------------------------------------------------------------------
    # Casualty tracking fields — read by TimeHorizonForecaster and
    # AI Decision Engine StateAggregator. Missing these = always 0.
    # ------------------------------------------------------------------
    estimated_casualties: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0",
        comment="Total casualties (dead + seriously injured)",
    )

    critical_patients: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0",
        comment="Patients requiring immediate ICU-level care",
    )

    # Operational dispatch priority (may differ from severity)
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default="MEDIUM", server_default="MEDIUM",
        comment="Dispatch priority: LOW|MEDIUM|HIGH|CRITICAL",
    )

    reported_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # SQLAlchemy relationship â€” lazy loaded to avoid N+1
    reporter = relationship(
        "User",
        foreign_keys=[reported_by],
        lazy="select",
    )
