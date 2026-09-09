"""
AegisAI Decision Engine — State Aggregator.

Extracts, cleans, and converts database entities and Digital Twin simulator
state into immutable, typed DTO representations (DecisionState).
Ensures pure mathematical engines receive clean DTOs without direct DB or ORM coupling.
"""

import math
from collections.abc import Sequence
from datetime import datetime, timezone

import structlog
from sqlalchemy.orm import Session

from app.modules.ai.enums import ExecutionMode
from app.modules.ai.schemas import (
    DecisionState,
    HospitalStateDTO,
    IncidentStateDTO,
    ResourceStateDTO,
    RoadStateDTO,
    ShelterStateDTO,
    TrafficStateDTO,
    WeatherStateDTO,
)
from app.modules.hospital.models import Hospital
from app.modules.incident.models import Incident
from app.modules.resource.models import RescueTeam, Shelter
from app.modules.simulation.engine import DigitalTwinEngine

logger = structlog.get_logger("aegis_ai.decision_engine.state")

# Standard capability and equipment mapping by vehicle type
VEHICLE_CAPABILITIES: dict[str, list[str]] = {
    "AMBULANCE": ["MEDICAL", "TRIAGE", "TRANSPORT", "ALS", "BLS", "OXYGEN"],
    "FIRE_TRUCK": ["FIRE", "EXTRICATION", "SEARCH_RESCUE", "HAZMAT_INITIAL", "WATER_SUPPLY"],
    "HAZMAT_UNIT": ["HAZMAT", "DECONTAMINATION", "CHEMICAL_CONTAINMENT", "GAS_DETECTION"],
    "RESCUE_BOAT": ["WATER_RESCUE", "FLOOD_EVACUATION", "FIRST_AID", "LIFE_SAVING"],
    "POLICE_PATROL": [
        "CROWD_CONTROL",
        "TRAFFIC_MANAGEMENT",
        "PERIMETER_SECURITY",
        "FIRST_RESPONSE",
    ],
    "RECON_DRONE": ["AERIAL_SURVEILLANCE", "THERMAL_SCANNING", "DAMAGE_ASSESSMENT"],
    "HELICOPTER": ["AIR_AMBULANCE", "AERIAL_RESCUE", "RAPID_TRANSPORT", "EXTRICATION"],
}

VEHICLE_EQUIPMENT: dict[str, list[str]] = {
    "AMBULANCE": ["Defibrillator", "Ventilator", "Spine Board", "Oxygen Tanks", "Trauma Kit"],
    "FIRE_TRUCK": ["High Pressure Hose", "Hydraulic Jaws", "Thermal Camera", "Foam Nozzle"],
    "HAZMAT_UNIT": ["Level A Suits", "Neutralizing Agents", "Air Sampler", "Decon Shower"],
    "RESCUE_BOAT": ["Outboard Motor", "Inflatable Rafts", "Life Vests", "Water Stretcher"],
    "POLICE_PATROL": ["Barricades", "Sirens", "First Aid Kit", "Radio Relay"],
    "RECON_DRONE": ["4K Optical Camera", "FLIR Thermal Sensor", "GPS Transponder"],
    "HELICOPTER": ["Winch Harness", "Medical Monitor", "Searchlight", "FLIR Gimbal"],
}


