"""
RescueNet AI — Missions API Router.

Provides Mission Control viewing and real-time tracking endpoints:
  GET /api/v1/missions — List all missions / active missions
"""

from typing import Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.common.response import ApiResponse
from app.core.database.session import get_db
from app.services.mission_service import MissionService

router = APIRouter(prefix="/missions", tags=["Mission Control"])


@router.get(
    "",
    summary="Get mission tracking data for Mission Control",
)
def get_missions(
    active_only: bool = Query(default=False, description="Filter only active missions"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Return comprehensive nested mission information for dashboard visualization:
    - assignment_id, status
    - disaster (id, title, type, severity, status, coordinates)
    - team (id, name, vehicle_type, members, status, coordinates)
    - distance_km, eta_minutes, route_geometry
    - started_at, completed_at, created_at
    """
    missions = MissionService.get_active_missions(db, active_only=active_only)
    return {
        "success": True,
        "count": len(missions),
        "data": missions,
    }
