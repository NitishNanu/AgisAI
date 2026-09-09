"""
AegisAI Audit Module — REST API Router.

Exposes endpoints for querying the system audit trail.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.common.response import ApiResponse
from app.core.database.session import get_db
from app.core.security.jwt import RequireRole
from app.modules.audit.service import AuditService
from app.modules.auth.models import User

router = APIRouter(prefix="/audit", tags=["Audit & Governance"])


@router.get("/logs", response_model=ApiResponse[list[dict]])
def get_audit_logs(
    action: str | None = Query(None, description="Filter by action name"),
    entity_type: str | None = Query(None, description="Filter by target entity type"),
    user_id: int | None = Query(None, description="Filter by user ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(RequireRole(["ADMIN", "COMMANDER"])),
) -> ApiResponse[list[dict]]:
    """Retrieve filtered audit trail records."""
    records = AuditService.get_logs(
        db=db,
        action=action,
        entity_type=entity_type,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    data = [
        {
            "id": r.id,
            "user_id": r.user_id,
            "action": r.action,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "ip_address": r.ip_address,
            "details": r.details,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]
    return ApiResponse.ok(data=data, message=f"Retrieved {len(data)} audit log record(s).")
