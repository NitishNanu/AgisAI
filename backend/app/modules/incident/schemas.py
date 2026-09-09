"""
AegisAI Incident Module â€” Pydantic v2 Schemas.

Strictly typed request and response schemas for incident management.
All geographic coordinates are validated at the schema level.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.incident.enums import DisasterType, IncidentStatus, SeverityLevel


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------
class IncidentCreate(BaseModel):
    """Schema for reporting a new incident."""

    title: str = Field(..., min_length=5, max_length=200, description="Incident title")
    description: str | None = Field(default=None, max_length=2000, description="Detailed description")
    disaster_type: DisasterType = Field(..., description="Classification of the disaster")
    severity: SeverityLevel = Field(default=SeverityLevel.MEDIUM, description="Severity level")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Incident latitude (WGS84)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Incident longitude (WGS84)")
    affected_radius_meters: float | None = Field(
        default=None, gt=0, le=500_000, description="Estimated affected radius in meters"
    )
    estimated_affected_people: int | None = Field(
        default=None, ge=0, description="Estimated number of affected people"
    )

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        """Title must not be whitespace only."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Incident title must not be blank.")
        return stripped


class IncidentUpdate(BaseModel):
    """Schema for updating an existing incident. All fields optional (PATCH semantics)."""

    title: str | None = Field(default=None, min_length=5, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    severity: SeverityLevel | None = Field(default=None)
    status: IncidentStatus | None = Field(default=None)
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    affected_radius_meters: float | None = Field(default=None, gt=0, le=500_000)
    estimated_affected_people: int | None = Field(default=None, ge=0)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------
class ReporterSummary(BaseModel):
    """Minimal reporter info embedded in incident responses."""

    id: int
    name: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class IncidentResponse(BaseModel):
    """Full incident entity response."""

    id: int
    title: str
    description: str | None
    disaster_type: str
    severity: str
    status: str
    latitude: float
    longitude: float
    affected_radius_meters: float | None
    estimated_affected_people: int | None
    reported_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentSummary(BaseModel):
    """Compact incident representation for list endpoints."""

    id: int
    title: str
    disaster_type: str
    severity: str
    status: str
    latitude: float
    longitude: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NearbyResourceResult(BaseModel):
    """Result item for nearby-resource proximity queries."""

    id: int
    name: str
    distance_meters: float
    latitude: float
    longitude: float
    extra_fields: dict = Field(default_factory=dict)
