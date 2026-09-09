"""
AegisAI Notification Module â€” ORM Models.
"""

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.base import Base, TimestampMixin


class Alert(Base, TimestampMixin):
    """
    System alerts and notifications for users.
    """

    __tablename__ = "alerts"

    __table_args__ = (
        CheckConstraint("severity IN ('INFO', 'WARNING', 'CRITICAL')", name="ck_alerts_severity"),
        Index("ix_alerts_target_user", "target_user_id"),
        Index("ix_alerts_target_role", "target_role"),
        Index("ix_alerts_is_read", "is_read"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)

    message: Mapped[str] = mapped_column(String(2000), nullable=False)

    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="INFO")

    target_role: Mapped[str | None] = mapped_column(String(50), nullable=True)

    target_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )

    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
