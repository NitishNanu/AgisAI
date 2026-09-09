"""
AegisAI Database Session — SQLAlchemy 2.x Engine & Session Factory.

Configures the connection pool with production-grade settings sourced
from AppSettings. Provides a type-annotated `get_db()` FastAPI dependency
that yields a scoped Session and guarantees cleanup on exit.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config.settings import settings
from app.core.database.base import Base

__all__ = ["Base", "SessionLocal", "create_all_tables", "engine", "get_db"]


# ---------------------------------------------------------------------------
# Engine — single instance per process
# ---------------------------------------------------------------------------
engine = create_engine(
    settings.DATABASE_URL,
    # Pool configuration
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    pool_pre_ping=settings.DATABASE_POOL_PRE_PING,
    # Echo SQL only in DEBUG mode — never in production
    echo=settings.DEBUG,
)


# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # Avoid N+1 fetches after commit
)


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session per request.

    Usage:
        @router.get("/example")
        def endpoint(db: Session = Depends(get_db)):
            ...

    The session is always closed in the `finally` block, even if an
    exception is raised during request processing. Rollback is handled
    by the ErrorHandlerMiddleware at the middleware level for domain
    exceptions; at DB level, the session close auto-rolls back any
    uncommitted transaction.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables() -> None:
    """
    Create all tables defined in ORM models.
    Called at startup only. In production, prefer Alembic migrations.
    """
    # Import all models so their metadata is registered before create_all
    import app.modules.auth.models  # noqa: F401
    import app.modules.hospital.models  # noqa: F401
    import app.modules.incident.models  # noqa: F401
    import app.modules.resource.models  # noqa: F401
    from app.core.database.base import Base

    Base.metadata.create_all(bind=engine)
