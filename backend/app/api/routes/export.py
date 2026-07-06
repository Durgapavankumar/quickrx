from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, JSONResponse
from app.services.session_store import session_store
from app.services.pdf_generator import generate_prescription_pdf

router = APIRouter()


@router.get("/sessions/{session_id}/export/pdf")
def export_pdf(session_id: str):
    """Returns a prescription PDF for the given session."""
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if not session.drugs:
        raise HTTPException(status_code=400, detail="No drugs in session to export.")

    pdf_bytes = generate_prescription_pdf(session)
    filename = f"prescription_{session_id[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/sessions/{session_id}/export/json")
def export_json(session_id: str):
    """Returns the full structured session as JSON."""
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return JSONResponse(content=session.model_dump())
