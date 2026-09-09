"""
AegisAI Auth Module â€” API Router.

Provides identity and user management endpoints:
  POST /api/v1/auth/register     â€” Self-registration
  POST /api/v1/auth/login        â€” Credential authentication (rate limited)
  POST /api/v1/auth/refresh      â€” Token refresh
  GET  /api/v1/auth/me           â€” Authenticated user's own profile

  GET   /api/v1/users             â€” List all users (ADMIN only)
  GET   /api/v1/users/{id}        â€” Get user by ID (ADMIN/COMMANDER)
  PATCH /api/v1/users/{id}/role   â€” Change user role (ADMIN only)
  PATCH /api/v1/users/{id}/deactivate â€” Deactivate account (ADMIN)
  PATCH /api/v1/users/{id}/reactivate â€” Reactivate account (ADMIN)
"""

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.common.exceptions import EntityNotFoundException, UnauthorizedException
from app.core.common.response import ApiResponse
from app.core.database.session import get_db
from app.core.middleware.rate_limiter import limiter
from app.core.security.jwt import RequireRole, get_current_active_user
from app.modules.auth.models import User
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import (
    RefreshTokenRequest,
    TokenResponse,
    UpdateUserRoleRequest,
    UserListResponse,
    UserLoginRequest,
    UserProfileResponse,
    UserRegisterRequest,
)
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth & Identity"])
users_router = APIRouter(prefix="/users", tags=["User Management"])


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------
@router.post(
    "/register",
    response_model=ApiResponse[UserProfileResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[UserProfileResponse]:
    """
    Create a new platform user account.

    Open endpoint â€” no authentication required.
    Validates email uniqueness, enforces password strength, and returns profile data.
    """
    user = AuthService.register_user(db, request)
    profile = UserProfileResponse.model_validate(user)
    return ApiResponse.created(data=profile, message="User registered successfully.")


@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
    summary="Authenticate and obtain JWT tokens",
)
@limiter.limit("20/minute")
async def login(
    request: Request,
    body: UserLoginRequest | None = None,
    db: Session = Depends(get_db),
) -> ApiResponse[TokenResponse]:
    """
    Authenticate with email and password (supports JSON body and form-encoded data).

    Returns a JWT access token (short-lived) and refresh token (long-lived).
    Rate limited to 20 requests/minute to prevent brute-force attacks.
    """
    email = ""
    password = ""

    if body is not None:
        email = body.email
        password = body.password
    else:
        # Fallback to form data or json if body wasn't passed directly
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                json_data = await request.json()
                email = json_data.get("email") or json_data.get("username", "")
                password = json_data.get("password", "")
            except Exception:
                pass
        else:
            try:
                form = await request.form()
                email = str(form.get("username") or form.get("email") or "")
                password = str(form.get("password") or "")
            except Exception:
                pass

    if not email or not password:
        raise UnauthorizedException("Email and password are required.")

    tokens = AuthService.login_user(db, email=email, password=password)
    return ApiResponse.ok(data=tokens, message="Login successful.")


@router.post(
    "/refresh",
    response_model=ApiResponse[TokenResponse],
    summary="Refresh access token using refresh token",
)
def refresh_token(
    body: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[TokenResponse]:
    """
    Exchange a valid refresh token for a fresh access + refresh token pair.

    The old refresh token is consumed and a new pair is returned.
    """
    tokens = AuthService.refresh_access_token(db, body.refresh_token)
    return ApiResponse.ok(data=tokens, message="Tokens refreshed successfully.")


@router.get(
    "/me",
    response_model=ApiResponse[UserProfileResponse],
    summary="Get current authenticated user's profile",
)
def get_me(
    current_user: User = Depends(get_current_active_user),
) -> ApiResponse[UserProfileResponse]:
    """Return the profile of the currently authenticated user."""
    profile = UserProfileResponse.model_validate(current_user)
    return ApiResponse.ok(data=profile, message="Profile retrieved successfully.")


# ---------------------------------------------------------------------------
# User management endpoints (admin operations)
# ---------------------------------------------------------------------------
@users_router.get(
    "",
    response_model=ApiResponse[dict],
    summary="List all users (ADMIN only)",
)
def list_users(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=200, description="Items per page"),
    role_filter: str | None = Query(default=None, description="Filter by role"),
    active_only: bool = Query(default=False, description="Return only active users"),
    db: Session = Depends(get_db),
    _: User = Depends(RequireRole(["ADMIN"])),
) -> ApiResponse[dict]:
    """
    Paginated list of all platform users.
    Restricted to ADMIN role only.
    """
    repo = UserRepository(db)
    skip = (page - 1) * page_size
    users, total = repo.list_users(
        skip=skip,
        limit=page_size,
        role_filter=role_filter,
        active_only=active_only,
    )
    items = [UserListResponse.model_validate(u) for u in users]
    return ApiResponse.paginated(
        data=[item.model_dump() for item in items],
        total=total,
        page=page,
        page_size=page_size,
        message=f"Retrieved {len(items)} users.",
    )


@users_router.get(
    "/{user_id}",
    response_model=ApiResponse[UserProfileResponse],
    summary="Get user by ID (ADMIN/COMMANDER)",
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(RequireRole(["ADMIN", "COMMANDER"])),
) -> ApiResponse[UserProfileResponse]:
    """Retrieve a specific user's full profile by their ID."""
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if user is None:
        raise EntityNotFoundException("User", user_id)
    profile = UserProfileResponse.model_validate(user)
    return ApiResponse.ok(data=profile, message="User retrieved successfully.")


@users_router.patch(
    "/{user_id}/role",
    response_model=ApiResponse[UserProfileResponse],
    summary="Update user role (ADMIN only)",
)
def update_role(
    user_id: int,
    body: UpdateUserRoleRequest,
    db: Session = Depends(get_db),
    _: User = Depends(RequireRole(["ADMIN"])),
) -> ApiResponse[UserProfileResponse]:
    """
    Change a user's platform role.

    Only ADMIN can promote or demote users. The change takes effect on the
    next login (tokens are not immediately invalidated).
    """
    repo = UserRepository(db)
    user = repo.update_role(user_id, body.role.value)
    if user is None:
        raise EntityNotFoundException("User", user_id)
    profile = UserProfileResponse.model_validate(user)
    return ApiResponse.ok(data=profile, message=f"Role updated to '{body.role.value}'.")


@users_router.patch(
    "/{user_id}/deactivate",
    response_model=ApiResponse[UserProfileResponse],
    summary="Deactivate user account (ADMIN only)",
)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(RequireRole(["ADMIN"])),
) -> ApiResponse[UserProfileResponse]:
    """Soft-deactivate a user account. The account data is preserved."""
    if user_id == current_admin.id:
        from app.core.common.exceptions import ValidationException
        raise ValidationException("You cannot deactivate your own account.")

    repo = UserRepository(db)
    user = repo.deactivate(user_id)
    if user is None:
        raise EntityNotFoundException("User", user_id)
    profile = UserProfileResponse.model_validate(user)
    return ApiResponse.ok(data=profile, message="Account deactivated.")


@users_router.patch(
    "/{user_id}/reactivate",
    response_model=ApiResponse[UserProfileResponse],
    summary="Reactivate user account (ADMIN only)",
)
def reactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(RequireRole(["ADMIN"])),
) -> ApiResponse[UserProfileResponse]:
    """Reactivate a previously deactivated user account."""
    repo = UserRepository(db)
    user = repo.reactivate(user_id)
    if user is None:
        raise EntityNotFoundException("User", user_id)
    profile = UserProfileResponse.model_validate(user)
    return ApiResponse.ok(data=profile, message="Account reactivated.")
