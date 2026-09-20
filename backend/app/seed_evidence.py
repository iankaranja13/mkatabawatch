import os
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .database import SessionLocal, Base, engine
from .models import Project, EvidenceSubmission, ReconciliationResult
from .ai_reconciler import run_heuristic_reconciliation, reconcile_with_llm

SEEDED_EVIDENCE = [
    # 1. Dar es Salaam Box Culverts (CROSSWORLD CONSTRUCTION - 1.52B TZS) -> DISCREPANCY
    {
        "project_id": "ocds-mv5oob-88Z1-2023-2024-W-82-S001",
        "submitted_by": "Juma Bakari (Local Resident)",
        "observation_type": "incomplete",
        "photo_url": "/static/images/demo_culvert_stalled.jpg",
        "gps_lat": -6.8124,
        "gps_lng": 39.1852,
        "timestamp": "2026-08-28T09:15:00Z",
        "description": "Only earthworks and concrete footings were poured at the Msumi-Bombambili site. Excavator left the site 3 weeks ago. Rainwater has flooded the trench creating a mosquito breeding hazard for nearby houses. No work observed at Kavesu-Liwiti.",
        "is_seeded_demo_data": True
    },
    {
        "project_id": "ocds-mv5oob-88Z1-2023-2024-W-82-S001",
        "submitted_by": "Amina Said (Ward Youth Monitor)",
        "observation_type": "delayed",
        "photo_url": "/static/images/demo_culvert_pipes.jpg",
        "gps_lat": -6.8290,
        "gps_lng": 39.1710,
        "timestamp": "2026-09-05T14:30:00Z",
        "description": "At Kisukuru drift, culvert concrete pipes were dumped by the roadside months ago and are now overgrown with tall weeds. Pedestrians and bodabodas are forced to navigate muddy detours during evening rain.",
        "is_seeded_demo_data": True
    },

    # 2. Ukerewe Referral Hospital Supervision (MALK CONSULTANTS - 960M TZS) -> CONSISTENT
    {
        "project_id": "ocds-mv5oob-81-2023-2024-C-01-S002",
        "submitted_by": "Emanuel Mwita (Ukerewe CSO)",
        "observation_type": "appears_completed",
        "photo_url": "/static/images/demo_hospital_survey.jpg",
        "gps_lat": -2.1645,
        "gps_lng": 33.0089,
        "timestamp": "2026-07-14T11:00:00Z",
        "description": "Consultant team and land surveyors observed carrying out geotechnical soil sampling and site pegging on the designated hospital plot in Nansio. Boundary markers installed.",
        "is_seeded_demo_data": True
    },
    {
        "project_id": "ocds-mv5oob-81-2023-2024-C-01-S002",
        "submitted_by": "Grace Charles (Health Committee)",
        "observation_type": "appears_completed",
        "photo_url": None,
        "gps_lat": -2.1620,
        "gps_lng": 33.0120,
        "timestamp": "2026-08-20T16:00:00Z",
        "description": "Attended the public EIA (Environmental Impact Assessment) stakeholder forum at the District Council Hall where Malk Consultants presented preliminary architectural layouts to community leaders.",
        "is_seeded_demo_data": True
    },

    # 3. Korogwe Water Treatment Plant (TUMAINI CIVIL WORKS - 888M TZS) -> DISCREPANCY
    {
        "project_id": "ocds-mv5oob-TR163-2023-2024-W-03-S003",
        "submitted_by": "Baraka Mndeme (Maji Safi Monitor)",
        "observation_type": "delayed",
        "photo_url": "/static/images/demo_water_treatment_deserted.jpg",
        "gps_lat": -5.1580,
        "gps_lng": 38.4820,
        "timestamp": "2026-08-18T10:20:00Z",
        "description": "Ground excavation for the primary water clarification tanks started in late July, but construction has completely stopped since mid-August. No contractor personnel or security on site.",
        "is_seeded_demo_data": True
    },
    {
        "project_id": "ocds-mv5oob-TR163-2023-2024-W-03-S003",
        "submitted_by": "Hassan Mhando (Community Elder)",
        "observation_type": "poor_quality",
        "photo_url": "/static/images/demo_rebar_rust.jpg",
        "gps_lat": -5.1595,
        "gps_lng": 38.4840,
        "timestamp": "2026-09-02T15:45:00Z",
        "description": "Steel rebar tied for foundation retaining walls has been left standing uncovered in the open sun and rain, showing significant rust corrosion without anti-rust sealant or concrete cover.",
        "is_seeded_demo_data": True
    },

    # 4. TARURA National HQ Supervision (NHC - 560M TZS) -> CONSISTENT
    {
        "project_id": "ocds-mv5oob-S10-2023-2024-C-14-S001",
        "submitted_by": "Peter S. (Dodoma Civic Watch)",
        "observation_type": "appears_completed",
        "photo_url": "/static/images/demo_tarura_hq_crane.jpg",
        "gps_lat": -6.1750,
        "gps_lng": 35.7890,
        "timestamp": "2026-07-22T08:30:00Z",
        "description": "Njedengwa Plot 11-13 fully enclosed with branded metal perimeter hoarding. Heavy tower crane erected, foundation piling rigs operational under active National Housing Corporation supervision.",
        "is_seeded_demo_data": True
    },
    {
        "project_id": "ocds-mv5oob-S10-2023-2024-C-14-S001",
        "submitted_by": "Neema Kavishe (Architectural Student)",
        "observation_type": "appears_completed",
        "photo_url": None,
        "gps_lat": -6.1745,
        "gps_lng": 35.7905,
        "timestamp": "2026-08-30T13:10:00Z",
        "description": "Basement slab casting completed with commercial concrete mixer trucks active on site. Safety officer present and personal protective equipment strictly enforced.",
        "is_seeded_demo_data": True
    },

    # 5. CEDHA Health Training Remodeling (DIGITAL SPACE CONSULTANCY - 261M TZS) -> DISCREPANCY
    {
        "project_id": "ocds-mv5oob-52-2023-2024-C-21-S001",
        "submitted_by": "Tatu Rashid (Sanawari Resident)",
        "observation_type": "not_started",
        "photo_url": "/static/images/demo_cedha_arusha.jpg",
        "gps_lat": -3.3620,
        "gps_lng": 36.7010,
        "timestamp": "2026-09-01T11:45:00Z",
        "description": "Inspected CEDHA Sanawari training centre campus. The classrooms, training labs, and hostel block designated for remodeling remain untouched with zero renovation works underway despite contract period starting in June.",
        "is_seeded_demo_data": True
    },
    {
        "project_id": "ocds-mv5oob-52-2023-2024-C-21-S001",
        "submitted_by": "Dr. E. Shirima (Healthcare Tutor)",
        "observation_type": "delayed",
        "photo_url": None,
        "gps_lat": -3.3615,
        "gps_lng": 36.7025,
        "timestamp": "2026-09-10T16:20:00Z",
        "description": "Staff at the campus confirm consultant visited in June to collect floorplans, but no contractor mobilized to site for civil remodeling. Over 3 months of the 12-month contract period have elapsed.",
        "is_seeded_demo_data": True
    },

    # 6. Namanga Border Rest House (SWASH CONSTRUCTION - 174M TZS) -> CONSISTENT
    {
        "project_id": "ocds-mv5oob-X2-2023-2024-W-09-S001",
        "submitted_by": "Lucas Mollel (Cross-Border Trader)",
        "observation_type": "appears_completed",
        "photo_url": "/static/images/demo_namanga_resthouse.jpg",
        "gps_lat": -2.5480,
        "gps_lng": 36.7910,
        "timestamp": "2026-08-15T14:15:00Z",
        "description": "Rest house block walling complete up to roof ring beam level at Namanga border post. Construction team is assembling pre-treated timber roof trusses on site.",
        "is_seeded_demo_data": True
    },
    {
        "project_id": "ocds-mv5oob-X2-2023-2024-W-09-S001",
        "submitted_by": "Lucas Mollel (Cross-Border Trader)",
        "observation_type": "appears_completed",
        "photo_url": None,
        "gps_lat": -2.5485,
        "gps_lng": 36.7905,
        "timestamp": "2026-09-08T09:30:00Z",
        "description": "Roof sheeting installation underway with galvanized metal corrugated sheets. Window burglar-proofing grilles fitted.",
        "is_seeded_demo_data": True
    },

    # 7. Mtimbira Primary School Dormitory (ZIDADU GENERAL SUPPLIES - 82M TZS) -> DISCREPANCY
    {
        "project_id": "ocds-mv5oob-79K7-2023-2024-G-566-S001",
        "submitted_by": "Mwalimu Hamisi (Mtimbira Parent Association)",
        "observation_type": "incomplete",
        "photo_url": "/static/images/demo_mtimbira_dorm.jpg",
        "gps_lat": -8.7840,
        "gps_lng": 36.3500,
        "timestamp": "2026-08-25T15:00:00Z",
        "description": "Contract specified full delivery of building materials within 30 days (ended June 2024). To date, only 140 bags of cement and gravel were delivered. Timber, roofing iron sheets, and electrical fittings are still missing.",
        "is_seeded_demo_data": True
    },
    {
        "project_id": "ocds-mv5oob-79K7-2023-2024-G-566-S001",
        "submitted_by": "Salum Nchimbi (Village Secretary)",
        "observation_type": "delayed",
        "photo_url": None,
        "gps_lat": -8.7835,
        "gps_lng": 36.3510,
        "timestamp": "2026-09-04T10:00:00Z",
        "description": "Dormitory structure remains unroofed at wall plate level because timber has not arrived. 80 primary school pupils continue boarding in overcrowded temporary village quarters.",
        "is_seeded_demo_data": True
    },

    # 8. Luiche Dam Mega-Project (CRJE EAST AFRICA - 20.7B TZS) -> NEEDS MORE EVIDENCE
    {
        "project_id": "ocds-mv5oob-00005-2023-2024-W-78-S001",
        "submitted_by": "Kigoma Community Observer",
        "observation_type": "other",
        "photo_url": None,
        "gps_lat": -4.8500,
        "gps_lng": 29.6800,
        "timestamp": "2026-08-10T12:00:00Z",
        "description": "Access road to the Luiche River basin has been cleared by heavy bulldozers. Main dam embankment construction site is restricted by security checkpoints and could not be independently inspected without official permit.",
        "is_seeded_demo_data": True
    }
]

