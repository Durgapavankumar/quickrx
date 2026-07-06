from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.core.asr import asr_engine
from app.core.nlp.extractor import extractor
from app.services.session_store import session_store
from app.models.prescription import TranscribeResponse

router = APIRouter()


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    session_id: str = Form(...),
    audio: UploadFile = File(...),
):
    """
    Accepts a WAV/WebM audio blob from the browser.
    Runs ASR → NLP extraction → appends DrugEntry to session.
    Returns transcript + structured DrugEntry.
    """
    if not session_store.get(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file received.")

    content_type = audio.content_type or "audio/webm"
    fmt = content_type.split("/")[-1].split(";")[0]  # e.g. "webm", "wav"

    transcript = asr_engine.transcribe(audio_bytes, audio_format=fmt)

    if not transcript:
        raise HTTPException(status_code=422, detail="ASR returned empty transcript.")

    drug_entry = extractor.extract(transcript)
    session_store.add_drug(session_id, drug_entry)

    return TranscribeResponse(transcript=transcript, drug_entry=drug_entry)
