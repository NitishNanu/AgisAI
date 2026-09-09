"""
AegisAI Prediction Module — Pydantic v2 Schemas and DTOs.

Covers all AI/ML API contracts, time-horizon forecasting models (+5m, +15m, +30m, +60m),
predictive alerts, and the unified command-center predictive dashboard.
Compatible with Python 3.10.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# -------------------------------------------------------------------------
# Horizon Forecasting DTOs
# -------------------------------------------------------------------------


class CasualtyHorizonForecast(BaseModel):
    """Casualty forecast at a specific time horizon."""

    horizon_minutes: int = Field(..., description="Forecast horizon in minutes: 5, 15, 30, 60")
    expected_casualties: int = Field(..., ge=0)
    critical_patients: int = Field(..., ge=0)
    injured: int = Field(..., ge=0)
    fatalities: int = Field(..., ge=0)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class CasualtyForecastDTO(BaseModel):
    """Consolidated casualty and patient load forecast."""

    current_casualties: int = 0
    current_critical: int = 0
    current_injured: int = 0
    current_fatalities: int = 0
    forecast: list[CasualtyHorizonForecast] = Field(default_factory=list)
    trend_summary: str = "STABLE"


class HospitalHorizonLoad(BaseModel):
    """Projected hospital capacity status at a time horizon."""

    horizon_minutes: int
    projected_bed_occupancy_percent: float = Field(..., ge=0.0)
    projected_icu_occupancy_percent: float = Field(..., ge=0.0)
    expected_admissions: int = 0
    status: str = "NORMAL"  # NORMAL | ELEVATED | WARNING | CRITICAL | OVERLOAD
    is_overloaded: bool = False


class HospitalLoadForecastDTO(BaseModel):
    """Predictive capacity and admission forecast for a medical facility."""

    hospital_id: int
    name: str
    latitude: float
    longitude: float
    total_beds: int
    available_beds: int
    icu_capacity: int
    available_icu: int
    current_bed_occupancy_percent: float
    current_icu_occupancy_percent: float
    forecast: list[HospitalHorizonLoad] = Field(default_factory=list)
    expected_overload_minutes: float | None = None
    status: str = "NORMAL"


class ResourceHorizonDemand(BaseModel):
    """Projected resource requirement at a time horizon."""

    horizon_minutes: int
    required_count: int = 0
    projected_shortage: int = 0
    utilization_percent: float = 0.0
    urgency_level: str = "LOW"  # LOW | MEDIUM | HIGH | CRITICAL


class ResourceDemandForecastDTO(BaseModel):
    """Predictive fleet requirement and shortage forecast."""

    resource_type: str  # AMBULANCE | FIRE_TRUCK | RESCUE_BOAT | POLICE_PATROL | DRONE
    current_available: int
    current_deployed: int
    forecast: list[ResourceHorizonDemand] = Field(default_factory=list)
    shortage_risk_level: str = "LOW"


class DisasterRiskForecastDTO(BaseModel):
    """Predictive hazard severity and spatial risk forecast."""

    incident_id: int
    disaster_type: str
    severity: str
    latitude: float
    longitude: float
    risk_level: str = "MODERATE"  # LOW | MODERATE | HIGH | CRITICAL
    risk_score: float = Field(..., ge=0.0, le=1.0)
    trend: str = "STABLE"  # INCREASING | STABLE | DECREASING
    spread_radius_forecast: dict[str, float] = Field(default_factory=dict)
    confidence: float | None = None
    contributing_factors: list[str] = Field(default_factory=list)


class FireSpreadZoneDTO(BaseModel):
    """Concentric fire propagation envelope."""

    horizon_minutes: int
    radius_meters: float
    risk_level: str
    estimated_population_impact: int


class FireSpreadForecastDTO(BaseModel):
    """Multi-horizon fire propagation projection."""

    incident_id: int
    disaster_type: str
    center_latitude: float
    center_longitude: float
    spread_direction_degrees: float
    spread_velocity_kmh: float
    zones: list[FireSpreadZoneDTO] = Field(default_factory=list)


class FloodRiskForecastDTO(BaseModel):
    """Flood inundation and evacuation risk projection."""

    incident_id: int
    affected_area_sq_km: float
    water_level_meters: float
    road_closure_risk: str
    buildings_at_risk_count: int
    evacuation_urgency: str


class PredictiveAlertDTO(BaseModel):
    """Proactive operational alert with structured explainability."""

    id: str
    type: str  # OVERLOAD | SHORTAGE | SPREAD | CASUALTY_SURGE
    severity: str  # INFO | WARNING | HIGH | CRITICAL
    title: str
    message: str
    timestamp: datetime
    source: str = "PREDICTIVE_ENGINE"
    related_entity_id: int | None = None
    related_entity_name: str | None = None
    confidence: float | None = None
    explanation: str
    recommended_action: str


class ModelMetadataDTO(BaseModel):
    """Observability and provenance metadata for active prediction models."""

    model_name: str = "AegisAI-PredictiveEngine-v1"
    model_version: str = "1.2.0"
    prediction_timestamp: datetime
    data_timestamp: datetime
    prediction_source: str = (
        "SIMULATION"  # SIMULATION | ML_MODEL | AI_MODEL | HISTORICAL | FALLBACK
    )
    confidence_calibrated: bool = True


class PredictiveDashboardResponse(BaseModel):
    """Consolidated command-center predictive dashboard payload."""

    generated_at: datetime
    simulation_id: str | None = None
    prediction_source: str = "SIMULATION"
    casualties: CasualtyForecastDTO
    hospitals: list[HospitalLoadForecastDTO] = Field(default_factory=list)
    resources: list[ResourceDemandForecastDTO] = Field(default_factory=list)
    disaster_risk: list[DisasterRiskForecastDTO] = Field(default_factory=list)
    fire_spread: list[FireSpreadForecastDTO] = Field(default_factory=list)
    flood_risk: list[FloodRiskForecastDTO] = Field(default_factory=list)
    alerts: list[PredictiveAlertDTO] = Field(default_factory=list)
    model_metadata: ModelMetadataDTO


# -------------------------------------------------------------------------
# Prediction Records & History
# -------------------------------------------------------------------------


class PredictionOutcomeRecordRequest(BaseModel):
    """Request to record real-world observed outcome for error tracking."""

    actual_value: dict[str, Any]
    error_rate: float | None = None


class PredictionRecordResponse(BaseModel):
    """Persisted prediction record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    prediction_type: str
    simulation_id: str | None = None
    incident_id: int | None = None
    model_name: str
    model_version: str
    forecast_horizon_minutes: int
    predicted_value: dict[str, Any]
    actual_value: dict[str, Any] | None = None
    error_rate: float | None = None
    confidence: float | None = None
    prediction_source: str
    created_at: datetime


