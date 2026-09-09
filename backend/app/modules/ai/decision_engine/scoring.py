"""
AegisAI Decision Engine — Multi-Criteria Scoring & Normalization.

Implements transparent, normalized scoring for candidate actions.
All metrics are strictly normalized to [0.0, 1.0] before weighted combination.
Weights are fully configurable via DispatchScoringPolicyConfig.
"""

import math

import structlog

from app.modules.ai.decision_engine.constraints import DISASTER_CAPABILITY_REQUIREMENTS
from app.modules.ai.schemas import (
    DispatchScoringPolicyConfig,
    HospitalStateDTO,
    IncidentStateDTO,
    ResourceStateDTO,
    ScoringBreakdownDTO,
    WeatherStateDTO,
)

logger = structlog.get_logger("aegis_ai.decision_engine.scoring")


class ScoringEngine:
    """Computes transparent normalized multi-criteria scores for candidate actions."""

    def __init__(self, policy_config: DispatchScoringPolicyConfig | None = None) -> None:
        self.config = policy_config or DispatchScoringPolicyConfig()

    def calculate_score(
        self,
        incident: IncidentStateDTO,
        resource: ResourceStateDTO,
        eta_minutes: float,
        distance_km: float,
        hospital: HospitalStateDTO | None = None,
        weather: WeatherStateDTO | None = None,
    ) -> tuple[float, ScoringBreakdownDTO, float]:
        """
        Calculates normalized total score, scoring breakdown, and confidence rating.

        Returns:
            (total_score: float, breakdown: ScoringBreakdownDTO, confidence: float)
        """
        # 1. Normalize ETA Score: Exponential decay (fastest response yields near 1.0)
        # ETA = 2 min -> 0.92, ETA = 6 min -> 0.78, ETA = 15 min -> 0.54, ETA = 30 min -> 0.30
        eta_score = max(0.0, min(1.0, math.exp(-eta_minutes / 25.0)))

        # 2. Normalize Distance Score: Linear decay bounded at 30km
        distance_score = max(0.0, min(1.0, 1.0 - (distance_km / 30.0)))

        # 3. Normalize Capability Match Score
        disaster_type = incident.disaster_type.upper()
        required_caps = DISASTER_CAPABILITY_REQUIREMENTS.get(disaster_type, ["GENERAL_RESCUE"])
        matched_caps = [c for c in resource.capabilities if c in required_caps]
        cap_ratio = (len(matched_caps) + 1.0) / (len(required_caps) + 1.0)
        capability_score = min(1.0, max(0.0, cap_ratio))

        # 4. Normalize Availability & Readiness Score
        avail_base = (
            1.0 if (resource.availability and resource.status.upper() == "AVAILABLE") else 0.0
        )
        fuel_factor = min(1.0, max(0.0, resource.fuel_level_percent / 100.0))
        availability_score = avail_base * (0.7 + 0.3 * fuel_factor)

        # 5. Normalize Hospital Capacity Score
        if hospital is not None:
            bed_ratio = min(1.0, hospital.available_beds / 30.0)
            icu_ratio = (
                min(1.0, hospital.available_icu / 10.0) if incident.critical_patients > 0 else 1.0
            )
            hospital_score = 0.6 * bed_ratio + 0.4 * icu_ratio
        else:
            hospital_score = 1.0

        # 6. Normalize Risk Score (Adverse weather / severe hazards reduce risk score)
        weather_penalty = 0.0
        if weather:
            if weather.condition in ["STORM", "FLOOD"]:
                weather_penalty += 0.25
            if weather.visibility_km < 3.0:
                weather_penalty += 0.15
        risk_score = max(0.1, min(1.0, 1.0 - weather_penalty))

        # Weighted combination
        cfg = self.config
        total_weights = (
            cfg.eta_weight
            + cfg.distance_weight
            + cfg.capability_weight
            + cfg.availability_weight
            + cfg.hospital_capacity_weight
            + cfg.risk_weight
        )
        total_score = (
            (cfg.eta_weight * eta_score)
            + (cfg.distance_weight * distance_score)
            + (cfg.capability_weight * capability_score)
            + (cfg.availability_weight * availability_score)
            + (cfg.hospital_capacity_weight * hospital_score)
            + (cfg.risk_weight * risk_score)
        ) / max(0.001, total_weights)
        total_score = round(max(0.0, min(1.0, total_score)), 4)

        # Confidence Calculation: Mathematical certainty based on data freshness & margins
        # High confidence when: ETA is under 15 min, capability is 1.0, hospital has ample margin
        confidence = (
            0.40 * eta_score
            + 0.30 * capability_score
            + 0.20 * hospital_score
            + 0.10 * availability_score
        )
        confidence = round(max(0.1, min(0.99, confidence)), 4)

        breakdown = ScoringBreakdownDTO(
            eta_score=round(eta_score, 4),
            distance_score=round(distance_score, 4),
            capability_score=round(capability_score, 4),
            availability_score=round(availability_score, 4),
            hospital_capacity_score=round(hospital_score, 4),
            risk_score=round(risk_score, 4),
            raw_eta_minutes=round(eta_minutes, 2),
            raw_distance_km=round(distance_km, 2),
            total_score=total_score,
        )

        return total_score, breakdown, confidence
