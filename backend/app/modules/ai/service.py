"""
AegisAI AI Module — Business Service Layer.

Implements end-to-end orchestration for the AI Decision Intelligence Engine:
- Decision generation across multiple policies
- Human-in-the-loop lifecycle management (Approve, Reject, Modify)
- Transaction-safe dispatch execution via AssignmentService
- Explainability generation (XAI + Ollama)
- Policy benchmarking and What-If hypothetical simulation
- Real-time event broadcasting
"""

from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy.orm import Session

from app.modules.ai.decision_engine.engine import DecisionEngine
from app.modules.ai.decision_engine.evaluator import DecisionEvaluator
from app.modules.ai.decision_engine.state import StateAggregator
from app.modules.ai.enums import DecisionStatus, DecisionType, ExecutionMode, FeedbackType
from app.modules.ai.events import AIDecisionEventPublisher
from app.modules.ai.exceptions import (
    DecisionExecutionException,
    DecisionNotFoundException,
    DecisionStateTransitionException,
)
from app.modules.ai.models import AIDecision
from app.modules.ai.providers.ollama_provider import OllamaExplanationProvider
from app.modules.ai.repository import AIDecisionRepository
from app.modules.ai.schemas import (
    AIDecisionApproveRequest,
    AIDecisionCreateRequest,
    AIDecisionFeedbackRequest,
    AIDecisionModifyRequest,
    AIDecisionRejectRequest,
    AIDecisionResponse,
    BenchmarkRequest,
    BenchmarkResponse,
    DecisionState,
    LLMExplanationResponse,
    WhatIfDecisionRequest,
    WhatIfDecisionResponse,
)
from app.modules.audit.service import AuditService
from app.modules.auth.models import User
from app.services.assignment_service import AssignmentService

logger = structlog.get_logger("aegis_ai.ai.service")


