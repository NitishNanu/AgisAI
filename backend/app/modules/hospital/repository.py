"""AegisAI Hospital Module â€” Repository Layer."""

from sqlalchemy.orm import Session

from app.modules.hospital.models import Hospital


class HospitalRepository:
    """Data access layer for the `hospitals` table."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, hospital_id: int) -> Hospital | None:
        """Retrieve hospital by primary key."""
        return self._db.query(Hospital).filter(Hospital.id == hospital_id).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        operational_only: bool = False,
    ) -> tuple[list[Hospital], int]:
        """Return paginated hospitals with optional operational filter."""
        query = self._db.query(Hospital)
        if operational_only:
            query = query.filter(Hospital.is_operational.is_(True))
        total = query.count()
        hospitals = query.order_by(Hospital.name).offset(skip).limit(limit).all()
        return hospitals, total

    def create(self, **kwargs: object) -> Hospital:
        """Create and persist a new hospital record."""
        try:
            from geoalchemy2.elements import WKTElement  # noqa: PLC0415
            lat = kwargs.get("latitude")
            lon = kwargs.get("longitude")
            if lat is not None and lon is not None:
                kwargs["location"] = WKTElement(f"POINT({lon} {lat})", srid=4326)
        except ImportError:
            pass

        hospital = Hospital(**kwargs)
        self._db.add(hospital)
        self._db.commit()
        self._db.refresh(hospital)
        return hospital

    def update(self, hospital_id: int, updates: dict) -> Hospital | None:
        """Apply partial updates to a hospital record."""
        hospital = self.get_by_id(hospital_id)
        if hospital is None:
            return None

        for field, value in updates.items():
            if value is not None and hasattr(hospital, field):
                setattr(hospital, field, value)

        if "latitude" in updates or "longitude" in updates:
            try:
                from geoalchemy2.elements import WKTElement  # noqa: PLC0415
                hospital.location = WKTElement(
                    f"POINT({hospital.longitude} {hospital.latitude})", srid=4326
                )
            except ImportError:
                pass

        self._db.commit()
        self._db.refresh(hospital)
        return hospital

    def delete(self, hospital_id: int) -> bool:
        """Hard-delete a hospital. Returns True if deleted."""
        hospital = self.get_by_id(hospital_id)
        if hospital is None:
            return False
        self._db.delete(hospital)
        self._db.commit()
        return True
