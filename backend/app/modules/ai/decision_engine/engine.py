"""
AegisAI Decision Engine — Core Engine Orchestrator.

Main entrypoint coordinating:
State Aggregation -> Prediction -> Candidate Generation -> Constraints ->
Scoring -> Policy Optimization -> Explainability -> Fallback Recovery.
"""

from typing import Any

import structlog

from app.modules.ai.decision_engine.candidates import CandidateGenerator
from app.modules.ai.decision_engine.policies import (
    DecisionPolicy,
    MLAssistedPolicy,
    NearestResourcePolicy,
    OptimizationPolicy,
    WeightedDispatchPolicy,
)
from app.modules.ai.enums import PolicyType
from app.modules.ai.schemas import (
    DecisionState,
    DispatchScoringPolicyConfig,
)

logger = structlog.get_logger("aegis_ai.decision_engine.orchestrator")


class DecisionEngine:
    """
    Production AI Decision Intelligence Engine for AegisAI.
    """

    def __init__(self) -> None:
        self.candidate_generator = CandidateGenerator()
        self.policies: dict[PolicyType, DecisionPolicy] = {
            PolicyType.BASELINE: NearestResourcePolicy(self.candidate_generator),
            PolicyType.HEURISTIC: WeightedDispatchPolicy(self.candidate_generator),
            PolicyType.OPTIMIZED: OptimizationPolicy(self.candidate_generator),
            PolicyType.ML_ASSISTED: MLAssistedPolicy(self.candidate_generator),
        }

    async def generate_decisions(
        self,
        state: DecisionState,
        policy_type: PolicyType = PolicyType.OPTIMIZED,
        custom_weights: DispatchScoringPolicyConfig | None = None,
    ) -> list[dict[str, Any]]:
        """
        Executes decision generation using the requested policy with guaranteed fallback.

        Fallback Hierarchy:
        OPTIMIZED / ML_ASSISTED -> HEURISTIC -> BASELINE
        """
        if not state.incidents:
            logger.info("decision_engine_no_active_incidents")
            return []

        primary_policy = self.policies.get(policy_type, self.policies[PolicyType.OPTIMIZED])

        try:
            logger.info("decision_engine_running_policy", policy=policy_type.value)
            decisions = await primary_policy.generate_decisions(state, custom_weights)
            if decisions:
                return decisions
        except Exception as err:
            logger.warning(
                "primary_policy_execution_failed_triggering_fallback",
                policy=policy_type.value,
                error=str(err),
            )

        # Fallback 1: Weighted Heuristic
        if policy_type != PolicyType.HEURISTIC:
            try:
                logger.info("decision_engine_fallback_to_heuristic")
                heuristic_policy = self.policies[PolicyType.HEURISTIC]
                decisions = await heuristic_policy.generate_decisions(state, custom_weights)
                if decisions:
                    return decisions
            except Exception as err:
                logger.warning("heuristic_fallback_failed", error=str(err))

        # Fallback 2: Nearest Resource Baseline
        if policy_type != PolicyType.BASELINE:
            try:
                logger.info("decision_engine_fallback_to_baseline")
                baseline_policy = self.policies[PolicyType.BASELINE]
                return await baseline_policy.generate_decisions(state, custom_weights)
            except Exception as err:
                logger.error("baseline_fallback_failed", error=str(err))

        return []
