"""
AegisAI Incident Module â€” Repository Layer.

Encapsulates all database access for incidents. Uses PostGIS spatial
functions for geospatial proximity queries.
"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.incident.enums import IncidentStatus
from app.modules.incident.models import Incident


class IncidentRepository:
    """
    Data access layer for the `incidents` table.

    Geospatial queries use PostGIS functions (ST_Distance, ST_DWithin)
    via SQLAlchemy's func interface.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, incident_id: int) -> Incident | None:
        """Retrieve a single incident by primary key."""
        return self._db.query(Incident).filter(Incident.id == incident_id).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status_filter: str | None = None,
        type_filter: str | None = None,
        severity_filter: str | None = None,
    ) -> tuple[list[Incident], int]:
        """
        Retrieve paginated incidents with optional filters.

        Args:
            skip: Number of records to skip.
            limit: Maximum records to return.
            status_filter: Filter by incident status.
            type_filter: Filter by disaster type.
            severity_filter: Filter by severity level.

        Returns:
            Tuple of (list of Incident, total count).
        """
        query = self._db.query(Incident)

        if status_filter:
            query = query.filter(Incident.status == status_filter.upper())
        if type_filter:
            query = query.filter(Incident.disaster_type == type_filter.upper())
        if severity_filter:
            query = query.filter(Incident.severity == severity_filter.upper())

        total = query.count()
        incidents = (
            query.order_by(Incident.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return incidents, total

    def get_active(self) -> list[Incident]:
        """Return all incidents with ACTIVE status."""
        return (
            self._db.query(Incident)
            .filter(Incident.status == IncidentStatus.ACTIVE.value)
            .order_by(Incident.created_at.desc())
            .all()
        )

    def create(
        self,
        title: str,
        description: str | None,
        disaster_type: str,
        severity: str,
        latitude: float,
        longitude: float,
        reported_by: int,
        affected_radius_meters: float | None = None,
        estimated_affected_people: int | None = None,
    ) -> Incident:
        """
        Persist a new incident record with PostGIS location point.

        The `location` Geography column is populated from lat/lon using
        WKTElement for PostGIS compatibility.
        """
        try:
            from geoalchemy2.elements import WKTElement  # noqa: PLC0415

            location = WKTElement(f"POINT({longitude} {latitude})", srid=4326)
        except ImportError:
            location = None  # Graceful degradation for test environments

        incident = Incident(
            title=title,
            description=description,
            disaster_type=disaster_type.upper(),
            severity=severity.upper(),
            status=IncidentStatus.ACTIVE.value,
            latitude=latitude,
            longitude=longitude,
            location=location,
            reported_by=reported_by,
            affected_radius_meters=affected_radius_meters,
            estimated_affected_people=estimated_affected_people,
        )
        self._db.add(incident)
        self._db.commit()
        self._db.refresh(incident)
        return incident

    def update(self, incident_id: int, updates: dict) -> Incident | None:
        """
        Apply a partial update to an incident.

        Args:
            incident_id: Target incident primary key.
            updates: Dictionary of field names to new values.

        Returns:
            Updated Incident or None if not found.
        """
        incident = self.get_by_id(incident_id)
        if incident is None:
            return None

        for field, value in updates.items():
            if value is not None and hasattr(incident, field):
                setattr(incident, field, value)

        # Update PostGIS location if coordinates changed
        if "latitude" in updates or "longitude" in updates:
            try:
                from geoalchemy2.elements import WKTElement  # noqa: PLC0415

                incident.location = WKTElement(
                    f"POINT({incident.longitude} {incident.latitude})", srid=4326
                )
            except ImportError:
                pass

        self._db.commit()
        self._db.refresh(incident)
        return incident

    def delete(self, incident_id: int) -> bool:
        """
        Hard-delete an incident record.

        Returns:
            True if deleted, False if not found.
        """
        incident = self.get_by_id(incident_id)
        if incident is None:
            return False
        self._db.delete(incident)
        self._db.commit()
        return True

    def find_nearby_with_model(
        self,
        model_class: type,
        incident: Incident,
        radius_meters: float,
        limit: int = 20,
    ) -> list[tuple]:
        """
        Generic PostGIS proximity query against any model with a `location` column.

        Args:
            model_class: SQLAlchemy ORM model class with `location` attribute.
            incident: Source incident for the origin point.
            radius_meters: Search radius in meters.
            limit: Maximum results.

        Returns:
            List of (model_instance, distance_meters) tuples ordered by distance.
        """
        if incident.location is None:
            return []

        distance_expr = func.ST_Distance(model_class.location, incident.location)

        return (
            self._db.query(model_class, distance_expr.label("distance_meters"))
            .filter(
                func.ST_DWithin(model_class.location, incident.location, radius_meters)
            )
            .order_by(distance_expr)
            .limit(limit)
            .all()
        )

    def find_nearest_with_model(
        self,
        model_class: type,
        incident: Incident,
        status_filter: str | None = None,
    ) -> tuple | None:
        """
        Find the single nearest entity of a given model to an incident.

        Args:
            model_class: ORM model class with `location` column.
            incident: Source incident.
            status_filter: If provided, filter by model's `status` column.

        Returns:
            (model_instance, distance_meters) tuple or None.
        """
        if incident.location is None:
            return None

        distance_expr = func.ST_Distance(model_class.location, incident.location)
        query = self._db.query(model_class, distance_expr.label("distance_meters"))

        if status_filter and hasattr(model_class, "status"):
            query = query.filter(model_class.status == status_filter)

        return query.order_by(distance_expr).first()
