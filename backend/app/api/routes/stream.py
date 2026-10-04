from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from app.core.asr import asr_engine
from app.core.nlp.extractor import extractor
from app.services.session_store import session_store
import asyncio
import json

router = APIRouter()


@router.websocket("/ws/transcribe/{session_id}")
async def websocket_transcribe(websocket: WebSocket, session_id: str):
    """
    Real-time voice streaming endpoint.
    Client sends audio chunks (bytes), receives transcript + drug entries as they stream.
    Keeps connection alive for continuous use within a session.
    """
    if not session_store.get(session_id):
        await websocket.close(code=4004, reason=f"Session {session_id} not found")
        return

    await websocket.accept()

    try:
        audio_chunks = []

        while True:
            data = await websocket.receive()

            if data["type"] == "websocket.receive.bytes":
                audio_chunks.append(data["bytes"])

            elif data["type"] == "websocket.receive.text":
                msg = json.loads(data["text"])
                action = msg.get("action")

                if action == "transcribe":
                    if not audio_chunks:
                        await websocket.send_json({
                            "error": "No audio data received",
                            "status": "error"
                        })
                        continue

                    audio_bytes = b"".join(audio_chunks)
                    fmt = msg.get("format", "webm")

                    try:
                        transcript = asr_engine.transcribe(audio_bytes, audio_format=fmt)

                        if not transcript:
                            await websocket.send_json({
                                "error": "ASR returned empty transcript",
                                "status": "error"
                            })
                            audio_chunks = []
                            continue

                        drug_entry = extractor.extract(transcript)
                        session_store.add_drug(session_id, drug_entry)

                        await websocket.send_json({
                            "transcript": transcript,
                            "drug_entry": drug_entry.model_dump() if hasattr(drug_entry, 'model_dump') else drug_entry,
                            "status": "success"
                        })

                        audio_chunks = []

                    except Exception as e:
                        await websocket.send_json({
                            "error": str(e),
                            "status": "error"
                        })
                        audio_chunks = []

                elif action == "reset":
                    audio_chunks = []
                    await websocket.send_json({
                        "status": "reset",
                        "message": "Audio buffer cleared"
                    })

                elif action == "close":
                    await websocket.close(code=1000)
                    break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({
            "error": f"WebSocket error: {str(e)}",
            "status": "error"
        })
        await websocket.close(code=1011)
