import os
import json
from datetime import datetime
from sqlalchemy.orm import Session
from .database import SessionLocal, engine, Base
from .models import Project

# Geographic coordinates for key Tanzanian administrative locations
REGION_COORDINATES = {
    "kigoma": {"lat": -4.8769, "lng": 29.6267, "name": "Kigoma District, Kigoma Region"},
    "iringa": {"lat": -7.7731, "lng": 35.6944, "name": "Kilolo District, Iringa Region"},
    "dodoma": {"lat": -6.1630, "lng": 35.7516, "name": "Dodoma City, Dodoma Region"},
    "dar es salaam": {"lat": -6.7924, "lng": 39.2083, "name": "Dar es Salaam City Council"},
    "mwanza": {"lat": -2.5164, "lng": 32.9000, "name": "Ukerewe District, Mwanza Region"},
    "tanga": {"lat": -5.0689, "lng": 39.0988, "name": "Korogwe, Tanga Region"},
    "arusha": {"lat": -3.3869, "lng": 36.6830, "name": "Arusha Municipality, Arusha Region"},
    "morogoro": {"lat": -6.8278, "lng": 37.6591, "name": "Malinyi District, Morogoro Region"},
    "geita": {"lat": -2.8714, "lng": 32.2289, "name": "Geita Municipal Council, Geita Region"},
    "tabora": {"lat": -5.0167, "lng": 32.8000, "name": "Urambo District, Tabora Region"},
}

SECTOR_KEYWORDS = {
    "water": ["water", "dam", "irrigation", "treatment", "sanitation", "borehole", "maji"],
    "health": ["hospital", "health", "dispensary", "cedha", "medical", "clinic", "afya"],
    "education": ["school", "primary", "secondary", "dormitory", "pupils", "shule", "mwalimu"],
    "transport": ["road", "culvert", "drift", "tarura", "bridge", "tanroads", "highway", "barabara"],
    "administration": ["building", "office", "headquarters", "rest house", "jengo", "utawala"]
}

def detect_sector(title: str, buyer: str) -> str:
    combined = (title + " " + buyer).lower()
    for sector, keywords in SECTOR_KEYWORDS.items():
        if any(k in combined for k in keywords):
            return sector
    return "infrastructure"

def detect_region_and_coords(title: str, buyer: str):
    combined = (title + " " + buyer).lower()
    for key, geo in REGION_COORDINATES.items():
        if key in combined:
            return key.title(), geo["name"], geo["lat"], geo["lng"]
    return "Tanzania", "Tanzania Mainland", -6.3690, 34.8888

def seed_verified_projects(db: Session = None):
    """Ingests verified real OCDS projects from data/verified_sample_projects.json into SQLite database."""
    Base.metadata.create_all(bind=engine)
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        sample_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data",
            "verified_sample_projects.json"
        )
        if not os.path.exists(sample_path):
            print(f"[Ingest] File not found: {sample_path}")
            return 0

        with open(sample_path, "r") as f:
            records = json.load(f)

        count = 0
        for rec in records:
            ocid = rec["ocid"]
            existing = db.query(Project).filter(Project.ocid == ocid).first()
            if existing:
                continue

            title = rec.get("title", "Public Procurement Project")
            buyer = rec.get("buyer", "Government of Tanzania")
            contractor = rec.get("contractor", "Registered Contractor")
            val_data = rec.get("contract_value", {})
            amount = float(val_data.get("amount", 0.0))
            currency = val_data.get("currency", "TZS")
            period = rec.get("contract_period", {})

            region, loc_name, lat, lng = detect_region_and_coords(title, buyer)
            sector = detect_sector(title, buyer)

            project = Project(
                id=ocid,
                ocid=ocid,
                title=title,
                buyer=buyer,
                contractor=contractor,
                contract_value=amount,
                currency=currency,
                region=region,
                location_name=loc_name,
                latitude=lat,
                longitude=lng,
                award_date=rec.get("award_date"),
                start_date=period.get("startDate"),
                expected_completion_date=period.get("endDate"),
                duration_days=period.get("durationInDays"),
                official_reported_progress=None, # Not reported in raw feed
                official_status=rec.get("contract_status", "active"),
                source_url=rec.get("source_url", f"https://data.nest.go.tz/ocds/{ocid}"),
                last_updated=rec.get("last_updated"),
                provenance="official",
                sector=sector
            )
            db.add(project)
            count += 1

        db.commit()
        print(f"[Ingest] Ingested {count} real OCDS projects successfully.")
        return count
    finally:
        if should_close:
            db.close()

if __name__ == "__main__":
    seed_verified_projects()
