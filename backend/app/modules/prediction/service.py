"""
AegisAI Prediction Module — Domain Service.

Provides complete AI/ML forecasting, risk assessment, and predictive intelligence:
1. `get_predictive_dashboard` — Consolidated command-center predictive dashboard payload.
2. `get_casualty_forecast`     — Multi-horizon casualty growth forecasting (+5m, +15m, +30m, +60m).
3. `get_hospital_forecast`     — Hospital ER & ICU saturation projection.
4. `get_resource_forecast`     — Fleet requirement & shortage analysis.
5. `get_risk_forecast`         — Multi-hazard spatial risk scoring.
6. `get_fire_spread_forecast`  — Spatial fire propagation envelopes.
7. `get_flood_risk_forecast`   — Flood inundation and evacuation urgency.
8. `predict_spread`            — Physics-based disaster radius growth + Ollama XAI narrative.
9. `optimize_allocation`       — Greedy priority-weighted resource allocation optimizer.
10. `get_rl_recommendation`    — Heuristic Reinforcement Learning policy.
11. `explain_decision`         — Standalone XAI endpoint calling Ollama.
12. `record_prediction_outcome`— Prediction telemetry error tracking.

Compatible with Python 3.10.
"""

import math
import time
from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy.orm import Session

from app.core.cache.redis_client import get_redis
from app.core.common.exceptions import EntityNotFoundException
from app.modules.hospital.models import Hospital
from app.modules.incident.models import Incident
from app.modules.incident.repository import IncidentRepository
from app.modules.prediction.ai_client import OllamaClient
from app.modules.prediction.alerts import PredictiveAlertEngine
from app.modules.prediction.forecaster import TimeHorizonForecaster
from app.modules.prediction.models import PredictionRecord
from app.modules.prediction.schemas import (
    AffectedZone,
    CasualtyForecastDTO,
    DisasterPredictionRequest,
    DisasterRiskForecastDTO,
    DisasterSpreadPredictionRequest,
    DisasterSpreadPredictionResponse,
    ExplainabilityRequest,
    ExplainabilityResponse,
    FireSpreadForecastDTO,
    FloodRiskForecastDTO,
    HospitalLoadForecastDTO,
    ModelMetadataDTO,
    OptimizedAssignment,
    PredictionOutcomeRecordRequest,
    PredictionRecordResponse,
    PredictionResponse,
    PredictiveDashboardResponse,
    ResourceDemandForecastDTO,
    ResourceOptimizationRequest,
    ResourceOptimizationResponse,
    RLAction,
    RLRecommendationRequest,
    RLRecommendationResponse,
)
from app.modules.resource.models import RescueTeam
from app.modules.simulation.engine import DigitalTwinEngine

