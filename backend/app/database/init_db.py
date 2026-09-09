"""
RescueNet AI — Database Initialization and Auto-Bootstrap.
"""

import structlog
from sqlalchemy import text

from app.core.database.base import Base
from app.core.database.session import SessionLocal, engine
from app.modules.analytics.models import AnalyticsReport, SystemMetricSnapshot  # noqa: F401
from app.modules.auth.models import User
from app.modules.hospital.models import Hospital
from app.modules.incident.models import Incident
from app.modules.notification.models import Alert
from app.modules.resource.models import RescueTeam, ResourceAssignment, Shelter
from app.modules.scenario.models import Scenario, ScenarioRun

logger = structlog.get_logger("aegis_ai.database")


def init_db():
    from app.core.config.settings import settings

    if settings.ENVIRONMENT == "testing":
        return

    try:
        # PostGIS extension must be installed by a DB superuser.
        # We attempt creation here as a convenience for fresh dev databases;
        # in production the DBA pre-installs it, so a failure here is non-fatal.
        with engine.begin() as connection:
            try:
                connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
                logger.info("postgis_extension_verified")
            except Exception as ext_err:
                logger.warning(
                    "postgis_extension_unavailable",
                    reason=str(ext_err),
                    hint="Ensure PostGIS is installed and the DB user has SUPERUSER or extension privileges.",
                )

        Base.metadata.create_all(bind=engine)
        logger.info("database_tables_verified")

        # Auto-seed if database is empty
        db = SessionLocal()
        try:
            incident_count = db.query(Incident).count()
            if incident_count == 0:
                logger.info("database_empty_auto_seeding")
                try:
                    from app.database.seed import seed_data  # noqa: PLC0415
                    seed_data()
                except ImportError:
                    try:
                        from app.database.seeder import seed_data as seed_data2  # noqa: PLC0415
                        seed_data2()
                    except ImportError:
                        logger.warning("seed_module_not_found", hint="Create app/database/seed.py with a seed_data() function.")
        finally:
            db.close()

    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error("database_initialization_failed", error=str(e))