"""
RescueNet AI — Mission Service.

Provides complete nested mission view data aggregating Assignment, Incident,
RescueTeam, routing geometry, and ETA details.
"""

import json
from typing import Any
from sqlalchemy.orm import Session

from app.modules.incident.models import Incident
from app.modules.resource.models import RescueTeam, ResourceAssignment


class MissionService:
    """
    Service for querying and structuring mission control tracking data.
    """

    @staticmethod
    def get_active_missions(
        db: Session,
        active_only: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Return complete nested mission details for tracking in Mission Control.

        Fields returned:
        - assignment_id
        - status
        - disaster (id, title, type, severity, status, latitude, longitude)
        - team (id, name, vehicle_type, members, status, latitude, longitude)
        - distance_km
        - eta_minutes
        - route_geometry
        - started_at
        - completed_at
        - created_at
        """
        query = db.query(ResourceAssignment)

        if active_only:
            query = query.filter(
                ResourceAssignment.status.in_(["ASSIGNED", "DISPATCHED", "EN_ROUTE", "ARRIVED"])
            )

        assignments = query.order_by(ResourceAssignment.created_at.desc()).all()

        missions: list[dict[str, Any]] = []

        for a in assignments:
            incident = a.incident or db.query(Incident).filter(Incident.id == a.incident_id).first()
            team = a.team or db.query(RescueTeam).filter(RescueTeam.id == a.team_id).first()

            if incident is None or team is None:
                continue

            # Parse route geometry if present
            geom = None
            if a.route_geometry:
                try:
                    geom = json.loads(a.route_geometry)
                except Exception:
                    geom = a.route_geometry

            missions.append({
                "assignment_id": a.id,
                "status": a.status,
                "disaster": {
                    "id": incident.id,
                    "title": incident.title,
                    "type": incident.disaster_type,
                    "severity": incident.severity,
                    "status": incident.status,
                    "latitude": incident.latitude,
                    "longitude": incident.longitude,
                },
                "team": {
                    "id": team.id,
                    "name": team.team_name,
                    "vehicle_type": team.vehicle_type,
                    "members": team.members,
                    "status": team.status,
                    "latitude": team.latitude,
                    "longitude": team.longitude,
                },
                "distance_km": a.distance_km,
                "eta_minutes": a.estimated_arrival_minutes,
                "route_geometry": geom,
                "started_at": a.started_at,
                "completed_at": a.completed_at,
                "created_at": a.created_at,
            })

        return missions
