from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

# --- Evidence Submission Schemas ---
class EvidenceSubmissionCreate(BaseModel):
    project_id: str
    submitted_by: Optional[str] = "Citizen Monitor"
    observation_type: str = Field(
        ...,
        description="not_started | delayed | incomplete | poor_quality | appears_completed | cannot_be_found | other"
    )
    photo_url: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    timestamp: Optional[str] = None
    description: str
    provenance: Optional[str] = "community"
    is_seeded_demo_data: Optional[bool] = False

class EvidenceSubmissionResponse(BaseModel):
    id: int
    project_id: str
    submitted_by: str
    observation_type: str
    photo_url: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    timestamp: Optional[str] = None
    description: str
    provenance: str
    is_seeded_demo_data: bool
    created_at: Optional[str] = None

    class Config:
        from_attributes = True

# --- AI Reconciliation Schemas ---
class ReconciliationRequest(BaseModel):
    project_id: str
    evidence_ids: Optional[List[int]] = None # If None, reconciles all evidence for project

class ReconciliationStructuredOutput(BaseModel):
    status: str = Field(
        ...,
        description="consistent | discrepancy_flagged | needs_more_evidence"
    )
    confidence: str = Field(
        ...,
        description="low | medium | high"
    )
    supporting_points: List[str] = Field(default_factory=list)
    concerning_points: List[str] = Field(default_factory=list)
    summary: str
    recommendation: str

class ReconciliationResponse(BaseModel):
    id: int
    project_id: str
    status: str
    confidence: str
    supporting_points: List[str]
    concerning_points: List[str]
    summary: str
    recommendation: str
    evidence_considered: List[int]
    provenance: str
    human_review_status: str
    human_notes: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True

class HumanReviewUpdate(BaseModel):
    human_review_status: str = Field(..., description="verified | resolved | dismissed | pending")
    human_notes: Optional[str] = None

# --- Project Schemas ---
class ProjectResponse(BaseModel):
    id: str
    ocid: str
    title: str
    buyer: str
    contractor: str
    contract_value: float
    currency: str
    region: str
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    award_date: Optional[str] = None
    start_date: Optional[str] = None
    expected_completion_date: Optional[str] = None
    duration_days: Optional[int] = None
    official_reported_progress: Optional[int] = None
    official_status: str
    source_url: str
    last_updated: Optional[str] = None
    provenance: str
    sector: str
    evidence_count: int = 0
    latest_reconciliation: Optional[ReconciliationResponse] = None

    class Config:
        from_attributes = True

class ProjectDetailResponse(ProjectResponse):
    evidence_submissions: List[EvidenceSubmissionResponse] = []
    reconciliation_results: List[ReconciliationResponse] = []
