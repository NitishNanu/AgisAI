"""
AegisAI AI Module — Pydantic v2 Schemas and DTOs.

Defines all typed data transfer objects for the AI Decision Intelligence layer.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.modules.ai.enums import (
    DecisionPriority,
    DecisionStatus,
    DecisionType,
    ExecutionMode,
    FeedbackType,
    PolicyType,
)

# -------------------------------------------------------------------------
# State DTOs (Immutable snapshot representations for the Decision Engine)
# -------------------------------------------------------------------------


class IncidentStateDTO(BaseModel):
    """Immutable snapshot of an emergency incident."""

    model_config = ConfigDict(frozen=True)

    incident_id: int
    title: str = ""
    disaster_type: str
    severity: str
    priority: str = "MEDIUM"
    latitude: float
    longitude: float
    affected_radius_meters: float = 0.0
    estimated_affected_people: int = 0
    estimated_casualties: int = 0
    critical_patients: int = 0
    status: str = "ACTIVE"
    created_at: datetime | None = None


class ResourceStateDTO(BaseModel):
    """Immutable snapshot of a mobile response unit."""

    model_config = ConfigDict(frozen=True)

    resource_id: int
    team_name: str
    vehicle_type: str
    members: int = 1
    status: str = "AVAILABLE"
    availability: bool = True
    latitude: float
    longitude: float
    equipment: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    fuel_level_percent: float = 100.0
    battery_level_percent: float = 100.0
    capacity: int = 4
    current_mission_id: int | None = None


class HospitalStateDTO(BaseModel):
    """Immutable snapshot of a medical facility."""

    model_config = ConfigDict(frozen=True)

    hospital_id: int
    name: str
    latitude: float
    longitude: float
    total_beds: int = 0
    available_beds: int = 0
    icu_capacity: int = 0
    available_icu: int = 0
    oxygen_available: bool = True
    blood_bank_available: bool = False
    is_operational: bool = True
    current_load_percent: float = 0.0


class ShelterStateDTO(BaseModel):
    """Immutable snapshot of a refuge shelter."""

    model_config = ConfigDict(frozen=True)

    shelter_id: int
    name: str
    latitude: float
    longitude: float
    capacity: int
    current_occupancy: int
    available_space: int
    is_open: bool = True


class RoadStateDTO(BaseModel):
    """Immutable snapshot of a road network segment."""

    model_config = ConfigDict(frozen=True)

    road_id: int
    name: str
    start_latitude: float
    start_longitude: float
    end_latitude: float
    end_longitude: float
    length_km: float = 1.0
    congestion_factor: float = 1.0
    is_blocked: bool = False
    blocked_reason: str | None = None


class WeatherStateDTO(BaseModel):
    """Immutable snapshot of environmental conditions."""

    model_config = ConfigDict(frozen=True)

    condition: str = "CLEAR"
    temperature_celsius: float = 22.0
    rainfall_mm: float = 0.0
    wind_speed_kmh: float = 10.0
    wind_direction_degrees: float = 180.0
    humidity_percent: float = 60.0
    visibility_km: float = 10.0
    severity: str = "NORMAL"


class TrafficStateDTO(BaseModel):
    """Immutable snapshot of city-wide traffic conditions."""

    model_config = ConfigDict(frozen=True)

    road_congestion_factor: float = 1.0
    average_speed_kmh: float = 45.0
    blocked_roads_count: int = 0


class DecisionState(BaseModel):
    """Complete consolidated state snapshot passed into AI decision policies."""

    model_config = ConfigDict(frozen=True)

    incidents: list[IncidentStateDTO] = Field(default_factory=list)
    resources: list[ResourceStateDTO] = Field(default_factory=list)
    hospitals: list[HospitalStateDTO] = Field(default_factory=list)
    shelters: list[ShelterStateDTO] = Field(default_factory=list)
    roads: list[RoadStateDTO] = Field(default_factory=list)
    weather: WeatherStateDTO = Field(default_factory=WeatherStateDTO)
    traffic: TrafficStateDTO = Field(default_factory=TrafficStateDTO)
    simulation_id: str | None = None
    execution_mode: ExecutionMode = ExecutionMode.LIVE
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# -------------------------------------------------------------------------
# Candidate & Scoring DTOs
# -------------------------------------------------------------------------


class ConstraintEvaluationDTO(BaseModel):
    """Details of hard constraints evaluated for a candidate."""

    passed: bool
    rejection_reasons: list[str] = Field(default_factory=list)
    checked_constraints: dict[str, bool] = Field(default_factory=dict)


class ScoringBreakdownDTO(BaseModel):
    """Transparent normalized scoring breakdown."""

    eta_score: float = 0.0
    distance_score: float = 0.0
    capability_score: float = 0.0
    availability_score: float = 0.0
    hospital_capacity_score: float = 0.0
    risk_score: float = 0.0
    raw_eta_minutes: float = 0.0
    raw_distance_km: float = 0.0
    total_score: float = 0.0


class DecisionCandidateDTO(BaseModel):
    """Evaluated action candidate for an incident."""

    resource_id: int
    resource_name: str
    vehicle_type: str
    incident_id: int
    hospital_id: int | None = None
    hospital_name: str | None = None
    eta_minutes: float
    distance_km: float
    route_geometry: Any = None
    suitability: float = 0.0
    constraints_passed: bool = True
    constraint_evaluation: ConstraintEvaluationDTO = Field(
        default_factory=lambda: ConstraintEvaluationDTO(passed=True)
    )
    scoring_breakdown: ScoringBreakdownDTO = Field(default_factory=ScoringBreakdownDTO)
    rejection_reason: str | None = None


class DispatchScoringPolicyConfig(BaseModel):
    """Configurable weights for multi-criteria candidate scoring."""

    eta_weight: float = Field(default=0.30, ge=0.0, le=1.0)
    distance_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    capability_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    availability_weight: float = Field(default=0.15, ge=0.0, le=1.0)
    hospital_capacity_weight: float = Field(default=0.10, ge=0.0, le=1.0)
    risk_weight: float = Field(default=0.05, ge=0.0, le=1.0)


# -------------------------------------------------------------------------
# Decision API Requests & Responses
# -------------------------------------------------------------------------


class AIDecisionCreateRequest(BaseModel):
    """Request payload to trigger decision generation."""

    policy_type: PolicyType = Field(default=PolicyType.OPTIMIZED)
    incident_ids: list[int] | None = Field(
        default=None,
        description="Optional list of incident IDs. If omitted, all active are evaluated.",
    )
    simulation_id: str | None = None
    execution_mode: ExecutionMode = Field(default=ExecutionMode.LIVE)
    custom_weights: DispatchScoringPolicyConfig | None = None
    generate_llm_explanation: bool = Field(
        default=True,
        description="Whether to run the Ollama explanation provider.",
    )


class AIDecisionActionDTO(BaseModel):
    """Action payload embedded in an AI decision."""

    incident_id: int
    resource_id: int
    resource_name: str | None = None
    vehicle_type: str | None = None
    destination_hospital_id: int | None = None
    destination_hospital_name: str | None = None
    estimated_arrival_minutes: float | None = None
    distance_km: float | None = None
    route_geometry: Any = None
    recommended_notes: str | None = None


class AlternativeCandidateDTO(BaseModel):
    """Summary of a rejected or secondary candidate for explainability."""

    resource_id: int
    resource_name: str
    score: float
    eta_minutes: float
    distance_km: float
    rejection_reason: str | None = None


class AIDecisionResponse(BaseModel):
    """Complete AI decision response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    decision_uuid: str
    simulation_id: str | None = None
    incident_id: int | None = None
    decision_type: DecisionType
    action: AIDecisionActionDTO
    resource_id: int | None = None
    destination_id: int | None = None
    priority: DecisionPriority
    score: float
    confidence: float
    reasoning: list[str]
    constraints: dict[str, Any]
    expected_impact: dict[str, Any]
    alternatives: list[AlternativeCandidateDTO]
    status: DecisionStatus
    policy_name: str
    policy_version: str
    model_name: str
    model_version: str
    approved_by: int | None = None
    approved_at: datetime | None = None
    executed_at: datetime | None = None
    rejection_reason: str | None = None
    modification_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class AIDecisionApproveRequest(BaseModel):
    """Request payload to approve an AI decision."""

    notes: str | None = Field(default=None, description="Optional commander approval notes")
    auto_execute: bool = Field(
        default=True,
        description="If true, immediately invokes AssignmentService to dispatch unit.",
    )


