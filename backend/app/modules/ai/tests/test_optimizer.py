"""
Unit tests for AI Decision Engine Global Assignment Optimizer.
"""

from app.modules.ai.decision_engine.optimizer import GlobalAssignmentOptimizer
from app.modules.ai.schemas import DecisionCandidateDTO, IncidentStateDTO


def test_global_optimization_resolves_competing_incidents() -> None:
    # Incident 1 is CRITICAL
    inc1 = IncidentStateDTO(
        incident_id=101,
        title="Critical Cardiac Emergency",
        disaster_type="MEDICAL",
        severity="CRITICAL",
        latitude=30.73,
        longitude=76.77,
        critical_patients=2,
    )

    # Incident 2 is MEDIUM
    inc2 = IncidentStateDTO(
        incident_id=102,
        title="Minor Fall",
        disaster_type="MEDICAL",
        severity="MEDIUM",
        latitude=30.74,
        longitude=76.78,
    )

    # Candidate options for Incident 1
    cand_inc1_amb1 = DecisionCandidateDTO(
        resource_id=1,
        resource_name="Ambulance A1",
        vehicle_type="AMBULANCE",
        incident_id=101,
        eta_minutes=4.0,
        distance_km=2.0,
        suitability=0.90,
        constraints_passed=True,
    )
    cand_inc1_amb2 = DecisionCandidateDTO(
        resource_id=2,
        resource_name="Ambulance A2",
        vehicle_type="AMBULANCE",
        incident_id=101,
        eta_minutes=25.0,
        distance_km=15.0,
        suitability=0.35,
        constraints_passed=True,
    )

    # Candidate options for Incident 2
    cand_inc2_amb1 = DecisionCandidateDTO(
        resource_id=1,
        resource_name="Ambulance A1",
        vehicle_type="AMBULANCE",
        incident_id=102,
        eta_minutes=3.0,
        distance_km=1.2,
        suitability=0.94,
        constraints_passed=True,
    )
    cand_inc2_amb2 = DecisionCandidateDTO(
        resource_id=2,
        resource_name="Ambulance A2",
        vehicle_type="AMBULANCE",
        incident_id=102,
        eta_minutes=8.0,
        distance_km=4.5,
        suitability=0.70,
        constraints_passed=True,
    )

    candidates_by_incident = {
        101: [cand_inc1_amb1, cand_inc1_amb2],
        102: [cand_inc2_amb1, cand_inc2_amb2],
    }

    # Run Kuhn-Munkres global optimization
    assignments = GlobalAssignmentOptimizer.solve_optimal_assignment(
        incidents=[inc1, inc2],
        candidates_by_incident=candidates_by_incident,
    )

    # Global optimization prioritizes critical incident for Amb 1
    assert assignments[101].resource_id == 1
    # Incident 2 gets Amb 2
    assert assignments[102].resource_id == 2
