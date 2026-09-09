"""
AegisAI Auth Module â€” User ORM Model.

Defines the `users` table with full production-grade constraints:
- Unique indexed email
- Role check constraint enforcing the platform role enum
- is_active flag for soft-deactivation
- Server-side timestamps for auditability
"""

from sqlalchemy import Boolean, CheckConstraint, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.base import Base, TimestampMixin

# Valid roles for the check constraint â€” mirrors AuthRole enum
_VALID_ROLES = "('ADMIN','COMMANDER','DISPATCHER','MEDIC','RESPONDER','CITIZEN')"


class User(Base, TimestampMixin):
    """
    Platform user entity.

    Roles:
      ADMIN      â€” Full system access, user management, simulation control
      COMMANDER  â€” Incident command, resource dispatch, analytics
      DISPATCHER â€” Resource assignment, mission tracking
      MEDIC      â€” Hospital management, triage
      RESPONDER  â€” Field operations, assignment updates
      CITIZEN    â€” Read-only public incident view
    """

    __tablename__ = "users"

    __table_args__ = (
        # Enforce role values at DB level â€” first line of defense
        CheckConstraint(f"role IN {_VALID_ROLES}", name="ck_users_role"),
        # Composite index for auth lookup (email + is_active)
        Index("ix_users_email_active", "email", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="CITIZEN",
        server_default="CITIZEN",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
