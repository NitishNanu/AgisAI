"""
RescueNet AI — Response Scoring Service.

Computes multi-factor response intelligence scores for ranking rescue teams:
- Vehicle Suitability (40%)
- Road Distance (25%)
- ETA (25%)
- Availability (10%)
"""


class ResponseScoringService:
    """
    Service for calculating multi-factor response compatibility scores.
    """

    # Compatibility rules mapping disaster types to vehicle scores (0-100)
    VEHICLE_COMPATIBILITY = {
        "FIRE": {
            "FIRE_TRUCK": 100,
            "RESCUE_VAN": 60,
            "AMBULANCE": 30,
            "HELICOPTER": 50,
            "HAZMAT_UNIT": 60,
            "COMMAND_VEHICLE": 50,
        },
        "BUILDING_COLLAPSE": {
            "RESCUE_VAN": 100,
            "CRANE_TRUCK": 100,
            "FIRE_TRUCK": 80,
            "AMBULANCE": 50,
            "HELICOPTER": 60,
            "COMMAND_VEHICLE": 60,
        },
        "ACCIDENT": {
            "AMBULANCE": 100,
            "RESCUE_VAN": 80,
            "FIRE_TRUCK": 50,
            "HELICOPTER": 70,
            "COMMAND_VEHICLE": 50,
        },
        "GAS_LEAK": {
            "HAZMAT_UNIT": 100,
            "FIRE_TRUCK": 100,
            "RESCUE_VAN": 70,
            "AMBULANCE": 40,
            "COMMAND_VEHICLE": 60,
        },
        "FLOOD": {
            "BOAT": 100,
            "RESCUE_VAN": 100,
            "HELICOPTER": 90,
            "FIRE_TRUCK": 70,
            "AMBULANCE": 60,
            "COMMAND_VEHICLE": 60,
        },
        "EARTHQUAKE": {
            "RESCUE_VAN": 100,
            "AMBULANCE": 90,
            "FIRE_TRUCK": 80,
            "HELICOPTER": 80,
            "CRANE_TRUCK": 80,
            "COMMAND_VEHICLE": 70,
        },
        "WILDFIRE": {
            "FIRE_TRUCK": 100,
            "HELICOPTER": 90,
            "RESCUE_VAN": 60,
            "AMBULANCE": 40,
            "COMMAND_VEHICLE": 60,
        },
        "TSUNAMI": {
            "BOAT": 100,
            "HELICOPTER": 100,
            "RESCUE_VAN": 80,
            "AMBULANCE": 60,
            "COMMAND_VEHICLE": 70,
        },
        "HAZMAT": {
            "HAZMAT_UNIT": 100,
            "FIRE_TRUCK": 80,
            "RESCUE_VAN": 60,
            "AMBULANCE": 50,
            "COMMAND_VEHICLE": 60,
        },
    }

    # Weights
    WEIGHT_VEHICLE = 0.40
    WEIGHT_DISTANCE = 0.25
    WEIGHT_ETA = 0.25
    WEIGHT_AVAILABILITY = 0.10

    @classmethod
    def get_vehicle_suitability_score(cls, disaster_type: str, vehicle_type: str) -> float:
        """Return suitability score (0-100) for a given vehicle type and disaster."""
        dtype = disaster_type.upper() if disaster_type else "FIRE"
        vtype = vehicle_type.upper() if vehicle_type else ""

        mapping = cls.VEHICLE_COMPATIBILITY.get(dtype, {})
        return float(mapping.get(vtype, 50.0))

    @classmethod
    def get_distance_score(cls, distance_km: float, max_km: float = 50.0) -> float:
        """Calculate distance score (0-100) where closer is higher."""
        if distance_km <= 0:
            return 100.0
        normalized = max(0.0, 100.0 - (distance_km / max_km) * 100.0)
        return min(100.0, normalized)

    @classmethod
    def get_eta_score(cls, eta_minutes: float, max_minutes: float = 60.0) -> float:
        """Calculate ETA score (0-100) where lower ETA is higher."""
        if eta_minutes <= 0:
            return 100.0
        normalized = max(0.0, 100.0 - (eta_minutes / max_minutes) * 100.0)
        return min(100.0, normalized)

    @classmethod
    def get_availability_score(cls, status: str) -> float:
        """Calculate availability score (0-100)."""
        st = status.upper() if status else "AVAILABLE"
        if st == "AVAILABLE":
            return 100.0
        elif st == "STANDBY":
            return 50.0
        return 0.0

    @classmethod
    def calculate_score(
        cls,
        disaster_type: str,
        vehicle_type: str,
        distance_km: float,
        eta_minutes: float,
        status: str = "AVAILABLE",
    ) -> float:
        """
        Calculate total composite response intelligence score (0-100).
        """
        suitability = cls.get_vehicle_suitability_score(disaster_type, vehicle_type)
        dist_score = cls.get_distance_score(distance_km)
        eta_sc = cls.get_eta_score(eta_minutes)
        avail_score = cls.get_availability_score(status)

        total_score = (
            (suitability * cls.WEIGHT_VEHICLE)
            + (dist_score * cls.WEIGHT_DISTANCE)
            + (eta_sc * cls.WEIGHT_ETA)
            + (avail_score * cls.WEIGHT_AVAILABILITY)
        )

        return round(total_score, 2)
