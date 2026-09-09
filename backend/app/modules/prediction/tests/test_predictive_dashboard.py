"""
AegisAI Prediction Module — Predictive Dashboard & Outcomes Tests.

Verifies the consolidated dashboard payload, granular domain queries,
and prediction outcome telemetry recording.
Compatible with Python 3.10.
"""

from unittest.mock import MagicMock

from app.modules.prediction.schemas import (
    PredictionOutcomeRecordRequest,
)
from app.modules.prediction.service import PredictionService


class TestPredictiveDashboardService:
    """Test suite for PredictionService dashboard and outcome methods."""

    def test_get_predictive_dashboard_structure(self) -> None:
        """Dashboard consolidation returns all required forecast domains and metadata."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.all.return_value = []

        res = PredictionService.get_predictive_dashboard(
            db=mock_db, simulation_id="sim-test-01", use_cache=False
        )

        assert res.prediction_source == "SIMULATION+ML"
        assert res.casualties is not None
        assert isinstance(res.hospitals, list)
        assert isinstance(res.resources, list)
        assert isinstance(res.disaster_risk, list)
        assert isinstance(res.alerts, list)
        assert res.model_metadata.model_name == "AegisAI-PredictiveEngine-v1"
        assert res.model_metadata.confidence_calibrated is True

    def test_record_outcome_updates_error(self) -> None:
        """Recording actual outcome updates record with error rate."""
        from datetime import datetime, timezone
        mock_record = MagicMock()
        mock_record.id = 12
        mock_record.prediction_type = "CASUALTY"
        mock_record.simulation_id = "sim-001"
        mock_record.incident_id = 1
        mock_record.model_name = "AegisAI-PredictiveEngine-v1"
        mock_record.model_version = "1.2.0"
        mock_record.forecast_horizon_minutes = 15
        mock_record.predicted_value = {"casualties": 80}
        mock_record.actual_value = None
        mock_record.error_rate = None
        mock_record.confidence = 0.9
        mock_record.prediction_source = "SIMULATION+ML"
        mock_record.created_at = datetime.now(timezone.utc)

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_record

        payload = PredictionOutcomeRecordRequest(
            actual_value={"actual_casualties": 85},
            error_rate=0.045,
        )

        res = PredictionService.record_outcome(mock_db, 12, payload)
        assert res.actual_value == {"actual_casualties": 85}
        assert mock_record.actual_value == {"actual_casualties": 85}
        assert mock_record.error_rate == 0.045
        assert mock_db.commit.called
