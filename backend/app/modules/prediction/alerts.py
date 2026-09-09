"""
AegisAI Prediction Module — Predictive Alert Engine.

Monitors real-time forecast telemetry, detects critical threshold breaches,
deduplicates alerts across cooldown windows, and generates factual XAI explanations.
Compatible with Python 3.10.
"""

from datetime import datetime, timezone

import structlog

from app.modules.prediction.schemas import (
    CasualtyForecastDTO,
    DisasterRiskForecastDTO,
    HospitalLoadForecastDTO,
    PredictiveAlertDTO,
    ResourceDemandForecastDTO,
)

logger = structlog.get_logger("aegis_ai.prediction.alerts")


class PredictiveAlertEngine:
    """Detects and formats actionable predictive alerts with structured explainability."""

    _last_alert_times: dict[str, datetime] = {}
    COOLDOWN_SECONDS: int = 120  # 2 minute deduplication cooldown

    @classmethod
    def generate_alerts(
        cls,
        casualties: CasualtyForecastDTO,
        hospitals: list[HospitalLoadForecastDTO],
        resources: list[ResourceDemandForecastDTO],
        disaster_risks: list[DisasterRiskForecastDTO],
    ) -> list[PredictiveAlertDTO]:
        """
        Evaluates forecast telemetry across all operational domains.
        """
        now = datetime.now(timezone.utc)
        alerts: list[PredictiveAlertDTO] = []

        # 1. Hospital Overload Alerts
        for h in hospitals:
            is_over = h.current_icu_occupancy_percent >= 90.0 or (
                h.forecast and h.forecast[-1].is_overloaded
            )
            if is_over:
                over_min = h.expected_overload_minutes or 30
                sev = (
                    "CRITICAL"
                    if (h.current_icu_occupancy_percent >= 95.0 or over_min <= 15)
                    else "HIGH"
                )
                alert_key = f"hosp_overload_{h.hospital_id}"

                if cls._should_emit(alert_key, now):
                    exp = (
                        f"ICU occupancy is {h.current_icu_occupancy_percent}% with only "
                        f"{h.available_icu} beds available. Patient inflow will exceed "
                        f"capacity within ~{int(over_min)} minutes."
                    )
                    act = f"Reroute non-critical transports away from {h.name}."

                    alerts.append(
                        PredictiveAlertDTO(
                            id=f"alt-hosp-{h.hospital_id}-{int(now.timestamp())}",
                            type="HOSPITAL_OVERLOAD",
                            severity=sev,
                            title=f"ICU Saturation Warning — {h.name}",
                            message=f"{h.name} near capacity (in ~{int(over_min)}m).",
                            timestamp=now,
                            source="PREDICTIVE_ENGINE",
                            related_entity_id=h.hospital_id,
                            related_entity_name=h.name,
                            confidence=0.92,
                            explanation=exp,
                            recommended_action=act,
                        )
                    )
                    cls._record_emission(alert_key, now)

        # 2. Resource Deficit Alerts
        for r in resources:
            for pt in r.forecast:
                if pt.projected_shortage > 0:
                    sev = "CRITICAL" if pt.projected_shortage >= 3 else "HIGH"
                    alert_key = f"res_shortage_{r.resource_type}_{pt.horizon_minutes}"

                    if cls._should_emit(alert_key, now):
                        exp = (
                            f"Available {r.resource_type} units: {r.current_available}. "
                            f"Demand at +{pt.horizon_minutes}m is {pt.required_count}. "
                            f"Deficit of {pt.projected_shortage} units will delay response."
                        )
                        act = f"Authorize mutual aid request for {r.resource_type} units."

                        alerts.append(
                            PredictiveAlertDTO(
                                id=f"alt-res-{r.resource_type}-{pt.horizon_minutes}-{int(now.timestamp())}",
                                type="RESOURCE_SHORTAGE",
                                severity=sev,
                                title=f"{r.resource_type} Shortage (+{pt.horizon_minutes}m)",
                                message=(
                                    f"Projected deficit of {pt.projected_shortage} "
                                    f"{r.resource_type}(s) in next {pt.horizon_minutes}m."
                                ),
                                timestamp=now,
                                source="PREDICTIVE_ENGINE",
                                related_entity_id=None,
                                related_entity_name=r.resource_type,
                                confidence=0.88,
                                explanation=exp,
                                recommended_action=act,
                            )
                        )
                        cls._record_emission(alert_key, now)
                    break

        # 3. Casualty Surge Alerts
        if casualties.forecast and len(casualties.forecast) >= 3:
            cas_30 = casualties.forecast[2].expected_casualties
            if casualties.current_casualties > 0 and cas_30 >= (
                casualties.current_casualties * 1.4
            ):
                alert_key = "casualty_surge_30m"
                if cls._should_emit(alert_key, now):
                    cur_c = casualties.current_casualties
                    pct_inc = int(((cas_30 - cur_c) / max(1, cur_c)) * 100)
                    exp = (
                        f"Active incident dynamics indicate casualties will surge from {cur_c} "
                        f"to {cas_30} within 30m due to hazard expansion."
                    )
                    act = "Pre-stage mobile triage stations and mass-casualty kits."

                    alerts.append(
                        PredictiveAlertDTO(
                            id=f"alt-cas-surge-{int(now.timestamp())}",
                            type="CASUALTY_SURGE",
                            severity="HIGH",
                            title="Accelerated Casualty Inflow Forecast",
                            message=f"Casualty growth projected to surge by {pct_inc}% in 30m.",
                            timestamp=now,
                            source="PREDICTIVE_ENGINE",
                            related_entity_id=None,
                            related_entity_name="City-Wide Casualties",
                            confidence=0.85,
                            explanation=exp,
                            recommended_action=act,
                        )
                    )
                    cls._record_emission(alert_key, now)

        # 4. Disaster Spatial Risk Alerts
        for dr in disaster_risks:
            if dr.risk_level == "CRITICAL":
                alert_key = f"disaster_risk_{dr.incident_id}"
                if cls._should_emit(alert_key, now):
                    exp = (
                        f"Incident #{dr.incident_id} ({dr.disaster_type}) reached CRITICAL risk. "
                        f"Factors: {', '.join(dr.contributing_factors)}."
                    )
                    act = "Establish secondary isolation perimeter and initiate citizen evacuation."

                    alerts.append(
                        PredictiveAlertDTO(
                            id=f"alt-risk-{dr.incident_id}-{int(now.timestamp())}",
                            type="DISASTER_SPREAD",
                            severity="CRITICAL",
                            title=f"Critical Hazard Expansion — Incident #{dr.incident_id}",
                            message=f"Incident #{dr.incident_id} exhibits critical growth risk.",
                            timestamp=now,
                            source="PREDICTIVE_ENGINE",
                            related_entity_id=dr.incident_id,
                            related_entity_name=f"Incident #{dr.incident_id}",
                            confidence=dr.confidence or 0.90,
                            explanation=exp,
                            recommended_action=act,
                        )
                    )
                    cls._record_emission(alert_key, now)

        return alerts

    @classmethod
    def _should_emit(cls, key: str, now: datetime) -> bool:
        """
        H5 FIX: Check deduplication state via Redis (multi-worker safe).

        Redis key exists → within cooldown → suppress.
        Redis unavailable → fall back to in-memory class-level dict.
        """
        redis_key = f"aegis:alert_cooldown:{key}"
        try:
            from app.core.cache.redis_client import get_redis  # noqa: PLC0415
            r = get_redis()
            if r is not None:
                return r.get(redis_key) is None
        except Exception:
            pass
        # In-memory fallback (single-process / no Redis)
        last = cls._last_alert_times.get(key)
        if last is None:
            return True
        return (now - last).total_seconds() > cls.COOLDOWN_SECONDS

    @classmethod
    def _record_emission(cls, key: str, now: datetime) -> None:
        """
        Record that an alert was emitted so the cooldown is enforced.

        Sets a Redis key with TTL = COOLDOWN_SECONDS (auto-expires).
        Also updates in-memory dict as fallback for non-Redis environments.
        """
        redis_key = f"aegis:alert_cooldown:{key}"
        try:
            from app.core.cache.redis_client import get_redis  # noqa: PLC0415
            r = get_redis()
            if r is not None:
                r.set(redis_key, "1", ex=cls.COOLDOWN_SECONDS)
                return
        except Exception:
            pass
        # In-memory fallback
        cls._last_alert_times[key] = now
