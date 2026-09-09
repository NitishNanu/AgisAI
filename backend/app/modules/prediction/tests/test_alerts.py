"""
AegisAI Prediction Module — Predictive Alert Engine Unit Tests.

Verifies threshold triggers, alert deduplication cooldowns, and XAI explainability payloads.
Compatible with Python 3.10.
"""

from app.modules.prediction.alerts import PredictiveAlertEngine
from app.modules.prediction.schemas import (
    CasualtyForecastDTO,
    DisasterRiskForecastDTO,
    HospitalHorizonLoad,
    HospitalLoadForecastDTO,
    ResourceDemandForecastDTO,
    ResourceHorizonDemand,
)


class TestPredictiveAlertEngine:
    """Test suite for PredictiveAlertEngine."""

    def test_hospital_overload_alert_generation(self) -> None:
        """Hospitals with projected overload or ICU > 90% generate critical alerts."""
        PredictiveAlertEngine._last_alert_times.clear()

        mock_hosp = HospitalLoadForecastDTO(
            hospital_id=5,
            name="City Trauma Hospital",
            latitude=30.73,
            longitude=76.77,
            total_beds=100,
            available_beds=5,
            icu_capacity=20,
            available_icu=1,
            current_bed_occupancy_percent=95.0,
            current_icu_occupancy_percent=95.0,
            forecast=[
                HospitalHorizonLoad(
                    horizon_minutes=15,
                    projected_bed_occupancy_percent=98.0,
                    projected_icu_occupancy_percent=102.0,
                    expected_admissions=10,
                    status="OVERLOAD",
                    is_overloaded=True,
                )
            ],
            expected_overload_minutes=15.0,
            status="OVERLOAD",
        )

        cas = CasualtyForecastDTO()
        alerts = PredictiveAlertEngine.generate_alerts(
            casualties=cas,
            hospitals=[mock_hosp],
            resources=[],
            disaster_risks=[],
        )

        assert len(alerts) >= 1
        over_alert = next(a for a in alerts if a.type == "HOSPITAL_OVERLOAD")
        assert over_alert.severity in ["HIGH", "CRITICAL"]
        assert over_alert.related_entity_id == 5
        assert "ICU Saturation Warning" in over_alert.title
        assert len(over_alert.explanation) > 10
        assert len(over_alert.recommended_action) > 10

    def test_resource_shortage_alert_generation(self) -> None:
        """Resource demand exceeding active fleet produces shortage alert."""
        PredictiveAlertEngine._last_alert_times.clear()

        mock_res = ResourceDemandForecastDTO(
            resource_type="AMBULANCE",
            current_available=2,
            current_deployed=5,
            forecast=[
                ResourceHorizonDemand(
                    horizon_minutes=30,
                    required_count=8,
                    projected_shortage=6,
                    utilization_percent=114.0,
                    urgency_level="CRITICAL",
                )
            ],
            shortage_risk_level="CRITICAL",
        )

        alerts = PredictiveAlertEngine.generate_alerts(
            casualties=CasualtyForecastDTO(),
            hospitals=[],
            resources=[mock_res],
            disaster_risks=[],
        )

        assert len(alerts) >= 1
        res_alert = next(a for a in alerts if a.type == "RESOURCE_SHORTAGE")
        assert res_alert.severity in ["HIGH", "CRITICAL"]
        assert "AMBULANCE" in res_alert.title
        assert "mutual aid" in res_alert.recommended_action.lower()

    def test_alert_deduplication_cooldown(self) -> None:
        """Alerts should be suppressed within the cooldown window to avoid spam."""
        PredictiveAlertEngine._last_alert_times.clear()

        mock_risk = DisasterRiskForecastDTO(
            incident_id=77,
            disaster_type="FIRE",
            severity="CRITICAL",
            latitude=30.73,
            longitude=76.78,
            risk_level="CRITICAL",
            risk_score=0.92,
            trend="INCREASING",
            confidence=0.90,
            contributing_factors=["Extreme wind velocity", "High density population"],
        )

        # First emission -> Alert generated
        first_pass = PredictiveAlertEngine.generate_alerts(
            casualties=CasualtyForecastDTO(),
            hospitals=[],
            resources=[],
            disaster_risks=[mock_risk],
        )
        assert len(first_pass) == 1

        # Immediate second emission -> Suppressed by cooldown
        second_pass = PredictiveAlertEngine.generate_alerts(
            casualties=CasualtyForecastDTO(),
            hospitals=[],
            resources=[],
            disaster_risks=[mock_risk],
        )
        assert len(second_pass) == 0