class AIDecisionRejectRequest(BaseModel):
    """Request payload to reject an AI decision."""

    rejection_reason: str = Field(..., min_length=3, description="Mandatory reason for rejection")


class AIDecisionModifyRequest(BaseModel):
    """Request payload to modify an AI decision before approval."""

    override_resource_id: int | None = None
    override_hospital_id: int | None = None
    modification_notes: str = Field(..., min_length=3, description="Description of manual changes")
    auto_execute: bool = Field(default=False)


class AIDecisionFeedbackRequest(BaseModel):
    """Request payload to record commander feedback or mission outcome."""

    feedback_type: FeedbackType
    actual_outcome: dict[str, Any] = Field(
        default_factory=dict,
        description="Observed outcome metrics (e.g., actual_response_time, success_rate)",
    )
    comments: str | None = None


# -------------------------------------------------------------------------
# Explanation, Benchmarking & What-If
# -------------------------------------------------------------------------


class LLMExplanationResponse(BaseModel):
    """Tactical briefing narrative generated by the explainability layer."""

    summary: str
    tactical_briefing: str
    reasons: list[str]
    rejected_alternatives_summary: str
    operational_risks: list[str]
    recommended_next_steps: list[str]
    model_used: str
    is_fallback: bool = False
    latency_ms: float = 0.0


