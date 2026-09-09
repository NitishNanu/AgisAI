"""
AegisAI Decision Engine — Candidate Generator.

Generates and evaluates candidate emergency response actions for incidents:
1. Calculates real-world road route & travel ETA via OSRM (with Haversine fallback).
2. Matches suitable destination hospitals/shelters.
3. Evaluates hard constraints via ConstraintEngine.
4. Scores candidates via multi-criteria ScoringEngine.
"""

import structlog

from app.modules.ai.decision_engine.constraints import ConstraintEngine
from app.modules.ai.decision_engine.scoring import ScoringEngine
from app.modules.ai.schemas import (
    DecisionCandidateDTO,
    DispatchScoringPolicyConfig,
    HospitalStateDTO,
    IncidentStateDTO,
    ResourceStateDTO,
    RoadStateDTO,
    WeatherStateDTO,
)
from app.routing.osrm import OSRMService

logger = structlog.get_logger("aegis_ai.decision_engine.candidates")


class CandidateGenerator:
    """Generates and evaluates candidate response actions for emergency incidents."""

    def __init__(
        self,
        constraint_engine: ConstraintEngine | None = None,
        scoring_engine: ScoringEngine | None = None,
        scoring_policy_config: DispatchScoringPolicyConfig | None = None,
    ) -> None:
        self.constraint_engine = constraint_engine or ConstraintEngine()
        self.scoring_engine = scoring_engine or ScoringEngine(scoring_policy_config)

    async def generate_candidates_for_incident(
        self,
        incident: IncidentStateDTO,
        resources: list[ResourceStateDTO],
        hospitals: list[HospitalStateDTO],
        roads: list[RoadStateDTO] | None = None,
        weather: WeatherStateDTO | None = None,
    ) -> list[DecisionCandidateDTO]:
        """
        Evaluate all resources as potential candidates for a given incident.
        """
        candidates: list[DecisionCandidateDTO] = []
        roads_list = roads or []

        # Find best operational hospital for medical/casualty incidents
        best_hospital = self._select_best_hospital(incident, hospitals)

        for res in resources:
            # 1. Calculate road route and travel ETA
            route_info = await OSRMService.get_route(
                start_lat=res.latitude,
                start_lon=res.longitude,
                end_lat=incident.latitude,
                end_lon=incident.longitude,
            )
            distance_km = route_info.get("distance_km", 1.0)
            eta_minutes = route_info.get("duration_minutes", 5.0)
            geometry = route_info.get("geometry")

            # 2. Hard constraint evaluation
            hosp_eval = (
                best_hospital if res.vehicle_type.upper() in ["AMBULANCE", "HELICOPTER"] else None
            )
            constraint_result = self.constraint_engine.evaluate_candidate(
                incident=incident,
                resource=res,
                hospital=hosp_eval,
                roads=roads_list,
            )

            # 3. Transparent scoring
            score, breakdown, confidence = self.scoring_engine.calculate_score(
                incident=incident,
                resource=res,
                eta_minutes=eta_minutes,
                distance_km=distance_km,
                hospital=hosp_eval,
                weather=weather,
            )

            rejection_reason = (
                "; ".join(constraint_result.rejection_reasons)
                if not constraint_result.passed
                else None
            )

            candidate = DecisionCandidateDTO(
                resource_id=res.resource_id,
                resource_name=res.team_name,
                vehicle_type=res.vehicle_type,
                incident_id=incident.incident_id,
                hospital_id=best_hospital.hospital_id if best_hospital else None,
                hospital_name=best_hospital.name if best_hospital else None,
                eta_minutes=eta_minutes,
                distance_km=distance_km,
                route_geometry=geometry,
                suitability=score if constraint_result.passed else 0.0,
                constraints_passed=constraint_result.passed,
                constraint_evaluation=constraint_result,
                scoring_breakdown=breakdown,
                rejection_reason=rejection_reason,
            )
            candidates.append(candidate)

        # Sort candidates: Valid candidates first by suitability desc, then rejected
        candidates.sort(
            key=lambda c: (1 if c.constraints_passed else 0, c.suitability), reverse=True
        )
        return candidates

    def _select_best_hospital(
        self,
        incident: IncidentStateDTO,
        hospitals: list[HospitalStateDTO],
    ) -> HospitalStateDTO | None:
        """Select nearest operational hospital with adequate beds."""
        if not hospitals:
            return None

        operational = [h for h in hospitals if h.is_operational and h.available_beds > 0]
        if not operational:
            return None

        if incident.critical_patients > 0:
            with_icu = [h for h in operational if h.available_icu > 0]
            if with_icu:
                operational = with_icu

        # Pick nearest
        return min(
            operational,
            key=lambda h: (
                (h.latitude - incident.latitude) ** 2 + (h.longitude - incident.longitude) ** 2
            ),
        )