class AIDecisionService:
    """Core domain service orchestrating AI Decision Intelligence."""

    def __init__(self) -> None:
        self.engine = DecisionEngine()
        self.llm_provider = OllamaExplanationProvider()

    async def generate_decisions(
        self,
        db: Session,
        request: AIDecisionCreateRequest,
        current_user: User | None = None,
    ) -> list[AIDecisionResponse]:
        """
        Builds decision state, executes mathematical policy optimization,
        persists recommendations, and broadcasts real-time events.
        """
        # 1. State Aggregation
        if request.simulation_id:
            state = StateAggregator.build_state_from_simulation(
                db=db,
                simulation_id=request.simulation_id,
                execution_mode=request.execution_mode,
            )
        else:
            state = StateAggregator.build_state_from_db(
                db=db,
                incident_ids=request.incident_ids,
                execution_mode=request.execution_mode,
            )

        if not state.incidents:
            logger.info("no_active_incidents_to_evaluate")
            return []

        # 2. Mathematical Optimization & Decision Generation
        raw_decisions = await self.engine.generate_decisions(
            state=state,
            policy_type=request.policy_type,
            custom_weights=request.custom_weights,
        )

        # 3. Persistence & Event Publishing
        created_responses: list[AIDecisionResponse] = []
        for raw in raw_decisions:
            raw["simulation_id"] = request.simulation_id
            raw["input_state_snapshot"] = {
                "incidents_count": len(state.incidents),
                "resources_count": len(state.resources),
                "weather": state.weather.condition,
            }

            db_decision = AIDecisionRepository.create_decision(db, raw)

            AIDecisionRepository.save_event(
                db=db,
                decision_id=db_decision.id,
                event_type="AI_DECISION_GENERATED",
                user_id=current_user.id if current_user else None,
                payload={"policy": request.policy_type.value},
            )

            resp_dto = AIDecisionResponse.model_validate(db_decision)
            created_responses.append(resp_dto)

            # Fire and forget real-time WebSocket broadcast
            await AIDecisionEventPublisher.publish_decision_generated(
                resp_dto.model_dump(mode="json")
            )

        logger.info(
            "ai_decisions_generated_successfully",
            count=len(created_responses),
            policy=request.policy_type.value,
        )
        return created_responses

    def get_decision(self, db: Session, identifier: str | int) -> AIDecision:
        """Fetch decision by ID or UUID with exception handling."""
        decision = AIDecisionRepository.get_by_id_or_uuid(db, identifier)
        if not decision:
            raise DecisionNotFoundException(identifier)
        return decision

    def list_decisions(
        self,
        db: Session,
        status: str | None = None,
        decision_type: str | None = None,
        incident_id: int | None = None,
        simulation_id: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[AIDecisionResponse], int]:
        """List persisted decisions with filters and pagination."""
        items, total = AIDecisionRepository.list_decisions(
            db=db,
            status=status,
            decision_type=decision_type,
            incident_id=incident_id,
            simulation_id=simulation_id,
            skip=skip,
            limit=limit,
        )
        return [AIDecisionResponse.model_validate(item) for item in items], total

    async def approve_decision(
        self,
        db: Session,
        identifier: str | int,
        request: AIDecisionApproveRequest,
        current_user: User,
    ) -> AIDecisionResponse:
        """
        Approve an AI recommendation and optionally execute automated dispatch.
        """
        decision = self.get_decision(db, identifier)

        if decision.status in [DecisionStatus.APPROVED.value, DecisionStatus.EXECUTED.value]:
            return AIDecisionResponse.model_validate(decision)

        if decision.status not in [
            DecisionStatus.REVIEW_REQUIRED.value,
            DecisionStatus.GENERATED.value,
            DecisionStatus.MODIFIED.value,
        ]:
            raise DecisionStateTransitionException(decision.status, DecisionStatus.APPROVED.value)

        now = datetime.now(timezone.utc)
        decision.status = DecisionStatus.APPROVED.value
        decision.approved_by = current_user.id
        decision.approved_at = now
        db.commit()
        db.refresh(decision)

        AIDecisionRepository.save_event(
            db=db,
            decision_id=decision.id,
            event_type="AI_DECISION_APPROVED",
            user_id=current_user.id,
            payload={"notes": request.notes},
        )
        AuditService.log(
            db=db,
            action="AI_DECISION_APPROVED",
            entity_type="ai_decisions",
            entity_id=decision.id,
            user_id=current_user.id,
            details={"notes": request.notes, "decision_uuid": decision.decision_uuid},
        )

        resp_dto = AIDecisionResponse.model_validate(decision)
        await AIDecisionEventPublisher.publish_decision_approved(resp_dto.model_dump(mode="json"))

        # Auto-execute if requested
        if request.auto_execute:
            return await self.execute_decision(
                db=db,
                identifier=decision.id,
                current_user=current_user,
            )

        return resp_dto

    async def reject_decision(
        self,
        db: Session,
        identifier: str | int,
        request: AIDecisionRejectRequest,
        current_user: User,
    ) -> AIDecisionResponse:
        """
        Reject an AI recommendation and record commander reason.
        """
        decision = self.get_decision(db, identifier)

        if decision.status not in [
            DecisionStatus.REVIEW_REQUIRED.value,
            DecisionStatus.GENERATED.value,
            DecisionStatus.MODIFIED.value,
        ]:
            raise DecisionStateTransitionException(decision.status, DecisionStatus.REJECTED.value)

        decision.status = DecisionStatus.REJECTED.value
        decision.rejection_reason = request.rejection_reason
        db.commit()
        db.refresh(decision)

        # Record audit event and feedback
        AIDecisionRepository.save_event(
            db=db,
            decision_id=decision.id,
            event_type="AI_DECISION_REJECTED",
            user_id=current_user.id,
            payload={"rejection_reason": request.rejection_reason},
        )
        AuditService.log(
            db=db,
            action="AI_DECISION_REJECTED",
            entity_type="ai_decisions",
            entity_id=decision.id,
            user_id=current_user.id,
            details={"rejection_reason": request.rejection_reason, "decision_uuid": decision.decision_uuid},
        )
        AIDecisionRepository.save_feedback(
            db=db,
            decision_id=decision.id,
            user_id=current_user.id,
            feedback_type=FeedbackType.REJECTED.value,
            actual_outcome={"status": "REJECTED_BY_COMMANDER"},
            comments=request.rejection_reason,
        )

        resp_dto = AIDecisionResponse.model_validate(decision)
        await AIDecisionEventPublisher.publish_decision_rejected(resp_dto.model_dump(mode="json"))
        return resp_dto

    async def modify_decision(
        self,
        db: Session,
        identifier: str | int,
        request: AIDecisionModifyRequest,
        current_user: User,
    ) -> AIDecisionResponse:
        """
        Modify recommended resource or destination hospital before approval.
        """
        decision = self.get_decision(db, identifier)

        if decision.status not in [
            DecisionStatus.REVIEW_REQUIRED.value,
            DecisionStatus.GENERATED.value,
            DecisionStatus.MODIFIED.value,
        ]:
            raise DecisionStateTransitionException(decision.status, DecisionStatus.MODIFIED.value)

        updated_action = dict(decision.action)
        if request.override_resource_id is not None:
            updated_action["resource_id"] = request.override_resource_id
            decision.resource_id = request.override_resource_id
        if request.override_hospital_id is not None:
            updated_action["destination_hospital_id"] = request.override_hospital_id
            decision.destination_id = request.override_hospital_id

        decision.action = updated_action
        decision.modification_notes = request.modification_notes
        decision.status = DecisionStatus.MODIFIED.value
        db.commit()
        db.refresh(decision)

        AIDecisionRepository.save_event(
            db=db,
            decision_id=decision.id,
            event_type="AI_DECISION_MODIFIED",
            user_id=current_user.id,
            payload={"notes": request.modification_notes},
        )
        AuditService.log(
            db=db,
            action="AI_DECISION_MODIFIED",
            entity_type="ai_decisions",
            entity_id=decision.id,
            user_id=current_user.id,
            details={"notes": request.modification_notes, "updated_action": updated_action, "decision_uuid": decision.decision_uuid},
        )
        AIDecisionRepository.save_feedback(
            db=db,
            decision_id=decision.id,
            user_id=current_user.id,
            feedback_type=FeedbackType.MODIFIED.value,
            actual_outcome={"modified_action": updated_action},
            comments=request.modification_notes,
        )

        resp_dto = AIDecisionResponse.model_validate(decision)

        if request.auto_execute:
            return await self.execute_decision(
                db=db,
                identifier=decision.id,
                current_user=current_user,
            )

        return resp_dto

    async def execute_decision(
        self,
        db: Session,
        identifier: str | int,
        current_user: User,
    ) -> AIDecisionResponse:
        """
        Executes approved decision by dispatching via the existing AssignmentService.
        Leverages SELECT FOR UPDATE database locking to eliminate race conditions.
        """
        decision = self.get_decision(db, identifier)

        if decision.status == DecisionStatus.EXECUTED.value:
            return AIDecisionResponse.model_validate(decision)

        # M7 FIX: Require the decision to have been approved (or commander-modified)
        # before it can be dispatched. Previously this guard was missing, allowing
        # REVIEW_REQUIRED decisions to be directly executed, bypassing human approval.
        _executable_statuses = {
            DecisionStatus.APPROVED.value,
            DecisionStatus.MODIFIED.value,
        }
        if decision.status not in _executable_statuses:
            raise DecisionStateTransitionException(
                f"{decision.status} (must be APPROVED or MODIFIED first)",
                DecisionStatus.EXECUTED.value,
            )

        if decision.decision_type != DecisionType.DISPATCH_RESOURCE.value:
            decision.status = DecisionStatus.EXECUTED.value
            decision.executed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(decision)
            return AIDecisionResponse.model_validate(decision)

        action = decision.action
        incident_id = action.get("incident_id") or decision.incident_id
        resource_id = action.get("resource_id") or decision.resource_id

        if not incident_id or not resource_id:
            raise DecisionExecutionException(
                "Missing incident_id or resource_id in decision action."
            )

        try:
            d_uuid_short = decision.decision_uuid[:8]
            rec_notes = action.get("recommended_notes", "")
            dispatch_notes = f"[AI Decision {d_uuid_short}] {rec_notes}"

            # Dispatch using existing transaction-safe AssignmentService
            assignment = AssignmentService.create_assignment(
                db=db,
                incident_id=incident_id,
                team_id=resource_id,
                dispatched_by=current_user.id,
                notes=dispatch_notes,
                estimated_arrival_minutes=action.get("estimated_arrival_minutes"),
                distance_km=action.get("distance_km"),
                route_geometry=action.get("route_geometry"),
            )

            now = datetime.now(timezone.utc)
            decision.status = DecisionStatus.EXECUTED.value
            decision.executed_at = now
            db.commit()
            db.refresh(decision)

            AIDecisionRepository.save_event(
                db=db,
                decision_id=decision.id,
                event_type="AI_DECISION_EXECUTED",
                user_id=current_user.id,
                payload={"assignment_id": assignment.id},
            )
            AuditService.log(
                db=db,
                action="AI_DECISION_EXECUTED",
                entity_type="ai_decisions",
                entity_id=decision.id,
                user_id=current_user.id,
                details={"decision_uuid": decision.decision_uuid, "assignment_id": assignment.id},
            )

            resp_dto = AIDecisionResponse.model_validate(decision)
            await AIDecisionEventPublisher.publish_decision_executed(
                resp_dto.model_dump(mode="json")
            )
            return resp_dto

        except Exception as e:
            logger.error("decision_execution_failed", decision_id=decision.id, error=str(e))
            await AIDecisionEventPublisher.publish_decision_failed(decision.id, str(e))
            raise DecisionExecutionException(str(e)) from e

    async def get_explanation(
        self,
        db: Session,
        identifier: str | int,
    ) -> LLMExplanationResponse:
        """
        Generates or retrieves operational LLM briefing for a decision.
        """
        decision = self.get_decision(db, identifier)
        decision_dict = {
            "id": decision.id,
            "decision_uuid": decision.decision_uuid,
            "action": decision.action,
            "reasoning": decision.reasoning,
            "expected_impact": decision.expected_impact,
            "alternatives": decision.alternatives,
            "priority": decision.priority,
        }
        return await self.llm_provider.generate_briefing(decision_dict)

    async def benchmark_policies(
        self,
        db: Session,
        request: BenchmarkRequest,
    ) -> BenchmarkResponse:
        """
        Runs mathematical comparison of decision policies against the current state.
        """
        state = StateAggregator.build_state_from_db(db=db, incident_ids=request.incident_ids)
        return await DecisionEvaluator.evaluate_policies(
            state=state,
            policies_to_compare=request.policies_to_compare,
        )

    async def run_what_if_analysis(
        self,
        db: Session,
        request: WhatIfDecisionRequest,
    ) -> WhatIfDecisionResponse:
        """
        Simulates what-if disaster conditions on an isolated state snapshot
        without modifying the active database.
        """
        baseline_state = StateAggregator.build_state_from_db(db=db)

        # 1. Generate Baseline decisions
        baseline_raw = await self.engine.generate_decisions(
            state=baseline_state,
            policy_type=request.policy_type,
        )

        # 2. Build Modified What-If State
        modified_roads = [
            r.model_copy(update={"is_blocked": True, "blocked_reason": "SIMULATED_DEBRIS"})
            if r.road_id in request.hypothetical_blocked_roads
            else r
            for r in baseline_state.roads
        ]

        modified_hospitals = [
            h.model_copy(update={"is_operational": False, "available_beds": 0})
            if h.hospital_id in request.hypothetical_disabled_hospitals
            else h
            for h in baseline_state.hospitals
        ]

        weather_copy = baseline_state.weather
        if request.hypothetical_severe_weather:
            weather_copy = baseline_state.weather.model_copy(
                update={"condition": request.hypothetical_severe_weather, "severity": "CRITICAL"}
            )

        what_if_state = DecisionState(
            incidents=baseline_state.incidents,
            resources=baseline_state.resources,
            hospitals=modified_hospitals,
            shelters=baseline_state.shelters,
            roads=modified_roads,
            weather=weather_copy,
            traffic=baseline_state.traffic,
            simulation_id=request.simulation_id,
            execution_mode=ExecutionMode.WHAT_IF,
            timestamp=baseline_state.timestamp,
        )

        # 3. Generate What-If decisions
        what_if_raw = await self.engine.generate_decisions(
            state=what_if_state,
            policy_type=request.policy_type,
        )

        base_dtos = [
            AIDecisionResponse(
                id=idx + 1,
                decision_uuid=f"sim-base-{idx + 1}",
                decision_type=DecisionType(d["decision_type"]),
                action=d["action"],
                incident_id=d.get("incident_id"),
                resource_id=d.get("resource_id"),
                destination_id=d.get("destination_id"),
                priority=d.get("priority", "MEDIUM"),
                score=d.get("score", 0.0),
                confidence=d.get("confidence", 0.0),
                reasoning=d.get("reasoning", []),
                constraints=d.get("constraints", {}),
                expected_impact=d.get("expected_impact", {}),
                alternatives=d.get("alternatives", []),
                status=DecisionStatus.GENERATED,
                policy_name=d.get("policy_name", "OPTIMIZED"),
                policy_version="1.0.0",
                model_name="llama3.2:3b",
                model_version="1.0.0",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            for idx, d in enumerate(baseline_raw)
        ]

        what_if_dtos = [
            AIDecisionResponse(
                id=idx + 100,
                decision_uuid=f"sim-whatif-{idx + 1}",
                decision_type=DecisionType(d["decision_type"]),
                action=d["action"],
                incident_id=d.get("incident_id"),
                resource_id=d.get("resource_id"),
                destination_id=d.get("destination_id"),
                priority=d.get("priority", "MEDIUM"),
                score=d.get("score", 0.0),
                confidence=d.get("confidence", 0.0),
                reasoning=d.get("reasoning", []),
                constraints=d.get("constraints", {}),
                expected_impact=d.get("expected_impact", {}),
                alternatives=d.get("alternatives", []),
                status=DecisionStatus.GENERATED,
                policy_name=d.get("policy_name", "OPTIMIZED"),
                policy_version="1.0.0",
                model_name="llama3.2:3b",
                model_version="1.0.0",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            for idx, d in enumerate(what_if_raw)
        ]

        avg_base_eta = sum(d.action.estimated_arrival_minutes or 0.0 for d in base_dtos) / max(
            1, len(base_dtos)
        )
        avg_whatif_eta = sum(d.action.estimated_arrival_minutes or 0.0 for d in what_if_dtos) / max(
            1, len(what_if_dtos)
        )

        impact = {
            "baseline_avg_eta_minutes": round(avg_base_eta, 2),
            "what_if_avg_eta_minutes": round(avg_whatif_eta, 2),
            "eta_impact_delta_minutes": round(avg_whatif_eta - avg_base_eta, 2),
            "blocked_roads_count": len(request.hypothetical_blocked_roads),
            "disabled_hospitals_count": len(request.hypothetical_disabled_hospitals),
            "rerouted_assignments_count": len(what_if_dtos),
        }

        roads_cnt = len(request.hypothetical_blocked_roads)
        hosps_cnt = len(request.hypothetical_disabled_hospitals)
        scen_name = f"What-If ({roads_cnt} roads blocked, {hosps_cnt} hospitals disabled)"

        return WhatIfDecisionResponse(
            scenario_name=scen_name,
            baseline_decisions=base_dtos,
            what_if_decisions=what_if_dtos,
            impact_analysis=impact,
        )

    def record_feedback(
        self,
        db: Session,
        identifier: str | int,
        request: AIDecisionFeedbackRequest,
        current_user: User,
    ) -> dict[str, Any]:
        """Record commander feedback and real-world outcome."""
        decision = self.get_decision(db, identifier)
        feedback = AIDecisionRepository.save_feedback(
            db=db,
            decision_id=decision.id,
            user_id=current_user.id,
            feedback_type=request.feedback_type.value,
            actual_outcome=request.actual_outcome,
            comments=request.comments,
        )
        return {
            "feedback_id": feedback.id,
            "decision_id": decision.id,
            "status": "RECORDED",
            "recorded_at": feedback.created_at.isoformat(),
        }
