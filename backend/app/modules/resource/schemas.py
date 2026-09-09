"""
AegisAI Resource Module â€” Pydantic v2 Schemas.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.resource.enums import AssignmentStatus, TeamStatus, VehicleType


# ---------------------------------------------------------------------------
# Rescue Team Schemas
# ---------------------------------------------------------------------------
class RescueTeamCreate(BaseModel):
    team_name: str = Field(..., min_length=3, max_length=100)
    vehicle_type: VehicleType
    members: int = Field(default=1, gt=0)
    status: TeamStatus = Field(default=TeamStatus.AVAILABLE)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)


class RescueTeamUpdate(BaseModel):
    team_name: str | None = Field(default=None, min_length=3, max_length=100)
    vehicle_type: VehicleType | None = None
    members: int | None = Field(default=None, gt=0)
    status: TeamStatus | None = None
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)


class RescueTeamResponse(BaseModel):
    id: int
    team_name: str
    vehicle_type: str
    members: int
    status: str
    latitude: float
    longitude: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Shelter Schemas
# ---------------------------------------------------------------------------
class ShelterCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    address: str | None = Field(default=None, max_length=500)
    capacity: int = Field(..., gt=0)
    current_occupancy: int = Field(default=0, ge=0)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)


class ShelterUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=200)
    address: str | None = Field(default=None, max_length=500)
    capacity: int | None = Field(default=None, gt=0)
    current_occupancy: int | None = Field(default=None, ge=0)
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)


class ShelterResponse(BaseModel):
    id: int
    name: str
    address: str | None
    capacity: int
    current_occupancy: int
    latitude: float
    longitude: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Assignment & Mission Schemas
# ---------------------------------------------------------------------------
class AssignmentCreate(BaseModel):
    incident_id: int
    team_id: int
    estimated_arrival_minutes: float | None = Field(default=None, ge=0)
    distance_km: float | None = Field(default=None, ge=0)
    route_geometry: str | None = None
    notes: str | None = Field(default=None, max_length=1000)


class AssignmentUpdate(BaseModel):
    status: AssignmentStatus | None = None
    estimated_arrival_minutes: float | None = Field(default=None, ge=0)
    distance_km: float | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=1000)


class AssignmentStatusUpdate(BaseModel):
    status: AssignmentStatus


class AssignmentResponse(BaseModel):
    id: int
    incident_id: int
    team_id: int
    dispatched_by: int
    status: str
    estimated_arrival_minutes: float | None = None
    distance_km: float | None = None
    route_geometry: str | None = None
    notes: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MissionDisasterDetail(BaseModel):
    id: int
    title: str
    type: str
    severity: str
    status: str
    latitude: float
    longitude: float


class MissionTeamDetail(BaseModel):
    id: int
    name: str
    vehicle_type: str
    members: int
    status: str
    latitude: float
    longitude: float


class MissionDetailResponse(BaseModel):
    assignment_id: int
    status: str
    disaster: MissionDisasterDetail
    team: MissionTeamDetail
    distance_km: float | None = None
    eta_minutes: float | None = None
    route_geometry: object | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None
