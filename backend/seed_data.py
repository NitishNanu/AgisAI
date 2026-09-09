"""
RescueNet AI — Master Seed Script.

Seeds the Chandigarh, Mohali, Panchkula demo geography with:
- 6 Disasters
- 6 Rescue Teams
- 5 Hospitals
- 6 Shelters
- Platform Users (Admin, Commander, Dispatcher, Citizen)
- Alerts & Initial Assignments
"""

import sys
import traceback
from datetime import datetime, timezone

sys.path.insert(0, "d:/PROJECTS/GoogleMapsDisaster/backend")

from app.core.database.session import SessionLocal
from app.core.security.jwt import hash_password
from app.modules.auth.models import User
from app.modules.hospital.models import Hospital
from app.modules.incident.enums import DisasterType, IncidentStatus, SeverityLevel
from app.modules.incident.models import Incident
from app.modules.notification.models import Alert
from app.modules.resource.enums import AssignmentStatus, TeamStatus, VehicleType
from app.modules.resource.models import RescueTeam, ResourceAssignment, Shelter

try:
    from geoalchemy2.elements import WKTElement
except ImportError:
    WKTElement = None


def make_geom(lat: float, lon: float):
    if WKTElement:
        return WKTElement(f"POINT({lon} {lat})", srid=4326)
    return None