# -------------------------------------------------------------------------
# Legacy / Existing Spread & Optimization Contracts
# -------------------------------------------------------------------------


class AffectedZone(BaseModel):
    """A concentric risk zone around an incident epicenter."""

    radius_meters: float = Field(..., description="Outer radius of this zone in meters")
    risk_level: str = Field(..., description="HIGH | MEDIUM | LOW")
    estimated_impacted_population: int = Field(..., ge=0)
    recommended_action: str = Field(..., description="Operational guidance for responders")


class DisasterPredictionRequest(BaseModel):
    """Request for disaster spread prediction on an existing incident."""

    incident_id: int = Field(..., description="ID of the incident to predict spread for")
    current_affected_radius_meters: float = Field(
        default=500.0, ge=0, description="Current radius of effect in meters"
    )
    time_horizon_hours: float = Field(
        default=6.0,
        ge=0.5,
        le=72.0,
        description="How many hours ahead to predict (0.5–72h)",
    )
    weather_multiplier: float = Field(
        default=1.0,
        ge=0.1,
        le=5.0,
        description="Environmental severity multiplier (1.0 = normal conditions)",
    )


class PredictionResponse(BaseModel):
    """AI-enhanced disaster spread prediction result."""

    incident_id: int
    time_horizon_hours: float
    predicted_radius_meters: float = Field(..., description="Predicted outer radius in meters")
    estimated_casualties: int = Field(..., ge=0)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    explanation: str = Field(..., description="LLM-generated XAI explanation of the prediction")
    ai_metadata: dict[str, Any] = Field(default_factory=dict)


class DisasterSpreadPredictionRequest(BaseModel):
    """Legacy disaster spread prediction request schema."""

    disaster_id: int
    disaster_type: str = Field(..., description="FIRE | FLOOD | EARTHQUAKE | GAS_LEAK | WILDFIRE")
    severity: str = Field(..., description="LOW | MEDIUM | HIGH | CRITICAL")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    wind_speed_kmh: float = Field(default=0.0, ge=0)
    forecast_hours: int = Field(default=3, ge=1, le=72)


