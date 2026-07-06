from fastapi import APIRouter, HTTPException
from app.services.session_store import session_store
from app.models.prescription import (
    PrescriptionSession, SessionCreateRequest, DrugEntry
)

router = APIRouter()


@router.post("/sessions", response_model=PrescriptionSession)
def create_session(body: SessionCreateRequest):
    """Start a new prescription session for a patient visit."""
    return session_store.create(body.patient_info)


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
def update_drug(session_id: str, drug_index: int, updated: DrugEntry):
    """Allow clinician to manually correct a flagged drug entry."""
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if drug_index < 0 or drug_index >= len(session.drugs):
        raise HTTPException(status_code=400, detail="Invalid drug index.")

    session.drugs[drug_index] = updated
    session.flagged_count = sum(1 for d in session.drugs if d.flagged_for_review)
    return session