def seed_data():
    db = SessionLocal()
    try:
        print("Cleaning existing demo data...")
        db.query(ResourceAssignment).delete()
        db.query(Alert).delete()
        db.query(Incident).delete()
        db.query(RescueTeam).delete()
        db.query(Hospital).delete()
        db.query(Shelter).delete()
        db.query(User).delete()
        db.commit()

        # 1. Platform Users
        print("Seeding users...")
        admin = User(
            name="System Admin",
            email="admin@example.com",
            password_hash=hash_password("Admin123"),
            role="ADMIN",
            is_active=True,
        )
        commander = User(
            name="Command Chief",
            email="commander@example.com",
            password_hash=hash_password("Commander123"),
            role="COMMANDER",
            is_active=True,
        )
        dispatcher = User(
            name="Central Dispatcher",
            email="dispatcher@example.com",
            password_hash=hash_password("Dispatcher123"),
            role="DISPATCHER",
            is_active=True,
        )
        citizen = User(
            name="Nitish Citizen",
            email="citizen@example.com",
            password_hash=hash_password("Citizen123"),
            role="CITIZEN",
            is_active=True,
        )
        db.add_all([admin, commander, dispatcher, citizen])
        db.commit()

        # 2. Alerts (Early Warning Systems)
        print("Seeding early warning alerts...")
        alert1 = Alert(
            title="Industrial Zone Hazard Warning",
            message="High concentration of volatile gas reported in Industrial Area Phase 1.",
            severity="CRITICAL",
            target_role="COMMANDER",
        )
        alert2 = Alert(
            title="Monsoon Water Level Warning",
            message="Sukhna Lake drainage channel overflowing near Sector 17.",
            severity="WARNING",
            target_role="DISPATCHER",
        )
        db.add_all([alert1, alert2])

        # 3. Disasters (Chandigarh / Mohali / Panchkula)
        print("Seeding 6 disasters...")
        disasters = [
            Incident(
                title="Industrial Fire",
                description="Large fire outbreak in a commercial packaging warehouse.",
                disaster_type=DisasterType.FIRE.value,
                severity=SeverityLevel.CRITICAL.value,
                status=IncidentStatus.ACTIVE.value,
                latitude=30.7046,
                longitude=76.7985,
                location=make_geom(30.7046, 76.7985),
                affected_radius_meters=400.0,
                estimated_affected_people=80,
                reported_by=commander.id,
            ),
            Incident(
                title="Building Collapse",
                description="Structural collapse of an old 3-storey building during excavation.",
                disaster_type=DisasterType.BUILDING_COLLAPSE.value,
                severity=SeverityLevel.CRITICAL.value,
                status=IncidentStatus.ACTIVE.value,
                latitude=30.7333,
                longitude=76.7794,
                location=make_geom(30.7333, 76.7794),
                affected_radius_meters=250.0,
                estimated_affected_people=45,
                reported_by=dispatcher.id,
            ),
            Incident(
                title="Major Flood Near Sector 17",
                description="Heavy downpour causing severe waterlogging and trapped commuters.",
                disaster_type=DisasterType.FLOOD.value,
                severity=SeverityLevel.HIGH.value,
                status=IncidentStatus.ACTIVE.value,
                latitude=30.7415,
                longitude=76.7685,
                location=make_geom(30.7415, 76.7685),
                affected_radius_meters=600.0,
                estimated_affected_people=200,
                reported_by=citizen.id,
            ),
            Incident(
                title="Road Accident NH-5",
                description="Multi-vehicle collision on highway near Zirakpur intersection.",
                disaster_type=DisasterType.ACCIDENT.value,
                severity=SeverityLevel.HIGH.value,
                status=IncidentStatus.ACTIVE.value,
                latitude=30.6425,
                longitude=76.8173,
                location=make_geom(30.6425, 76.8173),
                affected_radius_meters=100.0,
                estimated_affected_people=15,
                reported_by=citizen.id,
            ),
            Incident(
                title="Gas Leak Industrial Area",
                description="Chemical vapor release detected from refrigeration unit.",
                disaster_type=DisasterType.GAS_LEAK.value,
                severity=SeverityLevel.CRITICAL.value,
                status=IncidentStatus.ACTIVE.value,
                latitude=30.6975,
                longitude=76.8042,
                location=make_geom(30.6975, 76.8042),
                affected_radius_meters=500.0,
                estimated_affected_people=120,
                reported_by=commander.id,
            ),
            Incident(
                title="Flash Flood Mohali",
                description="Low-lying residential sectors flooded after cloudburst.",
                disaster_type=DisasterType.FLOOD.value,
                severity=SeverityLevel.HIGH.value,
                status=IncidentStatus.ACTIVE.value,
                latitude=30.7046,
                longitude=76.7179,
                location=make_geom(30.7046, 76.7179),
                affected_radius_meters=800.0,
                estimated_affected_people=350,
                reported_by=dispatcher.id,
            ),
        ]
        db.add_all(disasters)
        db.commit()

        # 4. Rescue Teams (6 Units)
        print("Seeding 6 rescue teams...")
        teams = [
            RescueTeam(
                team_name="Chandigarh Rescue Team 1",
                vehicle_type=VehicleType.RESCUE_VAN.value,
                members=6,
                status=TeamStatus.AVAILABLE.value,
                latitude=30.7350,
                longitude=76.7820,
                location=make_geom(30.7350, 76.7820),
            ),
            RescueTeam(
                team_name="Chandigarh Fire & Rescue 2",
                vehicle_type=VehicleType.FIRE_TRUCK.value,
                members=8,
                status=TeamStatus.AVAILABLE.value,
                latitude=30.7100,
                longitude=76.7900,
                location=make_geom(30.7100, 76.7900),
            ),
            RescueTeam(
                team_name="Sector 17 Emergency Unit",
                vehicle_type=VehicleType.AMBULANCE.value,
                members=4,
                status=TeamStatus.AVAILABLE.value,
                latitude=30.7400,
                longitude=76.7700,
                location=make_geom(30.7400, 76.7700),
            ),
            RescueTeam(
                team_name="Mohali Disaster Response Team",
                vehicle_type=VehicleType.RESCUE_VAN.value,
                members=7,
                status=TeamStatus.AVAILABLE.value,
                latitude=30.7050,
                longitude=76.7200,
                location=make_geom(30.7050, 76.7200),
            ),
            RescueTeam(
                team_name="Panchkula Emergency Team",
                vehicle_type=VehicleType.FIRE_TRUCK.value,
                members=6,
                status=TeamStatus.AVAILABLE.value,
                latitude=30.6900,
                longitude=76.8600,
                location=make_geom(30.6900, 76.8600),
            ),
            RescueTeam(
                team_name="Rapid Response Unit 6",
                vehicle_type=VehicleType.HAZMAT_UNIT.value,
                members=5,
                status=TeamStatus.AVAILABLE.value,
                latitude=30.7200,
                longitude=76.7600,
                location=make_geom(30.7200, 76.7600),
            ),
        ]
        db.add_all(teams)
        db.commit()

        # 5. Hospitals (5 Facilities)
        print("Seeding 5 hospitals...")
        hospitals = [
            Hospital(
                name="PGIMER Chandigarh",
                address="Sector 12, Chandigarh",
                emergency_contact="+91-172-2747585",
                beds=1500,
                icu_beds=250,
                oxygen_available=True,
                blood_bank_available=True,
                is_operational=True,
                latitude=30.7650,
                longitude=76.7750,
                location=make_geom(30.7650, 76.7750),
            ),
            Hospital(
                name="Government Multi Specialty Hospital (GMSH-16)",
                address="Sector 16, Chandigarh",
                emergency_contact="+91-172-2768201",
                beds=500,
                icu_beds=80,
                oxygen_available=True,
                blood_bank_available=True,
                is_operational=True,
                latitude=30.7450,
                longitude=76.7800,
                location=make_geom(30.7450, 76.7800),
            ),
            Hospital(
                name="GMCH Sector 32",
                address="Sector 32, Chandigarh",
                emergency_contact="+91-172-2665253",
                beds=800,
                icu_beds=120,
                oxygen_available=True,
                blood_bank_available=True,
                is_operational=True,
                latitude=30.7080,
                longitude=76.7740,
                location=make_geom(30.7080, 76.7740),
            ),
            Hospital(
                name="Fortis Hospital Mohali",
                address="Sector 62, Phase VIII, Mohali",
                emergency_contact="+91-172-5010777",
                beds=350,
                icu_beds=60,
                oxygen_available=True,
                blood_bank_available=True,
                is_operational=True,
                latitude=30.7010,
                longitude=76.7330,
                location=make_geom(30.7010, 76.7330),
            ),
            Hospital(
                name="Civil Hospital Panchkula",
                address="Sector 6, Panchkula",
                emergency_contact="+91-172-2560300",
                beds=300,
                icu_beds=40,
                oxygen_available=True,
                blood_bank_available=True,
                is_operational=True,
                latitude=30.6930,
                longitude=76.8520,
                location=make_geom(30.6930, 76.8520),
            ),
        ]
        db.add_all(hospitals)
        db.commit()

        # 6. Shelters (6 Safe Zones)
        print("Seeding 6 shelters...")
        shelters = [
            Shelter(
                name="Community Centre Sector 17",
                address="Sector 17, Chandigarh",
                capacity=500,
                current_occupancy=45,
                latitude=30.7390,
                longitude=76.7780,
                location=make_geom(30.7390, 76.7780),
            ),
            Shelter(
                name="Sports Complex Sector 42",
                address="Sector 42, Chandigarh",
                capacity=1200,
                current_occupancy=150,
                latitude=30.7250,
                longitude=76.7450,
                location=make_geom(30.7250, 76.7450),
            ),
            Shelter(
                name="Mohali Indoor Stadium Shelter",
                address="Phase 9, Mohali",
                capacity=800,
                current_occupancy=90,
                latitude=30.6920,
                longitude=76.7260,
                location=make_geom(30.6920, 76.7260),
            ),
            Shelter(
                name="Panchkula Sector 5 Ground Shelter",
                address="Sector 5, Panchkula",
                capacity=1000,
                current_occupancy=110,
                latitude=30.6950,
                longitude=76.8550,
                location=make_geom(30.6950, 76.8550),
            ),
            Shelter(
                name="Community Hall Sector 22",
                address="Sector 22-B, Chandigarh",
                capacity=400,
                current_occupancy=30,
                latitude=30.7310,
                longitude=76.7650,
                location=make_geom(30.7310, 76.7650),
            ),
            Shelter(
                name="Zirakpur Relief Transit Shelter",
                address="Patiala Highway, Zirakpur",
                capacity=600,
                current_occupancy=70,
                latitude=30.6350,
                longitude=76.8200,
                location=make_geom(30.6350, 76.8200),
            ),
        ]
        db.add_all(shelters)
        db.commit()

        print("Master seed data inserted successfully!")
        print(f"Summary: {len(disasters)} disasters, {len(teams)} teams, {len(hospitals)} hospitals, {len(shelters)} shelters.")
    except Exception as e:
        db.rollback()
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
