"""
Unit tests for AI Decision Engine Constraint Verification.
"""

import pytest

from app.modules.ai.decision_engine.constraints import (
    ConstraintEngine,
    EnergyLevelConstraint,
    HospitalCapacityConstraint,
    ResourceAvailableConstraint,
    ResourceCapabilityConstraint,
)
from app.modules.ai.schemas import (
    HospitalStateDTO,
    IncidentStateDTO,
    ResourceStateDTO,
)


@pytest.fixture
def base_incident() -> IncidentStateDTO:
    return IncidentStateDTO(
        incident_id=101,
        title="Downtown Highrise Fire",
        disaster_type="FIRE",
        severity="HIGH",
        latitude=30.7333,
        longitude=76.7794,
        critical_patients=2,
    )


@pytest.fixture
def base_fire_truck() -> ResourceStateDTO:
    return ResourceStateDTO(
        resource_id=1,
        team_name="Fire Engine 1",
        vehicle_type="FIRE_TRUCK",
        availability=True,
        status="AVAILABLE",
        latitude=30.7300,
        longitude=76.7700,
        capabilities=["FIRE", "EXTRICATION", "WATER_SUPPLY"],
        fuel_level_percent=90.0,
        battery_level_percent=100.0,
    )


@pytest.fixture
def base_ambulance() -> ResourceStateDTO:
    return ResourceStateDTO(
        resource_id=2,
        team_name="Medic Ambulance Alpha",
        vehicle_type="AMBULANCE",
        availability=True,
        status="AVAILABLE",
        latitude=30.7350,
        longitude=76.7750,
        capabilities=["MEDICAL", "ALS", "BLS", "TRIAGE"],
        fuel_level_percent=85.0,
        battery_level_percent=100.0,
    )


@pytest.fixture
def base_hospital() -> HospitalStateDTO:
    return HospitalStateDTO(
        hospital_id=1,
        name="Central Trauma Hospital",
        latitude=30.7400,
        longitude=76.7800,
        total_beds=100,
        available_beds=25,
        icu_capacity=20,
        available_icu=5,
        is_operational=True,
    )


def test_resource_available_constraint(
    base_incident: IncidentStateDTO,
    base_fire_truck: ResourceStateDTO,
) -> None:
    constraint = ResourceAvailableConstraint()
    passed, reason = constraint.evaluate(base_incident, base_fire_truck, None, [])
    assert passed is True
    assert reason is None

    busy_truck = base_fire_truck.model_copy(update={"status": "DISPATCHED", "availability": False})
    passed, reason = constraint.evaluate(base_incident, busy_truck, None, [])
    assert passed is False
    assert reason is not None
    assert "not available" in reason


def test_resource_capability_constraint(
    base_incident: IncidentStateDTO,
    base_fire_truck: ResourceStateDTO,
    base_ambulance: ResourceStateDTO,
) -> None:
    constraint = ResourceCapabilityConstraint()

    passed, _ = constraint.evaluate(base_incident, base_fire_truck, None, [])
    assert passed is True

    passed, reason = constraint.evaluate(base_incident, base_ambulance, None, [])
    assert passed is False
    assert reason is not None
    assert "lacks required capability" in reason

    med_incident = base_incident.model_copy(update={"disaster_type": "MEDICAL"})
    passed, _ = constraint.evaluate(med_incident, base_ambulance, None, [])
    assert passed is True


def test_hospital_capacity_constraint(
    base_incident: IncidentStateDTO,
    base_ambulance: ResourceStateDTO,
    base_hospital: HospitalStateDTO,
) -> None:
    constraint = HospitalCapacityConstraint()

    passed, _ = constraint.evaluate(base_incident, base_ambulance, base_hospital, [])
    assert passed is True

    full_icu = base_hospital.model_copy(update={"available_icu": 0})
    passed, reason = constraint.evaluate(base_incident, base_ambulance, full_icu, [])
    assert passed is False
    assert reason is not None
    assert "no available ICU beds" in reason

    closed_hosp = base_hospital.model_copy(update={"is_operational": False})
    passed, reason = constraint.evaluate(base_incident, base_ambulance, closed_hosp, [])
    assert passed is False
    assert reason is not None
    assert "non-operational" in reason


def test_energy_level_constraint(
    base_incident: IncidentStateDTO,
    base_fire_truck: ResourceStateDTO,
) -> None:
    constraint = EnergyLevelConstraint()

    passed, _ = constraint.evaluate(base_incident, base_fire_truck, None, [])
    assert passed is True

    low_fuel = base_fire_truck.model_copy(update={"fuel_level_percent": 10.0})
    passed, reason = constraint.evaluate(base_incident, low_fuel, None, [])
    assert passed is False
    assert reason is not None
    assert "fuel level is critically low" in reason


def test_constraint_engine_aggregate(
    base_incident: IncidentStateDTO,
    base_fire_truck: ResourceStateDTO,
) -> None:
    engine = ConstraintEngine()
    result = engine.evaluate_candidate(base_incident, base_fire_truck)
    assert result.passed is True
    assert len(result.rejection_reasons) == 0
    assert result.checked_constraints["RESOURCE_AVAILABLE"] is True
    assert result.checked_constraints["RESOURCE_CAPABILITY"] is True
