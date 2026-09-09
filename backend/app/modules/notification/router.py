"""
AegisAI Notification Module â€” API Router.
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.common.response import ApiResponse
from app.core.database.session import get_db
from app.core.security.jwt import RequireRole, get_current_active_user
from app.modules.auth.models import User
from app.modules.notification.schemas import AlertCreate, AlertResponse, MarkReadRequest
from app.modules.notification.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications & Alerts"])


@router.post(
    "/alerts",
    response_model=ApiResponse[AlertResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a system alert (ADMIN only)",
)
def create_alert(
    payload: AlertCreate,
    db: Session = Depends(get_db),
    _: User = Depends(RequireRole(["ADMIN"])),
) -> ApiResponse[AlertResponse]:
    """Manually trigger a system alert."""
    alert = NotificationService.create_alert(db, payload)
    return ApiResponse.created(data=AlertResponse.model_validate(alert))


@router.get(
    "/alerts",
    response_model=ApiResponse[dict],
    summary="Get my alerts",
)
def get_my_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ApiResponse[dict]:
    """Fetch alerts targeted to the current user, their role, or broadcast."""
    alerts, total = NotificationService.get_my_alerts(
        db, current_user.id, current_user.role, page, page_size, unread_only
    )
    items = [AlertResponse.model_validate(a).model_dump() for a in alerts]
    return ApiResponse.paginated(data=items, total=total, page=page, page_size=page_size)


@router.post(
    "/alerts/mark-read",
    response_model=ApiResponse[dict],
    summary="Mark alerts as read",
)
def mark_alerts_read(
    payload: MarkReadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ApiResponse[dict]:
    """Mark a list of alert IDs as read."""
    count = NotificationService.mark_alerts_read(db, payload.alert_ids, current_user.id, current_user.role)
    return ApiResponse.ok(data={"updated_count": count}, message=f"Marked {count} alerts as read.")
