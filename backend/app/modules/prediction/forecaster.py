"""
AegisAI Prediction Module — Time-Horizon Forecasting Engine.

Implements mathematical and simulation-grounded forecasting for:
- Casualties & Patient Growth (5m, 15m, 30m, 60m)
- Hospital Load & ICU Overload Projection
- Emergency Fleet Demand & Shortage Analysis
- Multi-Hazard Disaster Risk & Spatial Propagation
Compatible with Python 3.10.
"""

import math
from typing import Any

import structlog

from app.modules.prediction.schemas import (
    CasualtyForecastDTO,
    CasualtyHorizonForecast,
    DisasterRiskForecastDTO,
    FireSpreadForecastDTO,
    FireSpreadZoneDTO,
    FloodRiskForecastDTO,
    HospitalHorizonLoad,
    HospitalLoadForecastDTO,
    ResourceDemandForecastDTO,
    ResourceHorizonDemand,
)

logger = structlog.get_logger("aegis_ai.prediction.forecaster")

HORIZONS = [5, 15, 30, 60]

DISASTER_GROWTH_FACTORS: dict[str, float] = {
    "FIRE": 0.015,
    "WILDFIRE": 0.035,
    "FLOOD": 0.012,
    "GAS_LEAK": 0.018,
    "EARTHQUAKE": 0.005,
    "BUILDING_COLLAPSE": 0.004,
    "MEDICAL": 0.008,
    "TRAFFIC_ACCIDENT": 0.002,
    "STORM": 0.020,
    "OTHER": 0.005,
}

SEVERITY_FACTORS: dict[str, float] = {
    "CRITICAL": 2.2,
    "HIGH": 1.6,
    "MEDIUM": 1.1,
    "LOW": 0.7,
}


