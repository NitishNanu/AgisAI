"""
AegisAI JWT Security & RBAC — Authentication Core.

Provides:
  - Password hashing & verification via bcrypt
  - JWT access and refresh token creation/decoding
  - FastAPI dependency: get_current_user (loads User from DB)
  - FastAPI dependency: get_current_active_user (checks is_active flag)
  - RequireRole — callable RBAC guard dependency class

RBAC Role Hierarchy (highest to lowest privilege):
  ADMIN > COMMANDER > DISPATCHER > MEDIC > RESPONDER > CITIZEN
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.common.exceptions import ForbiddenException, UnauthorizedException
from app.core.config.settings import settings
from app.core.database.session import get_db

# ---------------------------------------------------------------------------
# OAuth2 scheme — tokenUrl points to the Aegis login endpoint
# ---------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1}/auth/login",
    auto_error=False,  # We handle missing token ourselves for better error messages
)


# ---------------------------------------------------------------------------
# Password utilities
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    """Hash a raw password using bcrypt. Store the result, never the plain text."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a stored bcrypt hash."""
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Token creation
# ---------------------------------------------------------------------------
def _create_token(
    subject: Any,
    expires_delta: timedelta,
    token_type: str = "access",
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Internal token factory. Signs a JWT with the platform secret key.

    Args:
        subject: The entity identifier to encode as `sub` (user ID).
        expires_delta: How long until the token expires.
        token_type: "access" or "refresh" — stored as `type` claim.
        extra_claims: Additional claims merged into the payload.

    Returns:
        Signed JWT string.
    """
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": now + expires_delta,
        "type": token_type,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# Backwards-compatible alias used by existing tests
def create_token(
    subject: Any,
    expires_delta: timedelta,
    token_type: str = "access",
    claims: dict[str, Any] | None = None,
) -> str:
    """Backwards-compatible token factory wrapper."""
    return _create_token(subject, expires_delta, token_type, claims)


def create_access_token(subject: Any, role: str = "CITIZEN") -> str:
    """
    Create a short-lived JWT access token.

    Embeds the user role for RBAC validation without a DB hit on every request.
    """
    return _create_token(
        subject=subject,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access",
        extra_claims={"role": role.upper()},
    )


def create_refresh_token(subject: Any) -> str:
    """
    Create a long-lived JWT refresh token.

    Refresh tokens do NOT carry role claims — used only to issue new access tokens.
    """
    return _create_token(
        subject=subject,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        token_type="refresh",
    )


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Raises:
        UnauthorizedException: If the token is malformed, expired, or tampered.
    """
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError as exc:
        raise UnauthorizedException(f"Invalid or expired token: {exc}") from exc


# ---------------------------------------------------------------------------
# FastAPI Dependencies
# ---------------------------------------------------------------------------
def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Any:
    """
    FastAPI dependency: extract and validate the Bearer token, then load
    the corresponding User from the database.

    Returns:
        User ORM instance.

    Raises:
        UnauthorizedException: On missing, malformed, or expired token.
    """
    if not token or token.strip() in ("", "null", "undefined", "None"):
        raise UnauthorizedException("Authentication token is missing.")

    payload = decode_token(token)

    if payload.get("type") != "access":
        raise UnauthorizedException("Invalid token type. Use an access token.")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException("Token payload is missing the subject claim.")

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise UnauthorizedException("Token subject is not a valid user identifier.")

    # Import here to avoid circular imports between security and auth module
    from app.modules.auth.models import User  # noqa: PLC0415

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise UnauthorizedException("User associated with this token no longer exists.")

    return user


def get_optional_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Any | None:
    """
    FastAPI dependency: extract user if valid token present, otherwise None.
    Does not raise UnauthorizedException.
    """
    if not token or token.strip() in ("", "null", "undefined", "None"):
        return None
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        user_id_str = payload.get("sub")
        if not user_id_str:
            return None
        user_id = int(user_id_str)
        from app.modules.auth.models import User  # noqa: PLC0415
        return db.query(User).filter(User.id == user_id).first()
    except Exception:
        return None



def get_current_active_user(
    current_user: Any = Depends(get_current_user),
) -> Any:
    """
    FastAPI dependency: same as get_current_user, plus active flag check.

    Use this on all protected endpoints to prevent suspended accounts from
    making API calls even with a valid token.

    Raises:
        ForbiddenException: If the user account is deactivated.
    """
    if not getattr(current_user, "is_active", True):
        raise ForbiddenException("Your account has been deactivated. Contact an administrator.")
    return current_user


# ---------------------------------------------------------------------------
# RBAC Guard
# ---------------------------------------------------------------------------
class RequireRole:
    """
    RBAC Authorization Dependency Guard.

    Usage:
        @router.get("/admin-only")
        def endpoint(user = Depends(RequireRole(["ADMIN"]))):
            ...

    ADMIN role always passes regardless of allowed_roles list.
    """

    def __init__(self, allowed_roles: list[str]) -> None:
        self.allowed_roles = [role.upper() for role in allowed_roles]

    def __call__(self, current_user: Any = Depends(get_current_active_user)) -> Any:
        """Check if the current user's role is in the allowed list."""
        user_role: str = getattr(current_user, "role", "CITIZEN").upper()

        # ADMIN always has full access
        if user_role == "ADMIN":
            return current_user

        if user_role not in self.allowed_roles:
            raise ForbiddenException(
                f"Role '{user_role}' is not authorized for this action. "
                f"Required: {self.allowed_roles}"
            )
        return current_user