class DisasterSpreadPredictionResponse(BaseModel):
    """Legacy disaster spread prediction response."""

    disaster_id: int
    disaster_type: str
    forecast_hours: int
    spread_direction_degrees: float
    spread_velocity_kmh: float
    confidence_score: float
    zones: list[AffectedZone]


class TeamCandidate(BaseModel):
    """A rescue team being considered for optimization assignment."""

    team_id: int
    team_name: str
    vehicle_type: str
    members: int
    status: str
    latitude: float
    longitude: float


class ResourceOptimizationRequest(BaseModel):
    """Request for AI-driven resource allocation optimization."""

    incident_ids: list[int] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="List of active incident IDs to optimize resource allocation for",
    )
    max_teams_per_incident: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of teams to assign per incident",
    )
    consider_severity: bool = Field(
        default=True,
        description="Weight allocation by incident severity",
    )


class OptimizedAssignment(BaseModel):
    """A single optimized team-to-incident assignment recommendation."""

    incident_id: int
    team_id: int
    team_name: str
    priority_score: float = Field(..., description="Composite assignment priority score (0–100)")
    distance_km: float
    eta_minutes: float
    rationale: str = Field(..., description="Human-readable reason for this assignment")


class ResourceOptimizationResponse(BaseModel):
    """Result of the resource allocation optimization pass."""

    total_incidents_covered: int
    total_teams_allocated: int
    unassigned_incidents: list[int] = Field(
        default_factory=list,
        description="Incident IDs for which no suitable team was found",
    )
    assignments: list[OptimizedAssignment]
    optimization_score: float = Field(
        ..., description="Overall quality score of the allocation (0–100)"
    )
    ai_metadata: dict[str, Any] = Field(default_factory=dict)


class RLRecommendationRequest(BaseModel):
    """Reinforcement Learning policy recommendation request."""

    incident_id: int = Field(..., description="The incident to get an action recommendation for")
    simulation_tick: int = Field(
        default=0,
        ge=0,
        description="Current simulation tick count (provides temporal context)",
    )
    active_incident_count: int = Field(default=1, ge=0)
    available_team_count: int = Field(default=0, ge=0)
    shelter_capacity_percent: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
        description="Current shelter system utilization as a percentage",
    )


class RLAction(BaseModel):
    """A single recommended action from the RL policy."""

    action_type: str = Field(
        ...,
        description=(
            "DISPATCH_TEAM | EVACUATE_CITIZENS | OPEN_SHELTER | "
            "REQUEST_REINFORCEMENT | ESCALATE_SEVERITY | MONITOR"
        ),
    )
    priority: int = Field(..., description="Action priority rank (1 = highest)")
    confidence: float = Field(..., ge=0.0, le=1.0)
    parameters: dict[str, Any] = Field(default_factory=dict)
    rationale: str


class RLRecommendationResponse(BaseModel):
    """RL policy recommendation output — a prioritized set of actions."""

    incident_id: int
    state_vector: dict[str, Any] = Field(
        ..., description="Encoded state features used by the policy"
    )
    recommended_actions: list[RLAction]
    policy_version: str = Field(default="heuristic-v1")
    ai_metadata: dict[str, Any] = Field(default_factory=dict)


class ExplainabilityRequest(BaseModel):
    """Request for an XAI explanation of a system decision."""

    decision_type: str = Field(
        ...,
        description="Type of decision: DISPATCH | PREDICTION | OPTIMIZATION | EVACUATION",
    )
    context: dict[str, Any] = Field(
        ...,
        description="Structured context dict containing the decision parameters",
    )
    target_audience: str = Field(
        default="commander",
        description="Audience tone: 'commander' (tactical) | 'public' (plain language)",
    )


class ExplainabilityResponse(BaseModel):
    """XAI explanation generated by the Ollama LLM."""

    decision_type: str
    explanation: str = Field(..., description="Plain-language explanation of the decision")
    key_factors: list[str] = Field(
        default_factory=list,
        description="Bullet-point list of the top contributing factors",
    )
    confidence: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Model confidence in the explanation quality",
    )
    ai_metadata: dict[str, Any] = Field(default_factory=dict)
