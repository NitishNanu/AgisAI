"""
AegisAI Hospital Module â€” API Router.

Endpoints:
  POST   /api/v1/hospitals                   â€” Register hospital (ADMIN/COMMANDER)
  GET    /api/v1/hospitals                   â€” List hospitals
  GET    /api/v1/hospitals/{id}              â€” Get hospital by ID
  PUT    /api/v1/hospitals/{id}              â€” Update hospital (ADMIN/COMMANDER)
  DELETE /api/v1/hospitals/{id}              â€” Delete hospital (ADMIN)
  GET    /api/v1/hospitals/{id}/capacity     â€” Get capacity info
  PATCH  /api/v1/hospitals/{id}/capacity     â€” Update capacity rapidly
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.common.response import ApiResponse
from app.core.database.session import get_db
from app.core.security.jwt import RequireRole, get_current_active_user
from app.modules.auth.models import User
from app.modules.hospital.schemas import (
    HospitalCapacityUpdate,
    HospitalCreate,
    HospitalResponse,
    HospitalSummary,
    HospitalUpdate,
)
from app.modules.hospital.service import HospitalService

router = APIRouter(prefix="/hospitals", tags=["Hospital Management"])


@router.post(
    "",
    response_model=ApiResponse[HospitalResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new hospital (ADMIN/COMMANDER)",
)
def create_hospital(
    payload: HospitalCreate,
    db: Session = Depends(get_db),
    _: User = Depends(RequireRole(["ADMIN", "COMMANDER"])),
) -> ApiResponse[HospitalResponse]:
    """Register a new medical facility in the emergency response network."""
    hospital = HospitalService.create_hospital(db, payload)
    return ApiResponse.created(
        data=HospitalResponse.model_validate(hospital),
        message="Hospital registered successfully.",
    )


@router.get(
    "",
    response_model=ApiResponse[dict],
    summary="List all hospitals",
)
def list_hospitals(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    operational_only: bool = Query(default=False, description="Return only operational hospitals"),
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """Return a paginated list of all hospitals in the response network."""
    hospitals, total = HospitalService.list_hospitals(db, page, page_size, operational_only)
    items = [HospitalSummary.model_validate(h) for h in hospitals]
    return ApiResponse.paginated(
        data=[i.model_dump() for i in items],
        total=total,
        page=page,
        page_size=page_size,
        message=f"Retrieved {len(items)} hospitals.",
    )


@router.get(
    "/{hospital_id}",
    response_model=ApiResponse[HospitalResponse],
    summary="Get hospital by ID",
)
def get_hospital(
    hospital_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> ApiResponse[HospitalResponse]:
    """Retrieve full details of a single hospital."""
    hospital = HospitalService.get_hospital(db, hospital_id)
    return ApiResponse.ok(
        data=HospitalResponse.model_validate(hospital),
        message="Hospital retrieved successfully.",
    )


@router.put(
    "/{hospital_id}",
    response_model=ApiResponse[HospitalResponse],
    summary="Update hospital details (ADMIN/COMMANDER)",
)
def update_hospital(
    hospital_id: int,
    payload: HospitalUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(RequireRole(["ADMIN", "COMMANDER"])),
) -> ApiResponse[HospitalResponse]:
    """Update hospital details including location and capacity."""
    hospital = HospitalService.update_hospital(db, hospital_id, payload)
    return ApiResponse.ok(
        data=HospitalResponse.model_validate(hospital),
        message="Hospital updated successfully.",
    )


@router.delete(
    "/{hospital_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a hospital (ADMIN only)",
)
def delete_hospital(
    hospital_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(RequireRole(["ADMIN"])),
) -> None:
    """Remove a hospital from the response network."""
    HospitalService.delete_hospital(db, hospital_id)
    return None


@router.get(
    "/{hospital_id}/capacity",
    response_model=ApiResponse[dict],
    summary="Get hospital capacity status",
)
def get_capacity(
    hospital_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> ApiResponse[dict]:
    """Return current bed and resource capacity for a hospital."""
    hospital = HospitalService.get_hospital(db, hospital_id)
    return ApiResponse.ok(
        data={
            "hospital_id": hospital.id,
            "name": hospital.name,
            "total_beds": hospital.beds,
            "icu_beds": hospital.icu_beds,
            "oxygen_available": hospital.oxygen_available,
            "blood_bank_available": hospital.blood_bank_available,
            "is_operational": hospital.is_operational,
        },
        message="Hospital capacity retrieved.",
    )


@router.patch(
    "/{hospital_id}/capacity",
    response_model=ApiResponse[HospitalResponse],
    summary="Rapidly update hospital capacity (ADMIN/COMMANDER/MEDIC)",
)
def update_capacity(
    hospital_id: int,
    payload: HospitalCapacityUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(RequireRole(["ADMIN", "COMMANDER", "MEDIC"])),
) -> ApiResponse[HospitalResponse]:
    """Quick capacity update endpoint for use during active mass casualty events."""
    hospital = HospitalService.update_capacity(db, hospital_id, payload)
    return ApiResponse.ok(
        data=HospitalResponse.model_validate(hospital),
        message="Hospital capacity updated.",
    )