_log = structlog.get_logger("aegis_ai.prediction")


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km between two WGS84 points."""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class PredictionService:
    """
    AI & Prediction Domain Service.

    Orchestrates time-horizon forecasting models, predictive alerts,
    caching, telemetry, and legacy ML algorithms.
    """

    # In-memory cache buffer (5s TTL)
    _cached_dashboard: dict[str, Any] = {}
    _cache_timestamp: float = 0.0

    # --- Predictive Intelligence Dashboard ----------------------------------

    @classmethod
    def get_predictive_dashboard(
        cls,
        db: Session,
        simulation_id: str | None = None,
        use_cache: bool = True,
    ) -> PredictiveDashboardResponse:
        """
        Consolidates all predictive intelligence into a single command-center payload.
        """
        now_t = time.time()
        if use_cache:
            r = get_redis()
            if r:
                try:
                    import json
                    cached_val = r.get("aegis:cache:predictive_dashboard")
                    if cached_val:
                        return PredictiveDashboardResponse(**json.loads(cached_val))
                except Exception as exc:
                    _log.debug("redis_cache_read_error", error=str(exc))
            if cls._cached_dashboard and (now_t - cls._cache_timestamp) < 5.0:
                return PredictiveDashboardResponse(**cls._cached_dashboard)

        now_dt = datetime.now(timezone.utc)

        # 1. Gather live state from DB and Digital Twin
        incidents = (
            db.query(Incident)
            .filter(Incident.status.in_(["ACTIVE", "REPORTED", "INVESTIGATING", "RESPONDING"]))
            .all()
        )
        hospitals = db.query(Hospital).filter(Hospital.is_operational.is_(True)).all()
        resources = db.query(RescueTeam).all()

        # Digital twin environmental context
        twin = DigitalTwinEngine()
        weather_sev = 1.0
        wind_spd = 15.0
        rain_mm = 0.0
        if twin and hasattr(twin, "weather") and twin.weather:
            w = twin.weather
            wind_spd = getattr(w, "wind_speed_kmh", 15.0) or 15.0
            rain_mm = getattr(w, "rainfall_mm", 0.0) or 0.0
            if getattr(w, "condition", "") in ["THUNDERSTORM", "HEAVY_RAIN", "STORM"]:
                weather_sev = 1.5

        # 2. Run Forecasting Engines
        active_teams_cnt = len([r for r in resources if r.status == "DEPLOYED"])
        casualties = TimeHorizonForecaster.forecast_casualties(
            incidents=incidents,
            weather_severity=weather_sev,
            active_teams_count=active_teams_cnt,
        )
        hosp_forecasts = TimeHorizonForecaster.forecast_hospitals(
            hospitals=hospitals,
            casualty_forecast=casualties,
        )
        res_forecasts = TimeHorizonForecaster.forecast_resources(
            resources=resources,
            incidents=incidents,
        )
        risk_forecasts = TimeHorizonForecaster.forecast_disaster_risk(
            incidents=incidents,
            weather_severity=weather_sev,
        )
        fire_forecasts = TimeHorizonForecaster.forecast_fire_spread(
            incidents=incidents,
            wind_speed_kmh=wind_spd,
        )
        flood_forecasts = TimeHorizonForecaster.forecast_flood_risk(
            incidents=incidents,
            rainfall_mm=rain_mm,
        )

        # 3. Generate Predictive Alerts
        alerts = PredictiveAlertEngine.generate_alerts(
            casualties=casualties,
            hospitals=hosp_forecasts,
            resources=res_forecasts,
            disaster_risks=risk_forecasts,
        )

        # 4. Model Metadata
        meta = ModelMetadataDTO(
            model_name="AegisAI-PredictiveEngine-v1",
            model_version="1.2.0",
            prediction_timestamp=now_dt,
            data_timestamp=now_dt,
            prediction_source="SIMULATION+ML",
            confidence_calibrated=True,
        )

        response = PredictiveDashboardResponse(
            generated_at=now_dt,
            simulation_id=simulation_id,
            prediction_source="SIMULATION+ML",
            casualties=casualties,
            hospitals=hosp_forecasts,
            resources=res_forecasts,
            disaster_risk=risk_forecasts,
            fire_spread=fire_forecasts,
            flood_risk=flood_forecasts,
            alerts=alerts,
            model_metadata=meta,
        )

        dumped_dashboard = response.model_dump(mode="json")
        cls._cached_dashboard = dumped_dashboard
        cls._cache_timestamp = now_t
        if r := get_redis():
            try:
                import json
                r.set("aegis:cache:predictive_dashboard", json.dumps(dumped_dashboard), ex=5)
            except Exception as exc:
                _log.debug("redis_cache_write_error", error=str(exc))

        # C4 FIX: Persist a combined forecast record so prediction_records is
        # actually populated for MAE/MAPE tracking. Fire-and-forget; errors
        # are logged but must not fail the dashboard response.
        try:
            cls.save_prediction_record(
                db=db,
                prediction_type="COMBINED_FORECAST",
                simulation_id=simulation_id,
                forecast_horizon_minutes=60,
                confidence=casualties.confidence_score if hasattr(casualties, "confidence_score") else 0.8,
                prediction_source="SIMULATION+ML",
                predicted_value={
                    "casualties_30m": getattr(casualties, "forecast_30m", None),
                    "casualties_60m": getattr(casualties, "forecast_60m", None),
                    "hospital_saturation_count": len(hosp_forecasts),
                    "resource_shortage_count": sum(
                        1 for r in res_forecasts if getattr(r, "shortage_risk", "LOW") in ("HIGH", "CRITICAL")
                    ),
                    "active_alerts": len(alerts),
                },
                input_snapshot={
                    "active_incidents": len(incidents),
                    "operational_hospitals": len(hospitals),
                    "total_resources": len(resources),
                    "weather_severity": weather_sev,
                },
            )
        except Exception as persist_err:
            _log.warning("prediction_record_persist_failed", error=str(persist_err))

        return response

    @classmethod
    def get_casualty_forecast(cls, db: Session) -> CasualtyForecastDTO:
        """Returns dedicated casualty & patient forecast."""
        incidents = db.query(Incident).filter(Incident.status.in_(["ACTIVE", "REPORTED"])).all()
        return TimeHorizonForecaster.forecast_casualties(incidents)

    @classmethod
    def get_hospital_forecast(cls, db: Session) -> list[HospitalLoadForecastDTO]:
        """Returns dedicated hospital saturation forecast."""
        incidents = db.query(Incident).filter(Incident.status.in_(["ACTIVE", "REPORTED"])).all()
        hospitals = db.query(Hospital).filter(Hospital.is_operational.is_(True)).all()
        cas = TimeHorizonForecaster.forecast_casualties(incidents)
        return TimeHorizonForecaster.forecast_hospitals(hospitals, cas)

    @classmethod
    def get_resource_forecast(cls, db: Session) -> list[ResourceDemandForecastDTO]:
        """Returns dedicated resource demand forecast."""
        incidents = db.query(Incident).filter(Incident.status.in_(["ACTIVE", "REPORTED"])).all()
        resources = db.query(RescueTeam).all()
        return TimeHorizonForecaster.forecast_resources(resources, incidents)

    @classmethod
    def get_risk_forecast(cls, db: Session) -> list[DisasterRiskForecastDTO]:
        """Returns dedicated disaster risk forecast."""
        incidents = db.query(Incident).filter(Incident.status.in_(["ACTIVE", "REPORTED"])).all()
        return TimeHorizonForecaster.forecast_disaster_risk(incidents)

    @classmethod
    def get_fire_spread_forecast(cls, db: Session) -> list[FireSpreadForecastDTO]:
        """Returns spatial fire spread zones."""
        incidents = db.query(Incident).filter(Incident.status.in_(["ACTIVE", "REPORTED"])).all()
        return TimeHorizonForecaster.forecast_fire_spread(incidents)

    @classmethod
    def get_flood_risk_forecast(cls, db: Session) -> list[FloodRiskForecastDTO]:
        """Returns flood inundation risk."""
        incidents = db.query(Incident).filter(Incident.status.in_(["ACTIVE", "REPORTED"])).all()
        return TimeHorizonForecaster.forecast_flood_risk(incidents)

    # --- Prediction Persistence & Outcomes -----------------------------------

    @classmethod
    def save_prediction_record(
        cls,
        db: Session,
        prediction_type: str,
        predicted_value: dict[str, Any],
        forecast_horizon_minutes: int = 15,
        simulation_id: str | None = None,
        incident_id: int | None = None,
        confidence: float | None = None,
        prediction_source: str = "SIMULATION",
        input_snapshot: dict[str, Any] | None = None,
    ) -> PredictionRecord:
        """Persists a prediction record for accuracy tracking."""
        record = PredictionRecord(
            prediction_type=prediction_type,
            simulation_id=simulation_id,
            incident_id=incident_id,
            forecast_horizon_minutes=forecast_horizon_minutes,
            predicted_value=predicted_value,
            confidence=confidence,
            prediction_source=prediction_source,
            input_snapshot=input_snapshot,
            created_at=datetime.now(timezone.utc),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @classmethod
    def record_outcome(
        cls,
        db: Session,
        record_id: int,
        payload: PredictionOutcomeRecordRequest,
    ) -> PredictionRecordResponse:
        """Records actual observed outcome against a previous prediction."""
        record = db.query(PredictionRecord).filter(PredictionRecord.id == record_id).first()
        if not record:
            raise EntityNotFoundException("PredictionRecord", record_id)

        record.actual_value = payload.actual_value
        if payload.error_rate is not None:
            record.error_rate = payload.error_rate
        db.commit()
        db.refresh(record)
        return PredictionRecordResponse.model_validate(record)

    @classmethod
    def list_prediction_history(
        cls,
        db: Session,
        prediction_type: str | None = None,
        simulation_id: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[PredictionRecordResponse], int]:
        """Retrieves prediction history with filters and pagination."""
        query = db.query(PredictionRecord)
        if prediction_type:
            query = query.filter(PredictionRecord.prediction_type == prediction_type)
        if simulation_id:
            query = query.filter(PredictionRecord.simulation_id == simulation_id)

        total = query.count()
        items = query.order_by(PredictionRecord.created_at.desc()).offset(skip).limit(limit).all()
        return [PredictionRecordResponse.model_validate(item) for item in items], total

    # --- Spread Prediction (Existing & Maintained) ---------------------------

    @staticmethod
    async def predict_spread(db: Session, payload: DisasterPredictionRequest) -> PredictionResponse:
        """Calculate disaster spread radius and generate an LLM XAI explanation."""
        repo = IncidentRepository(db)
        incident = repo.get_by_id(payload.incident_id)
        if incident is None:
            raise EntityNotFoundException("Incident", payload.incident_id)

        base_rate: dict[str, float] = {
            "FIRE": 150.0,
            "WILDFIRE": 500.0,
            "FLOOD": 200.0,
            "GAS_LEAK": 100.0,
            "EARTHQUAKE": 0.0,
            "BUILDING_COLLAPSE": 0.0,
            "LANDSLIDE": 80.0,
            "TSUNAMI": 400.0,
            "ACCIDENT": 0.0,
        }
        type_rate = base_rate.get(incident.disaster_type, 50.0)

        severity_mult: dict[str, float] = {
            "LOW": 0.5,
            "MEDIUM": 1.0,
            "HIGH": 2.0,
            "CRITICAL": 4.0,
        }
        sev_mult = severity_mult.get(incident.severity, 1.0)

        expansion = type_rate * sev_mult * payload.weather_multiplier * payload.time_horizon_hours
        predicted_radius = payload.current_affected_radius_meters + expansion

        area_sq_m = math.pi * (predicted_radius**2)
        population_density = 0.005
        estimated_casualties = int(area_sq_m * population_density * (sev_mult / 4.0))

        confidence = max(0.35, 0.95 - (payload.time_horizon_hours * 0.005))

        ai_client = OllamaClient()
        explanation = await ai_client.generate_explanation(
            incident_type=incident.disaster_type,
            severity=incident.severity,
            radius=payload.current_affected_radius_meters,
            time_horizon=payload.time_horizon_hours,
            predicted_radius=round(predicted_radius, 2),
        )

        return PredictionResponse(
            incident_id=incident.id,
            time_horizon_hours=payload.time_horizon_hours,
            predicted_radius_meters=round(predicted_radius, 2),
            estimated_casualties=estimated_casualties,
            confidence_score=round(confidence, 3),
            explanation=explanation,
            ai_metadata={"model": ai_client.model, "type": "spread_prediction"},
        )

    # --- Resource Optimization (Existing & Maintained) ----------------------

    @staticmethod
    def optimize_allocation(
        db: Session, request: ResourceOptimizationRequest
    ) -> ResourceOptimizationResponse:
        """Greedy priority-weighted resource allocation optimizer."""
        incident_repo = IncidentRepository(db)

        severity_score = {"CRITICAL": 100, "HIGH": 70, "MEDIUM": 40, "LOW": 10}
        status_score = {"REPORTED": 50, "INVESTIGATING": 30, "RESPONDING": 10, "MONITORING": 5}

        scored_incidents = []
        for inc_id in request.incident_ids:
            inc = incident_repo.get_by_id(inc_id)
            if inc is None:
                continue
            urgency = severity_score.get(inc.severity, 10) + status_score.get(inc.status, 0)
            scored_incidents.append((inc, urgency))

        scored_incidents.sort(key=lambda x: x[1], reverse=True)

        available_teams = db.query(RescueTeam).filter(RescueTeam.status == "AVAILABLE").all()
        assigned_team_ids: set[int] = set()
        assignments: list[OptimizedAssignment] = []
        unassigned: list[int] = []

        for incident, urgency_score in scored_incidents:
            teams_for_incident = 0
            teams_with_dist = [
                (
                    team,
                    _haversine_km(
                        team.latitude,
                        team.longitude,
                        incident.latitude,
                        incident.longitude,
                    ),
                )
                for team in available_teams
                if team.id not in assigned_team_ids
            ]
            teams_with_dist.sort(key=lambda x: x[1])

            for team, dist_km in teams_with_dist:
                if teams_for_incident >= request.max_teams_per_incident:
                    break

                eta_min = round(max(1.0, (dist_km / 40.0) * 60.0), 1)
                priority_score = round(urgency_score - (eta_min * 0.5) + (team.members * 1.5), 2)

                assignments.append(
                    OptimizedAssignment(
                        incident_id=incident.id,
                        team_id=team.id,
                        team_name=team.team_name,
                        priority_score=max(0.0, priority_score),
                        distance_km=round(dist_km, 2),
                        eta_minutes=eta_min,
                        rationale=(
                            f"{team.team_name} ({team.vehicle_type}, {team.members} members) "
                            f"is {dist_km:.1f} km away with {eta_min:.0f} min ETA. "
                            f"Assigned to {incident.disaster_type} incident "
                            f"(severity: {incident.severity})."
                        ),
                    )
                )
                assigned_team_ids.add(team.id)
                teams_for_incident += 1

            if teams_for_incident == 0:
                unassigned.append(incident.id)

        coverage_rate = len(scored_incidents) / max(1, len(request.incident_ids))
        avg_priority = sum(a.priority_score for a in assignments) / max(1, len(assignments))
        optimization_score = round(min(100.0, coverage_rate * 50 + avg_priority * 0.5), 2)

        return ResourceOptimizationResponse(
            total_incidents_covered=len(scored_incidents) - len(unassigned),
            total_teams_allocated=len(assigned_team_ids),
            unassigned_incidents=unassigned,
            assignments=assignments,
            optimization_score=optimization_score,
            ai_metadata={"algorithm": "greedy_priority_weighted", "version": "1.0"},
        )

    # --- RL Recommendation (Existing & Maintained) --------------------------

    @staticmethod
    def get_rl_recommendation(
        db: Session, request: RLRecommendationRequest
    ) -> RLRecommendationResponse:
        """Heuristic Reinforcement Learning policy — state to action mapping."""
        incident_repo = IncidentRepository(db)
        incident = incident_repo.get_by_id(request.incident_id)
        if incident is None:
            raise EntityNotFoundException("Incident", request.incident_id)

        severity_value = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        severity_val = severity_value.get(incident.severity, 2)
        team_deficit = request.active_incident_count - request.available_team_count
        shelter_pressure = request.shelter_capacity_percent > 80.0

        recommended_actions: list[RLAction] = []

        if severity_val >= 3:
            recommended_actions.append(
                RLAction(
                    action_type="DISPATCH_TEAM",
                    priority=1,
                    confidence=0.95,
                    parameters={"incident_id": request.incident_id, "count": 2},
                    rationale=(
                        f"Incident severity is {incident.severity}. "
                        "Immediate team dispatch is the highest-priority action."
                    ),
                )
            )

        if severity_val >= 4 and not shelter_pressure:
            recommended_actions.append(
                RLAction(
                    action_type="EVACUATE_CITIZENS",
                    priority=2,
                    confidence=0.88,
                    parameters={
                        "incident_id": request.incident_id,
                        "radius_meters": incident.affected_radius_meters or 1000,
                    },
                    rationale=(
                        "CRITICAL severity with available shelter capacity. "
                        "Immediate citizen evacuation will reduce casualties."
                    ),
                )
            )

        if shelter_pressure:
            recommended_actions.append(
                RLAction(
                    action_type="OPEN_SHELTER",
                    priority=2,
                    confidence=0.82,
                    parameters={"target_capacity_increase": 200},
                    rationale=(
                        f"Shelter system is at {request.shelter_capacity_percent:.0f}% capacity. "
                        "Opening additional shelter space is critical."
                    ),
                )
            )

        if team_deficit > 0:
            recommended_actions.append(
                RLAction(
                    action_type="REQUEST_REINFORCEMENT",
                    priority=3,
                    confidence=0.75,
                    parameters={"requested_teams": min(5, team_deficit + 2)},
                    rationale=(
                        f"Team deficit: {team_deficit} more incidents than available teams. "
                        "Requesting mutual aid reinforcement."
                    ),
                )
            )

        if request.active_incident_count >= 5 and severity_val < 4:
            recommended_actions.append(
                RLAction(
                    action_type="ESCALATE_SEVERITY",
                    priority=4,
                    confidence=0.70,
                    parameters={"incident_id": request.incident_id, "new_severity": "HIGH"},
                    rationale=(
                        f"Load high ({request.active_incident_count} incidents). "
                        "Escalating severity for resource prioritization."
                    ),
                )
            )

        if not recommended_actions or severity_val <= 2:
            recommended_actions.append(
                RLAction(
                    action_type="MONITOR",
                    priority=len(recommended_actions) + 1,
                    confidence=0.60,
                    parameters={"interval_minutes": 15},
                    rationale="Situation is stable. Continue active monitoring.",
                )
            )

        state_vector: dict[str, Any] = {
            "incident_id": request.incident_id,
            "severity_encoded": severity_val,
            "active_incidents": request.active_incident_count,
            "available_teams": request.available_team_count,
            "team_deficit": team_deficit,
            "shelter_pressure": shelter_pressure,
            "simulation_tick": request.simulation_tick,
        }

        return RLRecommendationResponse(
            incident_id=request.incident_id,
            state_vector=state_vector,
            recommended_actions=recommended_actions,
            policy_version="heuristic-v1",
            ai_metadata={"type": "heuristic_rl", "incident_severity": incident.severity},
        )

    # --- XAI Explainability (Existing & Maintained) -------------------------

    @staticmethod
    async def explain_decision(
        request: ExplainabilityRequest,
    ) -> ExplainabilityResponse:
        """Generate a plain-language explanation for any system decision."""
        ai_client = OllamaClient()

        context_str = "\n".join(f"  - {k}: {v}" for k, v in request.context.items())
        audience_note = (
            "Use tactical, precise language for a field commander."
            if request.target_audience == "commander"
            else "Use plain, accessible language for a general audience."
        )

        prompt = (
            f"You are an AI assistant for an emergency management platform.\n"
            f"Explain the following {request.decision_type} decision in clear terms.\n"
            f"Audience: {request.target_audience}. {audience_note}\n\n"
            f"Decision context:\n{context_str}\n\n"
            f"Provide:\n"
            f"1. A 2-3 sentence explanation of WHY this decision was made.\n"
            f"2. The top 3 contributing factors as bullet points.\n"
            f"Keep the total response under 150 words."
        )

        explanation_text = await ai_client.raw_generate(prompt)

        key_factors = [
            line.lstrip("•-* ").strip()
            for line in explanation_text.split("\n")
            if line.strip().startswith(("•", "-", "*", "1.", "2.", "3."))
        ][:3]

        if not key_factors:
            key_factors = [
                f"Decision type: {request.decision_type}",
                f"Context parameters: {len(request.context)} factors considered",
                "Optimization based on current system state",
            ]

        return ExplainabilityResponse(
            decision_type=request.decision_type,
            explanation=explanation_text,
            key_factors=key_factors,
            confidence=0.85,
            ai_metadata={"model": ai_client.model, "type": "xai_explanation"},
        )

    # --- Legacy Compatibility ------------------------------------------------

    @staticmethod
    def predict_disaster_spread(
        request: DisasterSpreadPredictionRequest,
    ) -> DisasterSpreadPredictionResponse:
        """Legacy disaster spread prediction — kept for backward compatibility."""
        velocity = round(
            request.wind_speed_kmh * 0.2 + (2.0 if request.severity == "CRITICAL" else 1.0),
            2,
        )
        direction = 45.0

        inner_radius = velocity * request.forecast_hours * 200.0
        outer_radius = inner_radius * 2.5

        zones = [
            AffectedZone(
                radius_meters=round(inner_radius, 2),
                risk_level="HIGH",
                estimated_impacted_population=int(inner_radius * 1.5),
                recommended_action="Immediate evacuation mandatory. Deploy fire & rescue assets.",
            ),
            AffectedZone(
                radius_meters=round(outer_radius, 2),
                risk_level="MEDIUM",
                estimated_impacted_population=int(outer_radius * 2.0),
                recommended_action="Prepare secondary perimeter reserves.",
            ),
        ]

        return DisasterSpreadPredictionResponse(
            disaster_id=request.disaster_id,
            disaster_type=request.disaster_type,
            forecast_hours=request.forecast_hours,
            spread_direction_degrees=direction,
            spread_velocity_kmh=velocity,
            confidence_score=0.92,
            zones=zones,
        )
