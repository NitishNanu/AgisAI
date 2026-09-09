"""
AegisAI Analytics Module — Pydantic v2 Schemas.

Defines all request/response models for the analytics API.
All schemas use model_config = ConfigDict(from_attributes=True) for
direct validation from SQLAlchemy ORM instances.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TypeBreakdownItem(BaseModel):
    """A single bucket in a type-based breakdown."""

    type: str
    count: int


class SeverityBreakdownItem(BaseModel):
    """A single bucket in a severity-based breakdown."""

    severity: str
    count: int


class StatusBreakdownItem(BaseModel):
    """A single bucket in a status-based breakdown."""

    status: str
    count: int


class TeamUtilizationSummary(BaseModel):
    """Rescue team availability and utilization metrics."""

    total: int
    available: int
    dispatched: int
    on_standby: int
    utilization_percent: float


class ShelterUtilizationSummary(BaseModel):
    """Aggregate shelter capacity and occupancy."""

    total_shelters: int
    total_capacity: int
    total_occupancy: int
    available_capacity: int
    occupancy_percent: float


class HospitalSummary(BaseModel):
    """Aggregate hospital capacity and availability."""

    total: int
    operational: int
    offline: int
    total_beds: int
    total_icu_beds: int
    with_oxygen: int


class DashboardSummary(BaseModel):
    """
    Mission Control dashboard KPI summary.

    Top-level aggregate for the emergency operations dashboard.
    Combines the most critical real-time metrics from all domains.
    """

    total_active_incidents: int = Field(..., description="Incidents in REPORTED/RESPONDING/INVESTIGATING state")
    critical_incidents: int = Field(..., description="Active incidents with CRITICAL severity")
    total_hospitals: int
    operational_hospitals: int
    total_shelters: int
    available_shelter_capacity: int
    available_rescue_teams: int
    dispatched_rescue_teams: int


class EmergencyAnalyticsSummary(BaseModel):
    """Legacy analytics summary schema — kept for backward compatibility."""

    total_incidents: int = 0
    active_incidents: int = 0
    resolved_incidents: int = 0
    total_rescue_teams: int = 0
    available_rescue_teams: int = 0
    dispatched_rescue_teams: int = 0
    total_hospital_beds: int = 0
    available_icu_beds: int = 0
    average_response_time_minutes: float = 0.0
    system_health_score: float = 0.0


class ResourceUtilizationReport(BaseModel):
    """Combined resource utilization across teams, shelters, and hospitals."""

    teams: TeamUtilizationSummary
    shelters: ShelterUtilizationSummary
    hospitals: HospitalSummary
    recent_assignments: list[dict[str, Any]] = Field(default_factory=list)


class GenerateReportRequest(BaseModel):
    """Request body for triggering a new analytics report generation."""

    title: str = Field(
        default="Platform Report",
        max_length=200,
        description="Human-readable title for this report",
    )


class AnalyticsReportResponse(BaseModel):
    """Response schema for a persisted analytics report."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    environment: str
    total_incidents: int
    active_incidents: int
    resolved_incidents: int
    critical_incidents: int
    total_rescue_teams: int
    available_rescue_teams: int
    dispatched_rescue_teams: int
    total_hospitals: int
    operational_hospitals: int
    total_hospital_beds: int
    total_icu_beds: int
    total_shelters: int
    available_shelter_capacity: int
    average_response_time_minutes: float | None
    system_health_score: float | None
    incident_type_breakdown: str | None
    incident_severity_breakdown: str | None
    created_at: str | None = None

    def created_at_str(self) -> str | None:
        """Return created_at as ISO string."""
        from datetime import datetime
        if isinstance(self.created_at, datetime):
            return self.created_at.isoformat()
        return str(self.created_at) if self.created_at else None


class MetricHistoryPoint(BaseModel):
    """A single data point in a time-series metric history."""

    timestamp: str | None
    value: float
    unit: str | None = None
