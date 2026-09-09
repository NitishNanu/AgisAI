"""
AegisAI Analytics Module — Repository.

Handles all persistence and complex aggregation queries for analytics data.
Provides time-windowed SQL aggregations over the incidents, rescue_teams,
hospitals, and shelters tables, plus CRUD for analytics reports.
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.analytics.models import AnalyticsReport, SystemMetricSnapshot
from app.modules.hospital.models import Hospital
from app.modules.incident.models import Incident
from app.modules.resource.models import RescueTeam, ResourceAssignment, Shelter

logger = structlog.get_logger("aegis_ai.analytics.repository")

# Active incident statuses — used in multiple queries
_ACTIVE_STATUSES = ("REPORTED", "INVESTIGATING", "RESPONDING", "ACTIVE", "MONITORING")


class AnalyticsRepository:
    """
    Repository for analytics aggregations and report persistence.

    All aggregation methods return plain Python dicts suitable for
    direct serialization — no ORM model hydration overhead.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    # --- Dashboard Aggregations ----------------------------------------------

    def count_active_incidents(self) -> int:
        """Count incidents currently in an active operational state."""
        return (
            self._db.query(Incident)
            .filter(Incident.status.in_(_ACTIVE_STATUSES))
            .count()
        )

    def count_incidents_by_type(self) -> list[dict[str, Any]]:
        """Group and count all incidents by disaster_type."""
        rows = (
            self._db.query(Incident.disaster_type, func.count(Incident.id).label("count"))
            .group_by(Incident.disaster_type)
            .order_by(func.count(Incident.id).desc())
            .all()
        )
        return [{"type": row.disaster_type, "count": row.count} for row in rows]

    def count_incidents_by_severity(self) -> list[dict[str, Any]]:
        """Group and count all incidents by severity level."""
        rows = (
            self._db.query(Incident.severity, func.count(Incident.id).label("count"))
            .group_by(Incident.severity)
            .order_by(func.count(Incident.id).desc())
            .all()
        )
        return [{"severity": row.severity, "count": row.count} for row in rows]

    def count_incidents_by_status(self) -> list[dict[str, Any]]:
        """Group and count incidents by their current lifecycle status."""
        rows = (
            self._db.query(Incident.status, func.count(Incident.id).label("count"))
            .group_by(Incident.status)
            .order_by(func.count(Incident.id).desc())
            .all()
        )
        return [{"status": row.status, "count": row.count} for row in rows]

    def get_incidents_in_window(self, hours: int = 24) -> list[dict[str, Any]]:
        """Return incident counts bucketed by hour for the past N hours."""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        rows = (
            self._db.query(Incident)
            .filter(Incident.created_at >= since)
            .order_by(Incident.created_at.asc())
            .all()
        )
        return [
            {
                "id": r.id,
                "title": r.title,
                "type": r.disaster_type,
                "severity": r.severity,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]

    # --- Resource Aggregations -----------------------------------------------

    def get_team_utilization(self) -> dict[str, Any]:
        """Calculate rescue team utilization rates."""
        total = self._db.query(RescueTeam).count()
        available = self._db.query(RescueTeam).filter(RescueTeam.status == "AVAILABLE").count()
        dispatched = self._db.query(RescueTeam).filter(RescueTeam.status == "DISPATCHED").count()
        on_standby = self._db.query(RescueTeam).filter(RescueTeam.status == "STANDBY").count()

        utilization_pct = round((dispatched / total * 100), 1) if total > 0 else 0.0

        return {
            "total": total,
            "available": available,
            "dispatched": dispatched,
            "on_standby": on_standby,
            "utilization_percent": utilization_pct,
        }

    def get_shelter_utilization(self) -> dict[str, Any]:
        """Calculate aggregate shelter occupancy across all shelters."""
        total_capacity_res = self._db.query(func.sum(Shelter.capacity)).scalar()
        total_occupancy_res = self._db.query(func.sum(Shelter.current_occupancy)).scalar()
        total_shelters = self._db.query(Shelter).count()

        total_capacity = int(total_capacity_res or 0)
        total_occupancy = int(total_occupancy_res or 0)
        available_capacity = max(0, total_capacity - total_occupancy)
        occupancy_pct = round((total_occupancy / total_capacity * 100), 1) if total_capacity > 0 else 0.0

        return {
            "total_shelters": total_shelters,
            "total_capacity": total_capacity,
            "total_occupancy": total_occupancy,
            "available_capacity": available_capacity,
            "occupancy_percent": occupancy_pct,
        }

    def get_hospital_summary(self) -> dict[str, Any]:
        """Aggregate hospital bed and resource availability."""
        total = self._db.query(Hospital).count()
        operational = self._db.query(Hospital).filter(Hospital.is_operational.is_(True)).count()
        total_beds = int(self._db.query(func.sum(Hospital.beds)).scalar() or 0)
        total_icu = int(self._db.query(func.sum(Hospital.icu_beds)).scalar() or 0)
        oxygen_count = self._db.query(Hospital).filter(Hospital.oxygen_available.is_(True)).count()

        return {
            "total": total,
            "operational": operational,
            "offline": total - operational,
            "total_beds": total_beds,
            "total_icu_beds": total_icu,
            "with_oxygen": oxygen_count,
        }

    def get_recent_assignments(self, limit: int = 10) -> list[dict[str, Any]]:
        """Return the most recent resource dispatch assignments."""
        rows = (
            self._db.query(ResourceAssignment)
            .order_by(ResourceAssignment.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "incident_id": r.incident_id,
                "team_id": r.team_id,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]

    # --- Report Persistence --------------------------------------------------

    def create_report(self, data: dict[str, Any]) -> AnalyticsReport:
        """Persist a full analytics report snapshot."""
        report = AnalyticsReport(
            title=data.get("title", "Platform Report"),
            environment=data.get("environment", "production"),
            total_incidents=data.get("total_incidents", 0),
            active_incidents=data.get("active_incidents", 0),
            resolved_incidents=data.get("resolved_incidents", 0),
            critical_incidents=data.get("critical_incidents", 0),
            total_rescue_teams=data.get("total_rescue_teams", 0),
            available_rescue_teams=data.get("available_rescue_teams", 0),
            dispatched_rescue_teams=data.get("dispatched_rescue_teams", 0),
            total_hospitals=data.get("total_hospitals", 0),
            operational_hospitals=data.get("operational_hospitals", 0),
            total_hospital_beds=data.get("total_hospital_beds", 0),
            total_icu_beds=data.get("total_icu_beds", 0),
            total_shelters=data.get("total_shelters", 0),
            available_shelter_capacity=data.get("available_shelter_capacity", 0),
            average_response_time_minutes=data.get("average_response_time_minutes"),
            system_health_score=data.get("system_health_score"),
            incident_type_breakdown=json.dumps(data.get("incident_type_breakdown", [])),
            incident_severity_breakdown=json.dumps(data.get("incident_severity_breakdown", [])),
        )
        self._db.add(report)
        self._db.commit()
        self._db.refresh(report)
        logger.info("analytics_report_created", report_id=report.id)
        return report

    def get_report_by_id(self, report_id: int) -> AnalyticsReport | None:
        """Fetch a persisted report by its primary key."""
        return self._db.query(AnalyticsReport).filter(AnalyticsReport.id == report_id).first()

    def list_reports(self, skip: int = 0, limit: int = 50) -> tuple[list[AnalyticsReport], int]:
        """Return paginated list of reports ordered by most recent first."""
        total = self._db.query(AnalyticsReport).count()
        reports = (
            self._db.query(AnalyticsReport)
            .order_by(AnalyticsReport.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return reports, total

    # --- Metric Snapshots ----------------------------------------------------

    def record_metric_snapshot(
        self,
        metric_name: str,
        metric_value: float,
        unit: str | None = None,
        source: str = "analytics_service",
    ) -> SystemMetricSnapshot:
        """Persist a single time-series metric data point."""
        snapshot = SystemMetricSnapshot(
            metric_name=metric_name,
            metric_value=metric_value,
            unit=unit,
            source=source,
        )
        self._db.add(snapshot)
        self._db.commit()
        self._db.refresh(snapshot)
        return snapshot

    def get_metric_history(
        self,
        metric_name: str,
        hours: int = 24,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """Return time-series data for a specific metric over the past N hours."""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        rows = (
            self._db.query(SystemMetricSnapshot)
            .filter(
                SystemMetricSnapshot.metric_name == metric_name,
                SystemMetricSnapshot.created_at >= since,
            )
            .order_by(SystemMetricSnapshot.created_at.asc())
            .limit(limit)
            .all()
        )
        return [
            {
                "timestamp": r.created_at.isoformat() if r.created_at else None,
                "value": r.metric_value,
                "unit": r.unit,
            }
            for r in rows
        ]
