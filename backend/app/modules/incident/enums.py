"""
AegisAI Incident Module â€” Domain Enums.

Python Enum classes that mirror the database check constraints.
Using Enum types ensures type-safety in service and repository code,
and provides a single source of truth for valid values.
"""

from enum import Enum


class DisasterType(str, Enum):
    """Supported disaster/emergency event classifications."""

    FIRE = "FIRE"
    FLOOD = "FLOOD"
    EARTHQUAKE = "EARTHQUAKE"
    BUILDING_COLLAPSE = "BUILDING_COLLAPSE"
    GAS_LEAK = "GAS_LEAK"
    ACCIDENT = "ACCIDENT"
    TSUNAMI = "TSUNAMI"
    HURRICANE = "HURRICANE"
    PANDEMIC = "PANDEMIC"
    HAZMAT = "HAZMAT"
    WILDFIRE = "WILDFIRE"
    LANDSLIDE = "LANDSLIDE"


class SeverityLevel(str, Enum):
    """Incident severity classification."""

    LOW = "LOW"          # Minor incident, minimal resources needed
    MEDIUM = "MEDIUM"    # Moderate impact, standard response
    HIGH = "HIGH"        # Significant impact, elevated response
    CRITICAL = "CRITICAL"  # Catastrophic â€” maximum resource mobilization


class IncidentStatus(str, Enum):
    """Operational status of an incident."""

    ACTIVE = "ACTIVE"          # Ongoing, needs response
    RESPONDING = "RESPONDING"  # Mission dispatched / teams en route
    MONITORING = "MONITORING"  # Under observation, reduced risk
    CONTAINED = "CONTAINED"    # Controlled but not resolved
    RESOLVED = "RESOLVED"      # Fully resolved and closed
    CANCELLED = "CANCELLED"    # False alarm or duplicate entry

