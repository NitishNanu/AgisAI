from app.modules.ai.models import (
    AIDecision,
    AIDecisionCandidate,
    AIDecisionEvent,
    AIDecisionFeedback,
)
from app.modules.auth.models import User
from app.modules.hospital.models import Hospital
from app.modules.incident.models import Incident
from app.modules.incident.models import Incident as Disaster
from app.modules.prediction.models import PredictionRecord
from app.modules.resource.models import (
    RescueTeam,
    ResourceAssignment,
    Shelter,
)
from app.modules.resource.models import (
    ResourceAssignment as Assignment,
)

__all__ = [
    "User",
    "Hospital",
    "Incident",
    "Disaster",
    "RescueTeam",
    "ResourceAssignment",
    "Assignment",
    "Shelter",
    "AIDecision",
    "AIDecisionCandidate",
    "AIDecisionFeedback",
    "AIDecisionEvent",
    "PredictionRecord",
]
