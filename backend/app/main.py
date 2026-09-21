import os
import shutil
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .database import engine, get_db, Base
from .models import Project, EvidenceSubmission, ReconciliationResult
from .schemas import (
    ProjectResponse,
    ProjectDetailResponse,
    EvidenceSubmissionCreate,
    EvidenceSubmissionResponse,
    ReconciliationRequest,
    ReconciliationResponse,
    HumanReviewUpdate,
)
from .ai_reconciler import reconcile_with_llm
from .ingest import seed_verified_projects

# Initialize tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MkatabaWatch API 🇹🇿",
    description="Public Contracts, Public Evidence — Tanzania Public Procurement Monitoring & AI Reconciliation",
    version="1.0.0"
)

# CORS
origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Upload directory
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Frontend static directory
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.on_event("startup")
def startup_event():
    db = next(get_db())
    # Ensure default verified projects are loaded
    seed_verified_projects(db)


# --- Dashboard Stats ---
@app.get("/api/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_projects = db.query(Project).count()
    total_evidence = db.query(EvidenceSubmission).count()
    seeded_evidence = db.query(EvidenceSubmission).filter(EvidenceSubmission.is_seeded_demo_data == True).count()
    community_evidence = db.query(EvidenceSubmission).filter(EvidenceSubmission.is_seeded_demo_data == False).count()
    
    flagged_discrepancies = db.query(ReconciliationResult).filter(
        ReconciliationResult.status == "discrepancy_flagged"
    ).count()
    verified_consistent = db.query(ReconciliationResult).filter(
        ReconciliationResult.status == "consistent"
    ).count()

    projects = db.query(Project).all()
    total_value_tzs = sum(p.contract_value for p in projects)

    return {
        "total_projects": total_projects,
        "total_value_tzs": total_value_tzs,
        "total_evidence_submissions": total_evidence,
        "community_evidence_submissions": community_evidence,
        "seeded_evidence_submissions": seeded_evidence,
        "discrepancies_flagged": flagged_discrepancies,
        "verified_consistent": verified_consistent,
        "official_source": "Tanzania PPRA NeST Open Contracting Data Portal (data.nest.go.tz)"
    }


# --- Projects Endpoints (Screen 1 & 2) ---
@app.get("/api/projects", response_model=List[ProjectResponse])
def list_projects(
    search: Optional[str] = None,
    region: Optional[str] = None,
    sector: Optional[str] = None,
    evidence_status: Optional[str] = None, # consistent | discrepancy_flagged | no_evidence
    db: Session = Depends(get_db)
):
    query = db.query(Project)

    if search:
        s = f"%{search}%"
        query = query.filter(
            (Project.title.ilike(s)) |
            (Project.buyer.ilike(s)) |
            (Project.contractor.ilike(s)) |
            (Project.ocid.ilike(s))
        )

    if region and region.lower() != "all":
        query = query.filter(Project.region.ilike(f"%{region}%"))

    if sector and sector.lower() != "all":
        query = query.filter(Project.sector == sector.lower())

    projects = query.order_by(desc(Project.contract_value)).all()
    results = [p.to_dict() for p in projects]

    if evidence_status:
        if evidence_status == "no_evidence":
            results = [r for r in results if r["evidence_count"] == 0]
        elif evidence_status == "discrepancy_flagged":
            results = [
                r for r in results
                if r["latest_reconciliation"] and r["latest_reconciliation"]["status"] == "discrepancy_flagged"
            ]
        elif evidence_status == "consistent":
            results = [
                r for r in results
                if r["latest_reconciliation"] and r["latest_reconciliation"]["status"] == "consistent"
            ]

    return results


@app.get("/api/projects/{project_id}")
def get_project_detail(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter((Project.id == project_id) | (Project.ocid == project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    data = project.to_dict()
    data["evidence_submissions"] = [e.to_dict() for e in project.evidence_submissions]
    data["reconciliation_results"] = [r.to_dict() for r in project.reconciliation_results]
    return data


@app.get("/api/ai-status")
def get_ai_status():
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    has_anthropic = bool(anthropic_key and not anthropic_key.startswith("your_"))
    has_openai = bool(openai_key and not openai_key.startswith("your_"))

    if has_anthropic:
        return {
            "mode": "live_llm",
            "provider": "Anthropic Claude",
            "model": "claude-3-5-sonnet-20241022",
            "message": "Live AI inference enabled with Anthropic Claude 3.5 Sonnet."
        }
    elif has_openai:
        return {
            "mode": "live_llm",
            "provider": "OpenAI",
            "model": "gpt-4o-mini",
            "message": "Live AI inference enabled with OpenAI."
        }
    else:
        return {
            "mode": "heuristic_fallback",
            "provider": "MkatabaWatch Rules Engine",
            "model": "Deterministic Reconciliation Engine",
            "message": "Running offline rule engine (Add ANTHROPIC_API_KEY to .env to enable Claude 3.5 Sonnet)."
        }


@app.get("/api/projects/{project_id}/raw-ocds")
async def get_raw_ocds(project_id: str, db: Session = Depends(get_db)):
    import json
    import httpx

    project = db.query(Project).filter((Project.id == project_id) | (Project.ocid == project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Try fetching live from NeST API with a fast 3-second timeout
    nest_url = f"https://nest.go.tz/gateway/nest-data-portal-api/api/records/{project.ocid}"
    try:
        async with httpx.AsyncClient(timeout=3.0, verify=False) as client:
            resp = await client.get(nest_url, headers={"User-Agent": "MkatabaWatch/1.0", "Accept": "application/json"})
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass

    # Return local cached verified record
    return {
        "ocid": project.ocid,
        "source": "Tanzania PPRA NeST Open Contracting Data Portal",
        "api_endpoint": nest_url,
        "compiledRelease": {
            "ocid": project.ocid,
            "date": project.last_updated,
            "tag": ["compiled"],
            "initiationType": "tender",
            "buyer": {"name": project.buyer},
            "tender": {
                "id": project.ocid,
                "title": project.title,
                "status": project.official_status,
                "procuringEntity": {"name": project.buyer}
            },
            "awards": [
                {
                    "date": project.award_date,
                    "value": {"amount": project.contract_value, "currency": project.currency},
                    "suppliers": [{"name": project.contractor}]
                }
            ],
            "contracts": [
                {
                    "status": project.official_status,
                    "period": {
                        "startDate": project.start_date,
                        "endDate": project.expected_completion_date,
                        "durationInDays": project.duration_days
                    },
                    "value": {"amount": project.contract_value, "currency": project.currency}
                }
            ]
        }
    }


# --- Evidence Submission Endpoints (Screen 3) ---
@app.post("/api/evidence")
def submit_evidence_json(
    payload: EvidenceSubmissionCreate,
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter((Project.id == payload.project_id) | (Project.ocid == payload.project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    evidence = EvidenceSubmission(
        project_id=project.id,
        submitted_by=payload.submitted_by or "Citizen Monitor",
        observation_type=payload.observation_type,
        photo_url=payload.photo_url,
        gps_lat=payload.gps_lat,
        gps_lng=payload.gps_lng,
        timestamp=payload.timestamp or datetime.utcnow().isoformat() + "Z",
        description=payload.description,
        provenance=payload.provenance or "community",
        is_seeded_demo_data=payload.is_seeded_demo_data or False
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence.to_dict()


@app.post("/api/evidence/upload")
async def submit_evidence_with_photo(
    project_id: str = Form(...),
    submitted_by: Optional[str] = Form("Citizen Monitor"),
    observation_type: str = Form(...),
    description: str = Form(...),
    gps_lat: Optional[float] = Form(None),
    gps_lng: Optional[float] = Form(None),
    timestamp: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter((Project.id == project_id) | (Project.ocid == project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    photo_url = None
    if photo and photo.filename:
        filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{photo.filename.replace(' ', '_')}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        photo_url = f"/uploads/{filename}"

    evidence = EvidenceSubmission(
        project_id=project.id,
        submitted_by=submitted_by,
        observation_type=observation_type,
        photo_url=photo_url,
        gps_lat=gps_lat,
        gps_lng=gps_lng,
        timestamp=timestamp or datetime.utcnow().isoformat() + "Z",
        description=description,
        provenance="community",
        is_seeded_demo_data=False
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence.to_dict()


# --- AI Reconciliation Endpoints (Screen 4) ---
@app.post("/api/reconcile/{project_id}")
async def trigger_reconciliation(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter((Project.id == project_id) | (Project.ocid == project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    evidence_items = project.evidence_submissions
    ai_output = await reconcile_with_llm(project, evidence_items)

    result = ReconciliationResult(
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
    db.add(result)
    db.commit()
    db.refresh(result)
    return result.to_dict()


# --- Verification Queue Endpoints (Screen 5) ---
@app.get("/api/verification-queue")
def get_verification_queue(
    status: Optional[str] = "discrepancy_flagged",
    review_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(ReconciliationResult)
    if status and status.lower() != "all":
        query = query.filter(ReconciliationResult.status == status)

    if review_status and review_status.lower() != "all":
        query = query.filter(ReconciliationResult.human_review_status == review_status)

    reconciliations = query.order_by(
        desc(ReconciliationResult.confidence == "high"),
        desc(ReconciliationResult.confidence == "medium"),
        desc(ReconciliationResult.created_at)
    ).all()

    output = []
    for r in reconciliations:
        item = r.to_dict()
        item["project"] = r.project.to_dict() if r.project else None
        output.append(item)
    return output


@app.patch("/api/verification-queue/{reconciliation_id}")
def update_human_review(
    reconciliation_id: int,
    payload: HumanReviewUpdate,
    db: Session = Depends(get_db)
):
    recon = db.query(ReconciliationResult).filter(ReconciliationResult.id == reconciliation_id).first()
    if not recon:
        raise HTTPException(status_code=404, detail="Reconciliation result not found")

    recon.human_review_status = payload.human_review_status
    if payload.human_notes is not None:
        recon.human_notes = payload.human_notes

    db.commit()
    db.refresh(recon)
    return recon.to_dict()


# Serve Single Page Application frontend if index.html exists
@app.get("/")
def serve_index():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "MkatabaWatch API running. Access frontend at /static/index.html or docs at /docs"}
