"""
AegisAI Prediction Module — Time-Horizon Forecaster Unit Tests.

Verifies multi-horizon forecasting for casualties, hospital saturation,
resource demand deficits, and spatial disaster risk.
Compatible with Python 3.10.
"""

from unittest.mock import MagicMock

from app.modules.prediction.forecaster import TimeHorizonForecaster


class TestTimeHorizonForecaster:
    """Test suite for TimeHorizonForecaster."""

    def test_forecast_casualties_empty(self) -> None:
        """When there are no active incidents, forecast should be 0/minimal and stable."""
        res = TimeHorizonForecaster.forecast_casualties(incidents=[])
        assert res.current_casualties == 0
        assert res.trend_summary == "MINIMAL"
        assert len(res.forecast) == 4
        assert [f.horizon_minutes for f in res.forecast] == [5, 15, 30, 60]
        assert all(f.expected_casualties == 0 for f in res.forecast)

    def test_forecast_casualties_with_disaster(self) -> None:
        """Casualties should increase over time horizon and confidence should decay cleanly."""
        mock_inc = MagicMock()
        mock_inc.disaster_type = "FIRE"
        mock_inc.severity = "HIGH"
        mock_inc.estimated_casualties = 20
        mock_inc.critical_patients = 5
        mock_inc.estimated_affected_people = 50

        res = TimeHorizonForecaster.forecast_casualties(
            incidents=[mock_inc],
            weather_severity=1.2,
            active_teams_count=2,
        )

        assert res.current_casualties == 20
        assert res.current_critical == 5
        assert len(res.forecast) == 4

        # Verify monotonic growth: 5m <= 15m <= 30m <= 60m
        cas_vals = [f.expected_casualties for f in res.forecast]
        assert cas_vals[0] <= cas_vals[1] <= cas_vals[2] <= cas_vals[3]
        assert cas_vals[3] > res.current_casualties

        # Verify calibrated confidence decay
        conf_vals = [f.confidence for f in res.forecast]
        assert conf_vals[0] > conf_vals[3]
        assert all(0.5 <= c <= 1.0 for c in conf_vals if c is not None)

    def test_forecast_hospitals_overload_detection(self) -> None:
        """Hospitals nearing capacity should trigger OVERLOAD or CRITICAL status."""
        mock_hosp = MagicMock()
        mock_hosp.id = 1
        mock_hosp.name = "Emergency Trauma Hospital"
        mock_hosp.latitude = 30.73
        mock_hosp.longitude = 76.77
        mock_hosp.total_beds = 100
        mock_hosp.available_beds = 5
        mock_hosp.icu_capacity = 10
        mock_hosp.available_icu = 1  # 90% full currently

        mock_cas = MagicMock()
        mock_cas.forecast = [
            MagicMock(horizon_minutes=5, expected_casualties=20, critical_patients=6),
            MagicMock(horizon_minutes=15, expected_casualties=40, critical_patients=12),
            MagicMock(horizon_minutes=30, expected_casualties=60, critical_patients=18),
            MagicMock(horizon_minutes=60, expected_casualties=90, critical_patients=25),
        ]

        results = TimeHorizonForecaster.forecast_hospitals([mock_hosp], mock_cas)
        assert len(results) == 1
        h_res = results[0]
        assert h_res.current_icu_occupancy_percent == 90.0
        assert h_res.status == "CRITICAL"
        assert h_res.expected_overload_minutes is not None
        assert h_res.expected_overload_minutes <= 15.0

    def test_forecast_resources_shortage_calculation(self) -> None:
        """Projected shortage and critical urgency are flagged when demand exceeds units."""
        mock_team1 = MagicMock()
        mock_team1.vehicle_type = "AMBULANCE"
        mock_team1.status = "AVAILABLE"

        mock_team2 = MagicMock()
        mock_team2.vehicle_type = "AMBULANCE"
        mock_team2.status = "DEPLOYED"

        mock_inc = MagicMock()
        mock_inc.critical_patients = 10
        mock_inc.disaster_type = "FIRE"

        results = TimeHorizonForecaster.forecast_resources([mock_team1, mock_team2], [mock_inc])
        amb_res = next(r for r in results if r.resource_type == "AMBULANCE")

        assert amb_res.current_available == 1
        assert amb_res.current_deployed == 1
        assert len(amb_res.forecast) == 4
        # At +60m horizon, high demand should produce shortage > 0
        assert amb_res.forecast[-1].projected_shortage > 0
        assert amb_res.shortage_risk_level in ["HIGH", "CRITICAL"]

    def test_forecast_disaster_risk_score_bounds(self) -> None:
        """Risk score must remain bounded in [0.0, 1.0] and generate valid horizon radii."""
        mock_inc = MagicMock()
        mock_inc.id = 101
        mock_inc.disaster_type = "GAS_LEAK"
        mock_inc.severity = "CRITICAL"
        mock_inc.affected_radius_meters = 400.0
        mock_inc.latitude = 30.73
        mock_inc.longitude = 76.78
        mock_inc.critical_patients = 4

        risks = TimeHorizonForecaster.forecast_disaster_risk([mock_inc], weather_severity=1.5)
        assert len(risks) == 1
        r = risks[0]
        assert 0.0 <= r.risk_score <= 1.0
        assert r.risk_level in ["HIGH", "CRITICAL"]
        assert "5m" in r.spread_radius_forecast
        assert "60m" in r.spread_radius_forecast
        assert r.spread_radius_forecast["60m"] > r.spread_radius_forecast["5m"]

    def test_forecast_fire_spread_zones(self) -> None:
        """Fire spread forecast generates concentric envelopes expanding over time."""
        mock_fire = MagicMock()
        mock_fire.id = 201
        mock_fire.disaster_type = "WILDFIRE"
        mock_fire.severity = "CRITICAL"
        mock_fire.affected_radius_meters = 500.0
        mock_fire.latitude = 30.75
        mock_fire.longitude = 76.79

        fires = TimeHorizonForecaster.forecast_fire_spread([mock_fire], wind_speed_kmh=30.0)
        assert len(fires) == 1
        f = fires[0]
        assert len(f.zones) == 5  # 0m, 5m, 15m, 30m, 60m
        assert f.zones[0].horizon_minutes == 0
        assert f.zones[4].horizon_minutes == 60
        assert f.zones[4].radius_meters > f.zones[0].radius_meters
