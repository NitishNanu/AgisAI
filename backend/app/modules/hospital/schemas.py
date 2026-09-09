"""
AegisAI Hospital Module — Pydantic v2 Schemas.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class HospitalCreate(BaseModel):
    """Schema for registering a new hospital."""

    name: str = Field(..., min_length=3, max_length=200)
    address: str | None = Field(default=None, max_length=500)
    emergency_contact: str | None = Field(default=None, max_length=20)

    # Canonical capacity fields (aligned with ORM and forecaster)
    total_beds: int = Field(..., ge=0, description="Total bed count")
    available_beds: int = Field(..., ge=0, description="Currently available beds")
    icu_capacity: int = Field(default=0, ge=0, description="Total ICU bed count")
    available_icu: int = Field(default=0, ge=0, description="Currently available ICU beds")

    oxygen_available: bool = Field(default=True)
    blood_bank_available: bool = Field(default=False)
    is_operational: bool = Field(default=True)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)

    @model_validator(mode="after")
    def validate_bed_counts(self) -> "HospitalCreate":
        if self.icu_capacity > self.total_beds:
            raise ValueError("icu_capacity cannot exceed total_beds")
        if self.available_beds > self.total_beds:
            raise ValueError("available_beds cannot exceed total_beds")
        if self.available_icu > self.icu_capacity:
            raise ValueError("available_icu cannot exceed icu_capacity")
        return self


class HospitalUpdate(BaseModel):
    """Schema for updating hospital details (PATCH semantics)."""

    name: str | None = Field(default=None, min_length=3, max_length=200)
    address: str | None = Field(default=None, max_length=500)
    emergency_contact: str | None = Field(default=None, max_length=20)

    total_beds: int | None = Field(default=None, ge=0)
    available_beds: int | None = Field(default=None, ge=0)
    icu_capacity: int | None = Field(default=None, ge=0)
    available_icu: int | None = Field(default=None, ge=0)

    oxygen_available: bool | None = None
    blood_bank_available: bool | None = None
    is_operational: bool | None = None
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)


class HospitalCapacityUpdate(BaseModel):
    """Schema for rapid capacity updates during mass casualty events."""

    total_beds: int = Field(..., ge=0, description="Updated total bed count")
    available_beds: int = Field(..., ge=0, description="Updated available bed count")
    icu_capacity: int = Field(..., ge=0, description="Updated ICU bed count")
    available_icu: int = Field(..., ge=0, description="Updated available ICU count")
    oxygen_available: bool = Field(default=True)


class HospitalResponse(BaseModel):
    """Full hospital entity response."""

    id: int
    name: str
    address: str | None
    emergency_contact: str | None
    total_beds: int
    available_beds: int
    icu_capacity: int
    available_icu: int
    oxygen_available: bool
    blood_bank_available: bool
    is_operational: bool
    latitude: float
    longitude: float
    created_at: datetime
    updated_at: datetime

    # Backward-compat aliases for any existing frontend code
    @property
    def beds(self) -> int:
        return self.total_beds

    @property
    def icu_beds(self) -> int:
        return self.icu_capacity

    model_config = ConfigDict(from_attributes=True)


class HospitalSummary(BaseModel):
    """Compact hospital info for list/nearby responses."""

    id: int
    name: str
    total_beds: int
    available_beds: int
    icu_capacity: int
    available_icu: int
    oxygen_available: bool
    is_operational: bool
    latitude: float
    longitude: float

    model_config = ConfigDict(from_attributes=True)

