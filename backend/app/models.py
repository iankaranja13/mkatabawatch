from datetime import datetime
import json
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from .database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, index=True) # Usually the OCID
    ocid = Column(String, unique=True, index=True, nullable=False)
    title = Column(Text, nullable=False)
    buyer = Column(String, index=True, nullable=False) # Procuring Entity
    contractor = Column(String, index=True, nullable=False) # Winning Vendor
    contract_value = Column(Float, nullable=False)
    currency = Column(String, default="TZS")
    region = Column(String, index=True, nullable=False)
    location_name = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    award_date = Column(String, nullable=True)
    start_date = Column(String, nullable=True)
    expected_completion_date = Column(String, nullable=True)
    duration_days = Column(Integer, nullable=True)
    official_reported_progress = Column(Integer, nullable=True) # Percentage 0-100 if reported
    official_status = Column(String, default="active") # active, complete, pending
    source_url = Column(String, nullable=False)
    last_updated = Column(String, nullable=True)
    provenance = Column(String, default="official")
    sector = Column(String, index=True, default="general") # water, health, education, transport, admin

    # Relationships
    evidence_submissions = relationship(
        "EvidenceSubmission", back_populates="project", cascade="all, delete-orphan", order_by="desc(EvidenceSubmission.created_at)"
    )
    reconciliation_results = relationship(
        "ReconciliationResult", back_populates="project", cascade="all, delete-orphan", order_by="desc(ReconciliationResult.created_at)"
    )

    def to_dict(self):
        latest_reconciliation = self.reconciliation_results[0] if self.reconciliation_results else None
        return {
            "id": self.id,
            "ocid": self.ocid,
            "title": self.title,
            "buyer": self.buyer,
            "contractor": self.contractor,
            "contract_value": self.contract_value,
            "currency": self.currency,
            "region": self.region,
            "location_name": self.location_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "award_date": self.award_date,
            "start_date": self.start_date,
            "expected_completion_date": self.expected_completion_date,
            "duration_days": self.duration_days,
            "official_reported_progress": self.official_reported_progress,
            "official_status": self.official_status,
            "source_url": self.source_url,
            "last_updated": self.last_updated,
            "provenance": self.provenance,
            "sector": self.sector,
            "evidence_count": len(self.evidence_submissions),
            "latest_reconciliation": latest_reconciliation.to_dict() if latest_reconciliation else None,
        }

class EvidenceSubmission(Base):
    __tablename__ = "evidence_submissions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(String, ForeignKey("projects.id"), index=True, nullable=False)
    submitted_by = Column(String, default="Citizen Monitor")
    observation_type = Column(String, nullable=False)
    # not_started | delayed | incomplete | poor_quality | appears_completed | cannot_be_found | other
    photo_url = Column(String, nullable=True)
    gps_lat = Column(Float, nullable=True)
    gps_lng = Column(Float, nullable=True)
    timestamp = Column(String, default=lambda: datetime.utcnow().isoformat() + "Z")
    description = Column(Text, nullable=False)
    provenance = Column(String, default="community") # community | verified
    is_seeded_demo_data = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="evidence_submissions")

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "submitted_by": self.submitted_by,
            "observation_type": self.observation_type,
            "photo_url": self.photo_url,
            "gps_lat": self.gps_lat,
            "gps_lng": self.gps_lng,
            "timestamp": self.timestamp,
            "description": self.description,
            "provenance": self.provenance,
            "is_seeded_demo_data": self.is_seeded_demo_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class ReconciliationResult(Base):
    __tablename__ = "reconciliation_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(String, ForeignKey("projects.id"), index=True, nullable=False)
    status = Column(String, nullable=False) # consistent | discrepancy_flagged | needs_more_evidence
    confidence = Column(String, nullable=False) # low | medium | high
    supporting_points_raw = Column(Text, default="[]")
    concerning_points_raw = Column(Text, default="[]")
    summary = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)
    evidence_considered_raw = Column(Text, default="[]")
    provenance = Column(String, default="ai_generated")
    human_review_status = Column(String, default="pending") # pending | verified | resolved | dismissed
    human_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="reconciliation_results")

    @property
    def supporting_points(self):
        try:
            return json.loads(self.supporting_points_raw or "[]")
        except Exception:
            return []

    @supporting_points.setter
    def supporting_points(self, value):
        self.supporting_points_raw = json.dumps(value if isinstance(value, list) else [])

    @property
    def concerning_points(self):
        try:
            return json.loads(self.concerning_points_raw or "[]")
        except Exception:
            return []

    @concerning_points.setter
    def concerning_points(self, value):
        self.concerning_points_raw = json.dumps(value if isinstance(value, list) else [])

    @property
    def evidence_considered(self):
        try:
            return json.loads(self.evidence_considered_raw or "[]")
        except Exception:
            return []

    @evidence_considered.setter
    def evidence_considered(self, value):
        self.evidence_considered_raw = json.dumps(value if isinstance(value, list) else [])

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "status": self.status,
            "confidence": self.confidence,
            "supporting_points": self.supporting_points,
            "concerning_points": self.concerning_points,
            "summary": self.summary,
            "recommendation": self.recommendation,
            "evidence_considered": self.evidence_considered,
            "provenance": self.provenance,
            "human_review_status": self.human_review_status,
            "human_notes": self.human_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
