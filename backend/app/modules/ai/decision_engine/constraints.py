"""
AegisAI Decision Engine — Hard & Soft Constraint Engine.

Implements strict domain rules and mathematical validation.
"""

from typing import Protocol

import structlog

from app.modules.ai.schemas import (
    ConstraintEvaluationDTO,
    HospitalStateDTO,
    IncidentStateDTO,
    ResourceStateDTO,
    RoadStateDTO,
)

logger = structlog.get_logger("aegis_ai.decision_engine.constraints")

DISASTER_CAPABILITY_REQUIREMENTS: dict[str, list[str]] = {
    "FIRE": ["FIRE", "EXTRICATION", "WATER_SUPPLY"],
    "FLOOD": ["WATER_RESCUE", "FLOOD_EVACUATION"],
    "HAZMAT": ["HAZMAT", "DECONTAMINATION", "CHEMICAL_CONTAINMENT"],
    "GAS_LEAK": ["HAZMAT", "GAS_DETECTION", "PERIMETER_SECURITY"],
    "EARTHQUAKE": ["SEARCH_RESCUE", "EXTRICATION", "MEDICAL", "TRIAGE"],
    "BUILDING_COLLAPSE": ["SEARCH_RESCUE", "EXTRICATION", "TRAUMA_CARE"],
    "MEDICAL": ["MEDICAL", "ALS", "BLS", "TRIAGE", "TRANSPORT"],
    "EPIDEMIC": ["MEDICAL", "DECONTAMINATION", "TRANSPORT"],
    "TRAFFIC_ACCIDENT": ["EXTRICATION", "MEDICAL", "TRAFFIC_MANAGEMENT"],
    "STORM": ["SEARCH_RESCUE", "WATER_RESCUE", "EMERGENCY_TRANSPORT"],
    "OTHER": ["FIRST_RESPONSE"],
}

DISASTER_PRIMARY_VEHICLES: dict[str, set[str]] = {
    "FIRE": {"FIRE_TRUCK", "HELICOPTER"},
    "FLOOD": {"RESCUE_BOAT", "HELICOPTER", "AMBULANCE"},
    "HAZMAT": {"HAZMAT_UNIT", "FIRE_TRUCK"},
    "GAS_LEAK": {"HAZMAT_UNIT", "FIRE_TRUCK"},
    "EARTHQUAKE": {"FIRE_TRUCK", "AMBULANCE", "POLICE_PATROL", "HELICOPTER", "RECON_DRONE"},
    "BUILDING_COLLAPSE": {"FIRE_TRUCK", "AMBULANCE", "HELICOPTER"},
    "MEDICAL": {"AMBULANCE", "HELICOPTER"},
    "EPIDEMIC": {"AMBULANCE"},
    "TRAFFIC_ACCIDENT": {"AMBULANCE", "FIRE_TRUCK", "POLICE_PATROL"},
    "STORM": {"RESCUE_BOAT", "FIRE_TRUCK", "AMBULANCE", "HELICOPTER"},
    "OTHER": {"AMBULANCE", "FIRE_TRUCK", "POLICE_PATROL", "RESCUE_BOAT"},
}


class Constraint(Protocol):
    """Protocol for candidate evaluation constraints."""

    name: str

    def evaluate(
        self,
        incident: IncidentStateDTO,
        resource: ResourceStateDTO,
        hospital: HospitalStateDTO | None,
        roads: list[RoadStateDTO],
    ) -> tuple[bool, str | None]:
        """Returns (passed, rejection_reason)."""
        ...


class ResourceAvailableConstraint:
    """Hard Constraint: Unit must be currently AVAILABLE and operational."""

    name = "RESOURCE_AVAILABLE"

    def evaluate(
        self,
        incident: IncidentStateDTO,
        resource: ResourceStateDTO,
        hospital: HospitalStateDTO | None,
        roads: list[RoadStateDTO],
    ) -> tuple[bool, str | None]:
        if not resource.availability or resource.status.upper() != "AVAILABLE":
            return False, f"Resource {resource.team_name} is {resource.status} and not available."
        return True, None


class ResourceCapabilityConstraint:
    """Hard Constraint: Resource equipment/type must support the incident requirements."""

    name = "RESOURCE_CAPABILITY"

    def evaluate(
        self,
        incident: IncidentStateDTO,
        resource: ResourceStateDTO,
        hospital: HospitalStateDTO | None,
        roads: list[RoadStateDTO],
    ) -> tuple[bool, str | None]:
        disaster_type = incident.disaster_type.upper()
        v_type = resource.vehicle_type.upper()

        allowed_vehicles = DISASTER_PRIMARY_VEHICLES.get(disaster_type)
        if allowed_vehicles and v_type not in allowed_vehicles:
            return False, f"Vehicle type '{v_type}' lacks required capability for {disaster_type}."

        return True, None


class HospitalCapacityConstraint:
    """Hard Constraint: Assigned hospital must be operational and have beds."""

    name = "HOSPITAL_CAPACITY"

    def evaluate(
        self,
        incident: IncidentStateDTO,
        resource: ResourceStateDTO,
        hospital: HospitalStateDTO | None,
        roads: list[RoadStateDTO],
    ) -> tuple[bool, str | None]:
        if hospital is None:
            return True, None

        if not hospital.is_operational:
            return False, f"Hospital {hospital.name} is non-operational or closed."

        if hospital.available_beds <= 0:
            return False, f"Hospital {hospital.name} has 0 available beds."

        if incident.critical_patients > 0 and hospital.available_icu <= 0:
            crit = incident.critical_patients
            msg = f"Hospital {hospital.name} lacks ICU beds for {crit} patients."
            return False, msg

        return True, None


class EnergyLevelConstraint:
    """Hard Constraint: Resource must have sufficient fuel/battery to execute mission."""

    name = "ENERGY_LEVEL"

    def evaluate(
        self,
        incident: IncidentStateDTO,
        resource: ResourceStateDTO,
        hospital: HospitalStateDTO | None,
        roads: list[RoadStateDTO],
    ) -> tuple[bool, str | None]:
        if resource.fuel_level_percent < 15.0:
            return False, f"Resource fuel is critically low ({resource.fuel_level_percent}% < 15%)."
        if resource.battery_level_percent < 15.0:
            return False, f"Battery is critically low ({resource.battery_level_percent}% < 15%)."
        return True, None


class ConstraintEngine:
    """Orchestrates hard constraint validation for candidate response actions."""

    def __init__(self) -> None:
        self.hard_constraints: list[Constraint] = [
            ResourceAvailableConstraint(),
            ResourceCapabilityConstraint(),
            HospitalCapacityConstraint(),
            EnergyLevelConstraint(),
        ]

    def evaluate_candidate(
        self,
        incident: IncidentStateDTO,
        resource: ResourceStateDTO,
        hospital: HospitalStateDTO | None = None,
        roads: list[RoadStateDTO] | None = None,
    ) -> ConstraintEvaluationDTO:
        """Evaluate all hard constraints against a candidate pair."""
        roads_list = roads or []
        reasons: list[str] = []
        checked: dict[str, bool] = {}
        all_passed = True

        for c in self.hard_constraints:
            passed, reason = c.evaluate(incident, resource, hospital, roads_list)
            checked[c.name] = passed
            if not passed:
                all_passed = False
                if reason:
                    reasons.append(reason)

        return ConstraintEvaluationDTO(
            passed=all_passed,
            rejection_reasons=reasons,
            checked_constraints=checked,
        )