async def seed_evidence_and_run_reconciliations():
    """Populates seeded evidence and automatically executes AI reconciliations."""
    db: Session = SessionLocal()
    try:
        print("[Seed] Checking and seeding demonstration evidence submissions...")
        added_count = 0
        project_ids_to_reconcile = set()

        for item in SEEDED_EVIDENCE:
            # Check if this exact description already exists
            existing = db.query(EvidenceSubmission).filter(
                EvidenceSubmission.project_id == item["project_id"],
                EvidenceSubmission.description == item["description"]
            ).first()

            if not existing:
                ev = EvidenceSubmission(
                    project_id=item["project_id"],
                    submitted_by=item["submitted_by"],
                    observation_type=item["observation_type"],
                    photo_url=item.get("photo_url"),
                    gps_lat=item["gps_lat"],
                    gps_lng=item["gps_lng"],
                    timestamp=item["timestamp"],
                    description=item["description"],
                    provenance="community",
                    is_seeded_demo_data=True
                )
                db.add(ev)
                project_ids_to_reconcile.add(item["project_id"])
                added_count += 1

        db.commit()
        print(f"[Seed] Successfully added {added_count} seeded evidence submissions.")

        # Reconcile projects that have new evidence
        for pid in project_ids_to_reconcile:
            project = db.query(Project).filter(Project.id == pid).first()
            if not project:
                continue

            evidence_items = project.evidence_submissions
            print(f"[Reconcile] Running AI reconciliation for project {pid} ({len(evidence_items)} evidence items)...")
            ai_output = await reconcile_with_llm(project, evidence_items)

            recon = ReconciliationResult(
                project_id=project.id,
                status=ai_output["status"],
                confidence=ai_output["confidence"],
                supporting_points=ai_output.get("supporting_points", []),
                concerning_points=ai_output.get("concerning_points", []),
                summary=ai_output["summary"],
                recommendation=ai_output["recommendation"],
                evidence_considered=[e.id for e in evidence_items],
                provenance="ai_generated",
                human_review_status="pending"
            )
            db.add(recon)

        db.commit()
        print(f"[Reconcile] Completed reconciliations for {len(project_ids_to_reconcile)} projects.")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(seed_evidence_and_run_reconciliations())