class StateAggregator:
    """Aggregates and formats state for the AI Decision Engine."""

    @classmethod
    def build_state_from_db(
        cls,
        db: Session,
        incident_ids: list[int] | None = None,
        execution_mode: ExecutionMode = ExecutionMode.LIVE,
    ) -> DecisionState:
        """
        Build DecisionState from real database entities.
        """
        # 1. Fetch Incidents
        incidents_query = db.query(Incident)
        if incident_ids:
            incidents_query = incidents_query.filter(Incident.id.in_(incident_ids))
        else:
            incidents_query = incidents_query.filter(Incident.status.in_(["ACTIVE", "RESPONDING"]))
        db_incidents: Sequence[Incident] = incidents_query.all()

        incident_dtos: list[IncidentStateDTO] = []
        for inc in db_incidents:
            est_affected = inc.estimated_affected_people or 10
            est_casualties = (
                max(1, int(est_affected * 0.15))
                if inc.severity in ["HIGH", "CRITICAL"]
                else max(0, int(est_affected * 0.05))
            )
            crit_patients = (
                max(0, int(est_casualties * 0.4))
                if inc.severity == "CRITICAL"
                else max(0, int(est_casualties * 0.2))
            )

            incident_dtos.append(
                IncidentStateDTO(
                    incident_id=inc.id,
                    title=inc.title,
                    disaster_type=inc.disaster_type.upper(),
                    severity=inc.severity.upper(),
                    priority=inc.severity.upper(),
                    latitude=inc.latitude,
                    longitude=inc.longitude,
                    affected_radius_meters=inc.affected_radius_meters or 500.0,
                    estimated_affected_people=est_affected,
                    estimated_casualties=est_casualties,
                    critical_patients=crit_patients,
                    status=inc.status.upper(),
                    created_at=inc.created_at,
                )
            )

        # 2. Fetch Resources
        db_teams: Sequence[RescueTeam] = db.query(RescueTeam).all()
        resource_dtos: list[ResourceStateDTO] = []
        for team in db_teams:
            v_type = team.vehicle_type.upper()
            caps = VEHICLE_CAPABILITIES.get(v_type, ["GENERAL_RESCUE"])
            eqs = VEHICLE_EQUIPMENT.get(v_type, ["Standard Emergency Gear"])
            is_avail = team.status.upper() == "AVAILABLE"

            resource_dtos.append(
                ResourceStateDTO(
                    resource_id=team.id,
                    team_name=team.team_name,
                    vehicle_type=v_type,
                    members=team.members,
                    status=team.status.upper(),
                    availability=is_avail,
                    latitude=team.latitude,
                    longitude=team.longitude,
                    equipment=eqs,
                    capabilities=caps,
                    fuel_level_percent=95.0 if is_avail else 70.0,
                    battery_level_percent=100.0,
                    capacity=max(2, team.members * 2),
                    current_mission_id=None,
                )
            )

        # 3. Fetch Hospitals
        db_hospitals: Sequence[Hospital] = (
            db.query(Hospital).filter(Hospital.is_operational.is_(True)).all()
        )
        hospital_dtos: list[HospitalStateDTO] = []
        for hosp in db_hospitals:
            avail_beds = max(0, hosp.beds - int(hosp.beds * 0.75))
            avail_icu = max(0, hosp.icu_beds - int(hosp.icu_beds * 0.70))
            load_pct = round(((hosp.beds - avail_beds) / max(1, hosp.beds)) * 100.0, 1)

            hospital_dtos.append(
                HospitalStateDTO(
                    hospital_id=hosp.id,
                    name=hosp.name,
                    latitude=hosp.latitude,
                    longitude=hosp.longitude,
                    total_beds=hosp.beds,
                    available_beds=avail_beds,
                    icu_capacity=hosp.icu_beds,
                    available_icu=avail_icu,
                    oxygen_available=hosp.oxygen_available,
                    blood_bank_available=hosp.blood_bank_available,
                    is_operational=hosp.is_operational,
                    current_load_percent=load_pct,
                )
            )

        # 4. Fetch Shelters
        db_shelters: Sequence[Shelter] = db.query(Shelter).all()
        shelter_dtos: list[ShelterStateDTO] = []
        for sh in db_shelters:
            avail = max(0, sh.capacity - sh.current_occupancy)
            shelter_dtos.append(
                ShelterStateDTO(
                    shelter_id=sh.id,
                    name=sh.name,
                    latitude=sh.latitude,
                    longitude=sh.longitude,
                    capacity=sh.capacity,
                    current_occupancy=sh.current_occupancy,
                    available_space=avail,
                    is_open=avail > 0,
                )
            )

        # 5. Extract environment from Digital Twin simulator if active
        dt_engine = DigitalTwinEngine()
        weather_dto = WeatherStateDTO(
            condition=dt_engine.weather.condition,
            temperature_celsius=dt_engine.weather.temperature_celsius,
            wind_speed_kmh=dt_engine.weather.wind_speed_kmh,
            humidity_percent=dt_engine.weather.humidity_percent,
            visibility_km=dt_engine.weather.visibility_km,
            severity="NORMAL" if dt_engine.weather.condition == "CLEAR" else "ADVERSE",
        )

        traffic_dto = TrafficStateDTO(
            road_congestion_factor=dt_engine.traffic.road_congestion_factor,
            average_speed_kmh=dt_engine.traffic.average_speed_kmh,
            blocked_roads_count=dt_engine.traffic.blocked_roads_count,
        )

        road_dtos: list[RoadStateDTO] = [
            RoadStateDTO(
                road_id=r.id,
                name=r.name,
                start_latitude=r.start_latitude,
                start_longitude=r.start_longitude,
                end_latitude=r.end_latitude,
                end_longitude=r.end_longitude,
                length_km=r.length_km,
                congestion_factor=r.congestion_factor,
                is_blocked=r.is_blocked,
                blocked_reason=r.blocked_reason,
            )
            for r in dt_engine.roads
        ]

        state = DecisionState(
            incidents=incident_dtos,
            resources=resource_dtos,
            hospitals=hospital_dtos,
            shelters=shelter_dtos,
            roads=road_dtos,
            weather=weather_dto,
            traffic=traffic_dto,
            execution_mode=execution_mode,
            timestamp=datetime.now(timezone.utc),
        )

        logger.info(
            "decision_state_built_from_db",
            incidents_count=len(state.incidents),
            resources_count=len(state.resources),
            hospitals_count=len(state.hospitals),
        )
        return state

    @classmethod
    def build_state_from_simulation(
        cls,
        db: Session,
        simulation_id: str,
        execution_mode: ExecutionMode = ExecutionMode.SIMULATION,
    ) -> DecisionState:
        """
        Build DecisionState augmented with real-time Digital Twin simulation entity metrics.
        """
        state = cls.build_state_from_db(db=db, execution_mode=execution_mode)
        dt_engine = DigitalTwinEngine()

        # Augment casualties and affected counts from actual citizen agents
        updated_incidents: list[IncidentStateDTO] = []
        for inc in state.incidents:
            endangered = 0
            injured = 0
            for citizen in dt_engine.citizens:
                d = cls._haversine(inc.latitude, inc.longitude, citizen.latitude, citizen.longitude)
                if d <= (inc.affected_radius_meters / 1000.0):
                    if citizen.status.value in ["ENDANGERED", "EVACUATING"]:
                        endangered += 1
                    elif citizen.status.value == "INJURED":
                        injured += 1

            if endangered > 0 or injured > 0:
                updated_incidents.append(
                    IncidentStateDTO(
                        incident_id=inc.incident_id,
                        title=inc.title,
                        disaster_type=inc.disaster_type,
                        severity=inc.severity,
                        priority=inc.priority,
                        latitude=inc.latitude,
                        longitude=inc.longitude,
                        affected_radius_meters=inc.affected_radius_meters,
                        estimated_affected_people=max(
                            inc.estimated_affected_people, endangered + injured
                        ),
                        estimated_casualties=max(inc.estimated_casualties, injured),
                        critical_patients=max(inc.critical_patients, int(injured * 0.5)),
                        status=inc.status,
                        created_at=inc.created_at,
                    )
                )
            else:
                updated_incidents.append(inc)

        return DecisionState(
            incidents=updated_incidents,
            resources=state.resources,
            hospitals=state.hospitals,
            shelters=state.shelters,
            roads=state.roads,
            weather=state.weather,
            traffic=state.traffic,
            simulation_id=simulation_id,
            execution_mode=execution_mode,
            timestamp=datetime.now(timezone.utc),
        )

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        )
        return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
