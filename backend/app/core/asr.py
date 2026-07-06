from faster_whisper import WhisperModel
from app.core.config import settings
import tempfile, os


class ASREngine:
    """
    Wraps faster-whisper. Model is loaded once at startup (lazy singleton).
    Exposes transcribe(audio_bytes) → str
    """

    def __init__(self):
        self._model: WhisperModel | None = None

    def _load_model(self):
        """Lazy load — only download/init Whisper on first transcription call."""
        if self._model is None:
            print(f"[ASR] Loading Whisper model: {settings.WHISPER_MODEL}")
            self._model = WhisperModel(
                settings.WHISPER_MODEL,
                device=settings.WHISPER_DEVICE,
                compute_type=settings.WHISPER_COMPUTE_TYPE,
            )
            print("[ASR] Model ready.")

    def transcribe(self, audio_bytes: bytes, audio_format: str = "webm") -> str:
        """
        Accepts raw audio bytes (from browser MediaRecorder),
        writes to a temp file, runs Whisper, returns transcript string.
        """
        self._load_model()

        suffix = f".{audio_format}"
        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            dir=settings.TEMP_AUDIO_DIR,
            delete=False
        ) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            segments, _ = self._model.transcribe(
                tmp_path,
                beam_size=5,
                language="en",
                condition_on_previous_text=False,
            )
            transcript = " ".join(seg.text.strip() for seg in segments)
            return transcript.strip()
        finally:
            os.unlink(tmp_path)   # always clean up temp audio


# Singleton
asr_engine = ASREngine()
