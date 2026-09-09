"""
AegisAI Incident Module â€” Domain Service.

Orchestrates incident lifecycle operations: reporting, updating, resolving,
and geospatial resource lookups (nearest teams, hospitals, shelters).

The service layer calls OSRM for real routing data with Haversine fallback,
and delegates all persistence to IncidentRepository.
"""

import math
from typing import Any

import structlog
from sqlalchemy.orm import Session

from app.core.common.exceptions import EntityNotFoundException, ForbiddenException
from app.modules.incident.models import Incident
from app.modules.incident.repository import IncidentRepository
from app.modules.incident.schemas import IncidentCreate, IncidentUpdate

logger = structlog.get_logger("aegis_ai.incident")


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance in km between two WGS84 coordinates."""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class IncidentService:
    """
    Incident Domain Service.

    Orchestrates all incident management operations.
    Methods are static â€” the service is stateless.
    """

    @staticmethod
    def report_incident(db: Session, payload: IncidentCreate, reporter_id: int) -> Incident:
        """
        Report a new emergency incident.

        Args:
            db: Database session.
            payload: Validated incident creation data.
            reporter_id: ID of the authenticated user reporting the incident.

        Returns:
            Persisted Incident instance.
        """
        repo = IncidentRepository(db)
        incident = repo.create(
            title=payload.title,
            description=payload.description,
            disaster_type=payload.disaster_type.value,
            severity=payload.severity.value,
            latitude=payload.latitude,
            longitude=payload.longitude,
            reported_by=reporter_id,
            affected_radius_meters=payload.affected_radius_meters,
            estimated_affected_people=payload.estimated_affected_people,
        )

        logger.info(
            "incident_reported",
            incident_id=incident.id,
            type=incident.disaster_type,
            severity=incident.severity,
            lat=incident.latitude,
            lon=incident.longitude,
            reporter_id=reporter_id,
        )
        return incident

    @staticmethod
    def get_incident(db: Session, incident_id: int) -> Incident:
        """
        Retrieve an incident by ID.

        Raises:
            EntityNotFoundException: If no incident with the given ID exists.
        """
        repo = IncidentRepository(db)
        incident = repo.get_by_id(incident_id)
        if incident is None:
            raise EntityNotFoundException("Incident", incident_id)
        return incident

    @staticmethod
    def list_incidents(
        db: Session,
        page: int = 1,
        page_size: int = 50,
        status_filter: str | None = None,
        type_filter: str | None = None,
        severity_filter: str | None = None,
    ) -> tuple[list[Incident], int]:
        """
        Return a paginated list of incidents with optional filters.

        Returns:
            Tuple of (incidents list, total count).
        """
        repo = IncidentRepository(db)
        skip = (page - 1) * page_size
        return repo.get_all(
            skip=skip,
            limit=page_size,
            status_filter=status_filter,
            type_filter=type_filter,
            severity_filter=severity_filter,
        )

    @staticmethod
    def update_incident(
        db: Session,
        incident_id: int,
        payload: IncidentUpdate,
        current_user_id: int,
        current_user_role: str,
    ) -> Incident:
        """
        Apply partial updates to an incident.

        Dispatchers can only update status. Commanders and above can update all fields.

        Raises:
            EntityNotFoundException: If incident not found.
            ForbiddenException: If role is insufficient for the requested change.
        """
        repo = IncidentRepository(db)
        incident = repo.get_by_id(incident_id)
        if incident is None:
            raise EntityNotFoundException("Incident", incident_id)

        updates: dict[str, Any] = {}

        # Build update dict from non-None payload fields
        if payload.title is not None:
            updates["title"] = payload.title.strip()
        if payload.description is not None:
            updates["description"] = payload.description
        if payload.severity is not None:
            updates["severity"] = payload.severity.value
        if payload.status is not None:
            updates["status"] = payload.status.value
        if payload.latitude is not None:
            updates["latitude"] = payload.latitude
        if payload.longitude is not None:
            updates["longitude"] = payload.longitude
        if payload.affected_radius_meters is not None:
            updates["affected_radius_meters"] = payload.affected_radius_meters
        if payload.estimated_affected_people is not None:
            updates["estimated_affected_people"] = payload.estimated_affected_people

        updated = repo.update(incident_id, updates)
        if updated is None:
            raise EntityNotFoundException("Incident", incident_id)

        logger.info(
            "incident_updated",
            incident_id=incident_id,
            updated_fields=list(updates.keys()),
            updated_by=current_user_id,
        )
        return updated

    @staticmethod
    def delete_incident(
        db: Session,
        incident_id: int,
        current_user_role: str,
    ) -> None:
        """
        Hard-delete an incident record.

        Only ADMIN and COMMANDER roles may delete incidents.

        Raises:
            ForbiddenException: If role is insufficient.
            EntityNotFoundException: If incident not found.
        """
        allowed_roles = {"ADMIN", "COMMANDER"}
        if current_user_role.upper() not in allowed_roles:
            raise ForbiddenException("Only ADMIN or COMMANDER can delete incidents.")

        repo = IncidentRepository(db)
        deleted = repo.delete(incident_id)
        if not deleted:
            raise EntityNotFoundException("Incident", incident_id)

        logger.info("incident_deleted", incident_id=incident_id, by_role=current_user_role)

    @staticmethod
    def get_nearest_rescue_team(
        db: Session,
        incident_id: int,
    ) -> dict[str, Any] | None:
        """
        Find the nearest available rescue team to the incident using PostGIS.

        Returns:
            Dict with team details and distance_meters, or None if no teams available.
        """
        from app.modules.resource.models import RescueTeam  # noqa: PLC0415

        repo = IncidentRepository(db)
        incident = repo.get_by_id(incident_id)
        if incident is None:
            raise EntityNotFoundException("Incident", incident_id)

        result = repo.find_nearest_with_model(
            model_class=RescueTeam,
            incident=incident,
            status_filter="AVAILABLE",
        )

        if result is None:
            return None

        team, distance_m = result
        return {
            "team_id": team.id,
            "team_name": team.team_name,
            "vehicle_type": team.vehicle_type,
            "members": team.members,
            "status": team.status,
            "latitude": team.latitude,
            "longitude": team.longitude,
            "distance_meters": round(float(distance_m), 2),
        }

    @staticmethod
    def get_nearby_hospitals(
        db: Session,
        incident_id: int,
        radius_km: float = 10.0,
    ) -> list[dict[str, Any]]:
        """
        Find all hospitals within radius_km of the incident.

        Returns:
            List of hospital dicts sorted by distance.
        """
        from app.modules.hospital.models import Hospital  # noqa: PLC0415

        repo = IncidentRepository(db)
        incident = repo.get_by_id(incident_id)
        if incident is None:
            raise EntityNotFoundException("Incident", incident_id)

        results = repo.find_nearby_with_model(
            model_class=Hospital,
            incident=incident,
            radius_meters=radius_km * 1000,
        )

        return [
            {
                "id": h.id,
                "name": h.name,
                "beds": h.beds,
                "icu_beds": h.icu_beds,
                "oxygen_available": h.oxygen_available,
                "is_operational": h.is_operational,
                "latitude": h.latitude,
                "longitude": h.longitude,
                "distance_meters": round(float(dist), 2),
            }
            for h, dist in results
        ]

    @staticmethod
    def get_nearby_shelters(
        db: Session,
        incident_id: int,
        radius_km: float = 10.0,
    ) -> list[dict[str, Any]]:
        """
        Find all shelters within radius_km of the incident.

        Returns:
            List of shelter dicts sorted by distance.
        """
        from app.modules.resource.models import Shelter  # noqa: PLC0415

        repo = IncidentRepository(db)
        incident = repo.get_by_id(incident_id)
        if incident is None:
            raise EntityNotFoundException("Incident", incident_id)

        results = repo.find_nearby_with_model(
            model_class=Shelter,
            incident=incident,
            radius_meters=radius_km * 1000,
        )

        return [
            {
                "id": s.id,
                "name": s.name,
                "capacity": s.capacity,
                "current_occupancy": s.current_occupancy,
                "available_space": s.capacity - s.current_occupancy,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "distance_meters": round(float(dist), 2),
            }
            for s, dist in results
        ]

    @staticmethod
    async def get_recommended_teams(
        db: Session,
        incident_id: int,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Return ranked rescue team recommendations using SmartDispatchService.
        """
        from app.services.smart_dispatch_service import SmartDispatchService  # noqa: PLC0415
        return await SmartDispatchService.get_recommended_teams(
            db=db, disaster_id=incident_id, limit=limit
        )