class StrategyBenchmarkMetric(BaseModel):
    """Comparative performance metrics for a decision policy."""

    policy_type: PolicyType
    decisions_generated_count: int
    assigned_incidents_count: int
    unassigned_incidents_count: int
    average_response_time_minutes: float
    max_response_time_minutes: float
    total_travel_distance_km: float
    average_score: float
    average_confidence: float
    resource_utilization_rate: float
    estimated_casualty_risk_reduction_percent: float
    solver_latency_ms: float


class BenchmarkRequest(BaseModel):
    """Request payload to run policy comparison."""

    policies_to_compare: list[PolicyType] = Field(
        default=[
            PolicyType.BASELINE,
            PolicyType.HEURISTIC,
            PolicyType.OPTIMIZED,
            PolicyType.ML_ASSISTED,
        ]
    )
    incident_ids: list[int] | None = None


class BenchmarkResponse(BaseModel):
    """Benchmark comparative results across decision policies."""

    evaluated_at: datetime
    incidents_count: int
    available_resources_count: int
    results: list[StrategyBenchmarkMetric]
    recommended_policy: PolicyType
    recommendation_rationale: str


class WhatIfDecisionRequest(BaseModel):
    """Request payload to simulate what-if hypothetical conditions."""

    simulation_id: str | None = None
    hypothetical_blocked_roads: list[int] = Field(default_factory=list)
    hypothetical_disabled_hospitals: list[int] = Field(default_factory=list)
    hypothetical_severe_weather: str | None = None
    policy_type: PolicyType = PolicyType.OPTIMIZED


class WhatIfDecisionResponse(BaseModel):
    """Comparison of baseline vs hypothetical what-if scenario decisions."""

    scenario_name: str
    baseline_decisions: list[AIDecisionResponse]
    what_if_decisions: list[AIDecisionResponse]
    impact_analysis: dict[str, Any]
