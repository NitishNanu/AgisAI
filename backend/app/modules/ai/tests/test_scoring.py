"""
Unit tests for AI Decision Engine Scoring & Normalization.
"""

from app.modules.ai.decision_engine.scoring import ScoringEngine
from app.modules.ai.schemas import (
    DispatchScoringPolicyConfig,
    HospitalStateDTO,
    IncidentStateDTO,
    ResourceStateDTO,
    WeatherStateDTO,
)


def test_scoring_normalization_and_weights() -> None:
    config = DispatchScoringPolicyConfig(
        eta_weight=0.30,
        distance_weight=0.20,
        capability_weight=0.20,
        availability_weight=0.15,
        hospital_capacity_weight=0.10,
        risk_weight=0.05,
    )
    engine = ScoringEngine(config)

    incident = IncidentStateDTO(
        incident_id=1,
        disaster_type="MEDICAL",
        severity="HIGH",
        latitude=30.73,
        longitude=76.77,
        critical_patients=1,
    )

    resource = ResourceStateDTO(
        resource_id=1,
        team_name="Ambulance A1",
        vehicle_type="AMBULANCE",
        availability=True,
        status="AVAILABLE",
        latitude=30.72,
        longitude=76.76,
        capabilities=["MEDICAL", "ALS", "BLS", "TRIAGE", "TRANSPORT"],
        fuel_level_percent=100.0,
    )

    hospital = HospitalStateDTO(
        hospital_id=1,
        name="Apollo Hospital",
        latitude=30.74,
        longitude=76.78,
        total_beds=50,
        available_beds=20,
        icu_capacity=10,
        available_icu=5,
        is_operational=True,
    )

    weather = WeatherStateDTO(condition="CLEAR", visibility_km=10.0)

    # 1. Fast ETA & Short distance should produce high score
    score_fast, breakdown_fast, conf_fast = engine.calculate_score(
        incident=incident,
        resource=resource,
        eta_minutes=3.0,
        distance_km=1.5,
        hospital=hospital,
        weather=weather,
    )

    assert 0.80 <= score_fast <= 1.0
    assert 0.80 <= conf_fast <= 1.0
    assert breakdown_fast.eta_score > 0.85
    assert breakdown_fast.distance_score > 0.90

    # 2. Slow ETA & Long distance should produce lower score
    score_slow, breakdown_slow, conf_slow = engine.calculate_score(
        incident=incident,
        resource=resource,
        eta_minutes=25.0,
        distance_km=20.0,
        hospital=hospital,
        weather=weather,
    )

    assert score_slow < score_fast
    assert conf_slow < conf_fast
    assert breakdown_slow.eta_score < breakdown_fast.eta_score
    assert breakdown_slow.distance_score < breakdown_fast.distance_score


def test_weather_penalty_in_risk_score() -> None:
    engine = ScoringEngine()

    incident = IncidentStateDTO(
        incident_id=1,
        disaster_type="FIRE",
        severity="MEDIUM",
        latitude=30.73,
        longitude=76.77,
    )
    resource = ResourceStateDTO(
        resource_id=1,
        team_name="Engine 1",
        vehicle_type="FIRE_TRUCK",
        availability=True,
        status="AVAILABLE",
        latitude=30.72,
        longitude=76.76,
        capabilities=["FIRE", "EXTRICATION"],
    )

    clear_weather = WeatherStateDTO(condition="CLEAR", visibility_km=10.0)
    storm_weather = WeatherStateDTO(condition="STORM", visibility_km=1.5)

    _, clear_breakdown, _ = engine.calculate_score(
        incident=incident,
        resource=resource,
        eta_minutes=5.0,
        distance_km=3.0,
        weather=clear_weather,
    )

    _, storm_breakdown, _ = engine.calculate_score(
        incident=incident,
        resource=resource,
        eta_minutes=5.0,
        distance_km=3.0,
        weather=storm_weather,
    )

    assert clear_breakdown.risk_score > storm_breakdown.risk_score
