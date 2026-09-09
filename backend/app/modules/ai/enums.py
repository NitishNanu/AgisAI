"""
AegisAI — AI Decision Engine Enums.

Defines all domain enums used by the AI Decision Intelligence layer:
- DecisionType: Categories of emergency management decisions.
- DecisionStatus: Lifecycle states for human-in-the-loop decision approval.
- DecisionPriority: Operational urgency of the decision.
- PolicyType: Strategy used to generate the decision.
- FeedbackType: Types of commander feedback captured for auditing and ML training.
"""

from enum import Enum


class DecisionType(str, Enum):
    """Supported emergency management decision types."""

    DISPATCH_RESOURCE = "DISPATCH_RESOURCE"
    ASSIGN_HOSPITAL = "ASSIGN_HOSPITAL"
    EVACUATE_AREA = "EVACUATE_AREA"
    OPEN_SHELTER = "OPEN_SHELTER"
    REROUTE_RESOURCE = "REROUTE_RESOURCE"
    ALLOCATE_SUPPLIES = "ALLOCATE_SUPPLIES"
    REQUEST_REINFORCEMENT = "REQUEST_REINFORCEMENT"
    PRIORITIZE_INCIDENT = "PRIORITIZE_INCIDENT"


class DecisionStatus(str, Enum):
    """Decision lifecycle state machine."""

    GENERATED = "GENERATED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MODIFIED = "MODIFIED"
    EXECUTING = "EXECUTING"
    EXECUTED = "EXECUTED"
    EXPIRED = "EXPIRED"


class DecisionPriority(str, Enum):
    """Operational priority rating for emergency response decisions."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PolicyType(str, Enum):
    """Supported AI decision generation policies."""

    BASELINE = "BASELINE"
    HEURISTIC = "HEURISTIC"
    OPTIMIZED = "OPTIMIZED"
    ML_ASSISTED = "ML_ASSISTED"
    RL_POLICY = "RL_POLICY"


class FeedbackType(str, Enum):
    """Commander feedback classification for AI decisions."""

    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    MODIFIED = "MODIFIED"
    OUTCOME_RATING = "OUTCOME_RATING"


class ExecutionMode(str, Enum):
    """Operational context mode for AI evaluation."""

    LIVE = "LIVE"
    SIMULATION = "SIMULATION"
    SCENARIO = "SCENARIO"
    WHAT_IF = "WHAT_IF"