class TimeHorizonForecaster:
    """Mathematical multi-horizon forecasting engine for emergency command awareness."""

    @classmethod
    def forecast_casualties(
        cls,
        incidents: list[Any],
        weather_severity: float = 1.0,
        active_teams_count: int = 0,
    ) -> CasualtyForecastDTO:
        """
        Projects casualty counts at 5m, 15m, 30m, and 60m horizons.
        """
        curr_cas = sum(getattr(i, "estimated_casualties", 0) or 0 for i in incidents)
        curr_crit = sum(getattr(i, "critical_patients", 0) or 0 for i in incidents)
        curr_inj = sum(getattr(i, "estimated_affected_people", 0) or 0 for i in incidents)

        # Baseline minimums if incidents exist
        if incidents and curr_cas == 0:
            curr_cas = len(incidents) * 4
            curr_crit = max(1, int(curr_cas * 0.25))
            curr_inj = curr_cas * 2

        curr_fatal = int(curr_cas * 0.08)

        # Compute aggregate hazard rate
        if incidents:
            max_growth = max(
                DISASTER_GROWTH_FACTORS.get(getattr(i, "disaster_type", "OTHER").upper(), 0.005)
                * SEVERITY_FACTORS.get(getattr(i, "severity", "MEDIUM").upper(), 1.0)
                for i in incidents
            )
        else:
            max_growth = 0.0

        # Mitigation factor from deployed rescue teams
        mitigation = max(0.4, 1.0 - (active_teams_count * 0.04))
        effective_growth_rate = max_growth * weather_severity * mitigation

        forecast_points: list[CasualtyHorizonForecast] = []
        for h in HORIZONS:
            growth_mult = math.exp(effective_growth_rate * h)
            proj_cas = int(math.ceil(curr_cas * growth_mult))
            proj_crit = int(math.ceil(curr_crit * math.exp(effective_growth_rate * 1.1 * h)))
            proj_inj = int(math.ceil(curr_inj * growth_mult))
            proj_fatal = int(math.ceil(curr_fatal + (proj_crit * 0.05 * (h / 30.0))))

            confidence = max(0.60, round(0.95 - (h * 0.004), 2))

            forecast_points.append(
                CasualtyHorizonForecast(
                    horizon_minutes=h,
                    expected_casualties=proj_cas,
                    critical_patients=proj_crit,
                    injured=proj_inj,
                    fatalities=proj_fatal,
                    confidence=confidence,
                )
            )

        trend = "INCREASING" if effective_growth_rate > 0.005 else "STABLE"
        if not incidents:
            trend = "MINIMAL"

        return CasualtyForecastDTO(
            current_casualties=curr_cas,
            current_critical=curr_crit,
            current_injured=curr_inj,
            current_fatalities=curr_fatal,
            forecast=forecast_points,
            trend_summary=trend,
        )

    @classmethod
    def forecast_hospitals(
        cls,
        hospitals: list[Any],
        casualty_forecast: CasualtyForecastDTO,
    ) -> list[HospitalLoadForecastDTO]:
        """
        Projects ER and ICU occupancy saturation across city hospitals.
        """
        if not hospitals:
            return []

        results: list[HospitalLoadForecastDTO] = []
        num_hospitals = len(hospitals)

        for h in hospitals:
            total_beds = getattr(h, "total_beds", 100) or 100
            avail_beds = getattr(h, "available_beds", 20) or 0
            icu_cap = getattr(h, "icu_capacity", 20) or 20
            avail_icu = getattr(h, "available_icu", 5) or 0

            occupied_beds = max(0, total_beds - avail_beds)
            occupied_icu = max(0, icu_cap - avail_icu)

            curr_bed_occ = round((occupied_beds / max(1, total_beds)) * 100.0, 1)
            curr_icu_occ = round((occupied_icu / max(1, icu_cap)) * 100.0, 1)

            horizon_loads: list[HospitalHorizonLoad] = []
            overload_min: float | None = None

            for pt in casualty_forecast.forecast:
                h_min = pt.horizon_minutes
                # Distributed incoming admissions
                exp_adm = int(math.ceil(pt.expected_casualties / num_hospitals))
                exp_crit_adm = int(math.ceil(pt.critical_patients / num_hospitals))

                proj_occ_beds = occupied_beds + int(exp_adm * (h_min / 60.0))
                proj_occ_icu = occupied_icu + int(exp_crit_adm * (h_min / 60.0))

                proj_bed_pct = round((proj_occ_beds / max(1, total_beds)) * 100.0, 1)
                proj_icu_pct = round((proj_occ_icu / max(1, icu_cap)) * 100.0, 1)

                is_over = proj_bed_pct >= 100.0 or proj_icu_pct >= 100.0

                if proj_icu_pct >= 100.0 or proj_bed_pct >= 100.0:
                    status = "OVERLOAD"
                    if overload_min is None:
                        overload_min = float(h_min)
                elif proj_icu_pct >= 90.0 or proj_bed_pct >= 90.0:
                    status = "CRITICAL"
                elif proj_icu_pct >= 80.0 or proj_bed_pct >= 80.0:
                    status = "WARNING"
                elif proj_icu_pct >= 65.0:
                    status = "ELEVATED"
                else:
                    status = "NORMAL"

                horizon_loads.append(
                    HospitalHorizonLoad(
                        horizon_minutes=h_min,
                        projected_bed_occupancy_percent=proj_bed_pct,
                        projected_icu_occupancy_percent=proj_icu_pct,
                        expected_admissions=exp_adm,
                        status=status,
                        is_overloaded=is_over,
                    )
                )

            current_status = "NORMAL"
            if curr_icu_occ >= 90.0 or curr_bed_occ >= 90.0:
                current_status = "CRITICAL"
            elif curr_icu_occ >= 80.0 or curr_bed_occ >= 80.0:
                current_status = "WARNING"

            results.append(
                HospitalLoadForecastDTO(
                    hospital_id=getattr(h, "id", 0) or getattr(h, "hospital_id", 0),
                    name=getattr(h, "name", "Hospital"),
                    latitude=getattr(h, "latitude", 0.0),
                    longitude=getattr(h, "longitude", 0.0),
                    total_beds=total_beds,
                    available_beds=avail_beds,
                    icu_capacity=icu_cap,
                    available_icu=avail_icu,
                    current_bed_occupancy_percent=curr_bed_occ,
                    current_icu_occupancy_percent=curr_icu_occ,
                    forecast=horizon_loads,
                    expected_overload_minutes=overload_min,
                    status=current_status,
                )
            )

        return results

    @classmethod
    def forecast_resources(
        cls,
        resources: list[Any],
        incidents: list[Any],
    ) -> list[ResourceDemandForecastDTO]:
        """
        Projects fleet requirements and shortages across vehicle types.
        """
        categories = ["AMBULANCE", "FIRE_TRUCK", "RESCUE_BOAT", "POLICE_PATROL", "DRONE"]
        results: list[ResourceDemandForecastDTO] = []

        total_critical = sum(getattr(i, "critical_patients", 0) or 0 for i in incidents)
        total_incidents = len(incidents)

        for cat in categories:
            matching = [r for r in resources if getattr(r, "vehicle_type", "").upper() == cat]
            avail = len(
                [r for r in matching if getattr(r, "status", "AVAILABLE").upper() == "AVAILABLE"]
            )
            deployed = len(matching) - avail

            # Demand baseline
            if cat == "AMBULANCE":
                base_req = max(1, int(math.ceil(total_critical * 0.8 + total_incidents * 0.5)))
            elif cat == "FIRE_TRUCK":
                fire_cnt = len(
                    [
                        i
                        for i in incidents
                        if getattr(i, "disaster_type", "").upper()
                        in ["FIRE", "WILDFIRE", "GAS_LEAK"]
                    ]
                )
                base_req = max(1, fire_cnt * 2) if fire_cnt > 0 else 1
            elif cat == "RESCUE_BOAT":
                flood_cnt = len(
                    [
                        i
                        for i in incidents
                        if getattr(i, "disaster_type", "").upper() in ["FLOOD", "STORM", "TSUNAMI"]
                    ]
                )
                base_req = max(1, flood_cnt * 2) if flood_cnt > 0 else 0
            elif cat == "POLICE_PATROL":
                base_req = max(1, total_incidents)
            else:
                base_req = max(1, int(math.ceil(total_incidents * 0.5)))

            if not incidents:
                base_req = 0

            horizon_demands: list[ResourceHorizonDemand] = []
            max_shortage = 0

            for h in HORIZONS:
                scale = 1.0 + (h / 60.0) * 0.4
                req = int(math.ceil(base_req * scale))
                shortage = max(0, req - avail)
                if shortage > max_shortage:
                    max_shortage = shortage

                util = (
                    round((req / max(1, avail + deployed)) * 100.0, 1)
                    if (avail + deployed)
                    else 0.0
                )

                if shortage > 3:
                    urg = "CRITICAL"
                elif shortage > 0:
                    urg = "HIGH"
                elif util > 85.0:
                    urg = "MEDIUM"
                else:
                    urg = "LOW"

                horizon_demands.append(
                    ResourceHorizonDemand(
                        horizon_minutes=h,
                        required_count=req,
                        projected_shortage=shortage,
                        utilization_percent=util,
                        urgency_level=urg,
                    )
                )

            shortage_risk = (
                "CRITICAL" if max_shortage > 3 else ("HIGH" if max_shortage > 0 else "LOW")
            )

            results.append(
                ResourceDemandForecastDTO(
                    resource_type=cat,
                    current_available=avail,
                    current_deployed=deployed,
                    forecast=horizon_demands,
                    shortage_risk_level=shortage_risk,
                )
            )

        return results

    @classmethod
    def forecast_disaster_risk(
        cls,
        incidents: list[Any],
        weather_severity: float = 1.0,
    ) -> list[DisasterRiskForecastDTO]:
        """
        Projects composite spatial risk and propagation radius for active incidents.
        """
        results: list[DisasterRiskForecastDTO] = []
        for inc in incidents:
            d_type = getattr(inc, "disaster_type", "OTHER").upper()
            sev = getattr(inc, "severity", "MEDIUM").upper()
            radius = getattr(inc, "affected_radius_meters", 500.0) or 500.0

            sev_mult = SEVERITY_FACTORS.get(sev, 1.0)
            base_growth = DISASTER_GROWTH_FACTORS.get(d_type, 0.005)

            score = min(
                0.98, max(0.15, (sev_mult / 2.5) * 0.6 + (weather_severity - 1.0) * 0.2 + 0.2)
            )

            if score >= 0.75:
                risk_lvl = "CRITICAL"
            elif score >= 0.55:
                risk_lvl = "HIGH"
            elif score >= 0.35:
                risk_lvl = "MODERATE"
            else:
                risk_lvl = "LOW"

            radius_forecast: dict[str, float] = {}
            for h in HORIZONS:
                exp_rad = radius * (1.0 + (base_growth * weather_severity * h))
                radius_forecast[f"{h}m"] = round(exp_rad, 1)

            factors = [
                f"Disaster type: {d_type}",
                f"Severity rating: {sev}",
                f"Environmental multiplier: {weather_severity:.1f}x",
            ]
            if getattr(inc, "critical_patients", 0) > 0:
                factors.append(f"{inc.critical_patients} critical patients at scene")

            trend = "INCREASING" if base_growth > 0.008 else "STABLE"

            results.append(
                DisasterRiskForecastDTO(
                    incident_id=getattr(inc, "id", 0) or getattr(inc, "incident_id", 0),
                    disaster_type=d_type,
                    severity=sev,
                    latitude=getattr(inc, "latitude", 0.0),
                    longitude=getattr(inc, "longitude", 0.0),
                    risk_level=risk_lvl,
                    risk_score=round(score, 3),
                    trend=trend,
                    spread_radius_forecast=radius_forecast,
                    confidence=0.88,
                    contributing_factors=factors,
                )
            )

        return results

    @classmethod
    def forecast_fire_spread(
        cls,
        incidents: list[Any],
        wind_speed_kmh: float = 15.0,
    ) -> list[FireSpreadForecastDTO]:
        """
        Projects multi-horizon fire propagation envelopes.
        """
        fires = [
            i for i in incidents if getattr(i, "disaster_type", "").upper() in ["FIRE", "WILDFIRE"]
        ]
        results: list[FireSpreadForecastDTO] = []

        for f in fires:
            inc_id = getattr(f, "id", 0) or getattr(f, "incident_id", 0)
            base_rad = getattr(f, "affected_radius_meters", 300.0) or 300.0
            sev = getattr(f, "severity", "HIGH").upper()
            sev_mult = SEVERITY_FACTORS.get(sev, 1.5)

            velocity = round((wind_speed_kmh * 0.15) + (sev_mult * 2.0), 2)
            direction = 45.0  # North-East vector

            zones: list[FireSpreadZoneDTO] = [
                FireSpreadZoneDTO(
                    horizon_minutes=0,
                    radius_meters=round(base_rad, 1),
                    risk_level="CRITICAL",
                    estimated_population_impact=int(base_rad * 0.8),
                )
            ]

            for h in HORIZONS:
                rad = base_rad + (velocity * (h / 60.0) * 500.0)
                risk = "CRITICAL" if h <= 15 else ("HIGH" if h <= 30 else "MODERATE")
                pop = int(rad * 0.9)
                zones.append(
                    FireSpreadZoneDTO(
                        horizon_minutes=h,
                        radius_meters=round(rad, 1),
                        risk_level=risk,
                        estimated_population_impact=pop,
                    )
                )

            results.append(
                FireSpreadForecastDTO(
                    incident_id=inc_id,
                    disaster_type=getattr(f, "disaster_type", "FIRE"),
                    center_latitude=getattr(f, "latitude", 0.0),
                    center_longitude=getattr(f, "longitude", 0.0),
                    spread_direction_degrees=direction,
                    spread_velocity_kmh=velocity,
                    zones=zones,
                )
            )

        return results

    @classmethod
    def forecast_flood_risk(
        cls,
        incidents: list[Any],
        rainfall_mm: float = 20.0,
    ) -> list[FloodRiskForecastDTO]:
        """
        Projects flood inundation and evacuation urgency.
        """
        floods = [
            i
            for i in incidents
            if getattr(i, "disaster_type", "").upper() in ["FLOOD", "STORM", "TSUNAMI"]
        ]
        results: list[FloodRiskForecastDTO] = []

        for fl in floods:
            inc_id = getattr(fl, "id", 0) or getattr(fl, "incident_id", 0)
            sev = getattr(fl, "severity", "HIGH").upper()
            sev_mult = SEVERITY_FACTORS.get(sev, 1.5)

            water_lvl = round(1.2 + (rainfall_mm * 0.04) * sev_mult, 2)
            area = round(1.5 * sev_mult + (rainfall_mm * 0.05), 2)
            bldgs = int(area * 45)

            urgency = "CRITICAL" if water_lvl > 2.5 else ("HIGH" if water_lvl > 1.8 else "MODERATE")
            closure = "HIGH" if water_lvl > 1.5 else "MODERATE"

            results.append(
                FloodRiskForecastDTO(
                    incident_id=inc_id,
                    affected_area_sq_km=area,
                    water_level_meters=water_lvl,
                    road_closure_risk=closure,
                    buildings_at_risk_count=bldgs,
                    evacuation_urgency=urgency,
                )
            )

        return results
