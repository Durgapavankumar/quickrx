from fastapi import APIRouter, HTTPException, Query
from app.services.session_store import session_store
from app.services.corrections import apply_drug_correction
from app.models.prescription import (
    PrescriptionSession, SessionCreateRequest, DrugEntryUpdate, PatientSummary
)

router = APIRouter()


@router.post("/sessions", response_model=PrescriptionSession)
def create_session(body: SessionCreateRequest):
    """Start a new prescription session for a patient visit."""
    return session_store.create(body.patient_info)


@router.get("/sessions", response_model=list[PrescriptionSession])
def list_sessions(
    patient_name: str | None = Query(None, description="Filter by patient name (case-insensitive)"),
    limit: int = Query(50, ge=1, le=500),
):
    """Past sessions, newest first — pass patient_name for one patient's history."""
    return session_store.list_sessions(patient_name=patient_name, limit=limit)


@router.get("/patients", response_model=list[PatientSummary])
def list_patients():
    """Distinct patients seen so far, with visit counts, most recent first."""
    return session_store.list_patients()


@router.get("/sessions/{session_id}", response_model=PrescriptionSession)
def get_session(session_id: str):
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    if not session_store.delete(session_id):
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"message": "Session deleted."}


@router.patch("/sessions/{session_id}/drugs/{drug_index}", response_model=PrescriptionSession)
def update_drug(session_id: str, drug_index: int, update: DrugEntryUpdate):
    """
    Clinician correction of an extracted entry. Send only the changed fields;
    an empty body just marks the entry as verified. The entry is re-validated
    against the formulary and unflagged (manually_verified = true).
    """
    session = _get_or_404(session_id)
    if not 0 <= drug_index < len(session.drugs):
        raise HTTPException(status_code=400, detail="Invalid drug index.")

    corrected = apply_drug_correction(session.drugs[drug_index], update)
    return session_store.update_drug(session_id, drug_index, corrected)


@router.delete("/sessions/{session_id}/drugs/{drug_index}", response_model=PrescriptionSession)
def remove_drug(session_id: str, drug_index: int):
    """Remove a wrongly extracted drug entry from the session."""
    _get_or_404(session_id)
    session = session_store.remove_drug(session_id, drug_index)
    if session is None:
        raise HTTPException(status_code=400, detail="Invalid drug index.")
    return session


def _get_or_404(session_id: str) -> PrescriptionSession:
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session
