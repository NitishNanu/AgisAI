"""
AegisAI / RescueNet AI — External Feeds REST API Router.

Endpoints:
  GET  /api/v1/feeds/sources  — List configured external third-party feeds
  GET  /api/v1/feeds/alerts   — Poll and retrieve live alerts across all feeds
  POST /api/v1/feeds/sync     — Trigger full feed sync and auto-ingestion
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.common.response import ApiResponse
from app.core.database.session import get_db
from app.core.security.jwt import get_current_active_user
from app.modules.auth.models import User
from app.modules.external_feeds.service import feeds_service

router = APIRouter(prefix="/feeds", tags=["Third-Party Disaster Intelligence Feeds"])


@router.get(
    "/sources",
    response_model=ApiResponse[list],
    summary="List all configured third-party feeds and status",
)
def get_sources(
    _: User = Depends(get_current_active_user),
) -> ApiResponse[list]:
    """Returns active third-party feeds (Weather, USGS Earthquakes, News Wires, Satellites)."""
    sources = feeds_service.get_configured_sources()
    return ApiResponse.ok(data=sources, message="Configured feeds retrieved.")


@router.get(
    "/alerts",
    response_model=ApiResponse[list],
    summary="Poll real-time alerts from all external third-party APIs",
)
async def get_live_feed_alerts(
    lat: float = Query(default=19.0760, description="Center latitude"),
    lon: float = Query(default=72.8777, description="Center longitude"),
    _: User = Depends(get_current_active_user),
) -> ApiResponse[list]:
    """Fetches real-time alerts from Open-Meteo Weather, USGS Earthquakes, and News feeds."""
    alerts = await feeds_service.poll_all_feeds(latitude=lat, longitude=lon)
    return ApiResponse.ok(
        data=alerts,
        message=f"Retrieved {len(alerts)} alert(s) from external feeds.",
    )


@router.post(
    "/sync",
    response_model=ApiResponse[dict],
    summary="Sync external feeds and automatically ingest detected disasters",
)
async def sync_feeds(
    persist: bool = Query(default=False, description="Persist detected disasters to DB and map"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ApiResponse[dict]:
    """
    Polls all external feeds, executes the Auto-Discovery pipeline on each,
    and optionally persists them to the live emergency database and map.
    """
    result = await feeds_service.sync_and_auto_ingest(
        db=db,
        reporter_id=current_user.id,
        persist=persist,
    )
    return ApiResponse.ok(
        data=result,
        message=f"Sync completed. Processed {result['total_alerts_detected']} external feed alert(s).",
    )
