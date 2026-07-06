from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ConfidenceLevel(str, Enum):
    HIGH = "high"       # >= 0.85
    MEDIUM = "medium"   # 0.60 – 0.84
    LOW = "low"         # < 0.60  → flagged for clinician review


class DrugEntry(BaseModel):
    """Single extracted drug line — the core output unit of the NLP pipeline."""
    drug_name: Optional[str] = None          # as spoken / matched
    generic_name: Optional[str] = None       # from drug dictionary
    category: Optional[str] = None           # drug class from dictionary
    dose: Optional[str] = None               # numeric value e.g. "500"
    dose_unit: Optional[str] = None          # mg / mcg / ml / IU etc.
    frequency: Optional[str] = None          # e.g. "twice daily"
    duration: Optional[str] = None           # e.g. "5 days"
    duration_unit: Optional[str] = None      # days / weeks / months
    route: Optional[str] = None              # oral / topical / inhaled etc.
    instructions: Optional[str] = None       # after food, before bed, etc.
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel = ConfidenceLevel.LOW
    flagged_for_review: bool = False
    raw_transcript: Optional[str] = None     # original ASR text for audit trail


class PatientInfo(BaseModel):
    """Minimum patient + clinician data required on a prescription."""
    patient_name: Optional[str] = None
    patient_age: Optional[str] = None
    patient_gender: Optional[str] = None
    doctor_name: Optional[str] = None
    clinic_name: Optional[str] = None
    date: Optional[str] = None               # ISO date string


class PrescriptionSession(BaseModel):
    """One patient visit — may contain multiple drug entries."""
    session_id: str
    patient_info: PatientInfo
    drugs: list[DrugEntry] = []
    flagged_count: int = 0
    created_at: str


class TranscribeRequest(BaseModel):
    """Request payload for audio transcription."""
    session_id: str


class TranscribeResponse(BaseModel):
    """What the ASR module returns."""
    transcript: str
    drug_entry: DrugEntry


class SessionCreateRequest(BaseModel):
    patient_info: PatientInfo
