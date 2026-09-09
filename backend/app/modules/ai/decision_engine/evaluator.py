"""
AegisAI Decision Engine — Evaluator & Policy Benchmarking.

Evaluates decision outcomes across multiple policies on the same state
to compute objective performance metrics.
"""

import time
from datetime import datetime, timezone

import structlog

from app.modules.ai.decision_engine.policies import (
    MLAssistedPolicy,
    NearestResourcePolicy,
    OptimizationPolicy,
    WeightedDispatchPolicy,
)
from app.modules.ai.enums import PolicyType
from app.modules.ai.schemas import (
    BenchmarkResponse,
    DecisionState,
    StrategyBenchmarkMetric,
)

logger = structlog.get_logger("aegis_ai.decision_engine.evaluator")


class DecisionEvaluator:
    """Evaluates and benchmarks decision strategy policies."""

    POLICIES = {
        PolicyType.BASELINE: NearestResourcePolicy(),
        PolicyType.HEURISTIC: WeightedDispatchPolicy(),
        PolicyType.OPTIMIZED: OptimizationPolicy(),
        PolicyType.ML_ASSISTED: MLAssistedPolicy(),
    }

    @classmethod
    async def evaluate_policies(
        cls,
        state: DecisionState,
        policies_to_compare: list[PolicyType] | None = None,
    ) -> BenchmarkResponse:
        """
        Runs benchmark comparison across requested policies.
        """
        compare_list = policies_to_compare or [
            PolicyType.BASELINE,
            PolicyType.HEURISTIC,
            PolicyType.OPTIMIZED,
            PolicyType.ML_ASSISTED,
        ]

        metrics_list: list[StrategyBenchmarkMetric] = []
        incidents_count = len(state.incidents)
        resources_count = len([r for r in state.resources if r.availability])

        for p_type in compare_list:
            policy = cls.POLICIES.get(p_type)
            if not policy:
                continue

            start_t = time.perf_counter()
            decisions = await policy.generate_decisions(state)
            latency_ms = (time.perf_counter() - start_t) * 1000.0

            assigned_count = len(decisions)
            unassigned_count = max(0, incidents_count - assigned_count)

            etas = [
                d["action"]["estimated_arrival_minutes"]
                for d in decisions
                if d.get("action", {}).get("estimated_arrival_minutes")
            ]
            distances = [
                d["action"]["distance_km"]
                for d in decisions
                if d.get("action", {}).get("distance_km")
            ]
            scores = [d.get("score", 0.0) for d in decisions]
            confidences = [d.get("confidence", 0.0) for d in decisions]

            avg_eta = sum(etas) / max(1, len(etas)) if etas else 0.0
            max_eta = max(etas) if etas else 0.0
            total_dist = sum(distances) if distances else 0.0
            avg_score = sum(scores) / max(1, len(scores)) if scores else 0.0
            avg_conf = sum(confidences) / max(1, len(confidences)) if confidences else 0.0
            utilization = (assigned_count / max(1, resources_count)) * 100.0

            risk_red = min(96.0, max(10.0, (avg_score * 60.0) + max(0.0, 30.0 - avg_eta)))

            metric = StrategyBenchmarkMetric(
                policy_type=p_type,
                decisions_generated_count=assigned_count,
                assigned_incidents_count=assigned_count,
                unassigned_incidents_count=unassigned_count,
                average_response_time_minutes=round(avg_eta, 2),
                max_response_time_minutes=round(max_eta, 2),
                total_travel_distance_km=round(total_dist, 2),
                average_score=round(avg_score, 4),
                average_confidence=round(avg_conf, 4),
                resource_utilization_rate=round(utilization, 1),
                estimated_casualty_risk_reduction_percent=round(risk_red, 1),
                solver_latency_ms=round(latency_ms, 2),
            )
            metrics_list.append(metric)

        sorted_by_perf = sorted(
            metrics_list,
            key=lambda m: (m.average_score, -m.average_response_time_minutes),
            reverse=True,
        )
        winner = sorted_by_perf[0].policy_type if sorted_by_perf else PolicyType.OPTIMIZED

        rationale = "No active incidents to evaluate."
        if sorted_by_perf:
            w_metric = sorted_by_perf[0]
            rationale = (
                f"Policy '{winner.value}' achieved the optimal balance of response speed "
                f"({w_metric.average_response_time_minutes:.1f} min avg ETA), "
                f"composite suitability ({w_metric.average_score:.2f}), and risk mitigation."
            )

        return BenchmarkResponse(
            evaluated_at=datetime.now(timezone.utc),
            incidents_count=incidents_count,
            available_resources_count=resources_count,
            results=metrics_list,
            recommended_policy=winner,
            recommendation_rationale=rationale,
        )
