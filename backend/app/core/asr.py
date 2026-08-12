import torch
import torchaudio
from transformers import pipeline
from app.core.config import settings
import tempfile, os


class ASREngine:
    """
    Uses AI4Bharat's Wav2Vec2-Indic-en model for Indian English ASR.
    Optimized for Indian accents and medical terminology.
    Model is loaded once at startup (lazy singleton).
    Exposes transcribe(audio_bytes) → str
    """

    def __init__(self):
        self._model = None
        self._device = self._get_device()

    def _get_device(self):
        if settings.ASR_DEVICE == "cpu":
            return "cpu"
        return "cuda" if torch.cuda.is_available() else "cpu"

    def _load_model(self):
        """Lazy load — only download/init model on first transcription call."""
        if self._model is None:
            print(f"[ASR] Loading Indian English model: {settings.ASR_MODEL}")
            self._model = pipeline(
                "automatic-speech-recognition",
                model=settings.ASR_MODEL,
                device=0 if self._device == "cuda" else -1,
            )
            print("[ASR] Model ready for Indian English transcription.")

    def _convert_audio(self, audio_bytes: bytes, audio_format: str) -> torch.Tensor:
        """Convert raw audio bytes to tensor."""
        suffix = f".{audio_format}"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            waveform, sample_rate = torchaudio.load(tmp_path)
            if sample_rate != 16000:
                resampler = torchaudio.transforms.Resample(sample_rate, 16000)
                waveform = resampler(waveform)
            return waveform.squeeze(0)
        finally:
            os.unlink(tmp_path)

    def transcribe(self, audio_bytes: bytes, audio_format: str = "webm") -> str:
        """
        Accepts raw audio bytes (from browser MediaRecorder),
        converts to 16kHz wav, runs Indian English ASR, returns transcript string.
        """
        self._load_model()

        waveform = self._convert_audio(audio_bytes, audio_format)
        result = self._model(waveform.numpy())
        transcript = result.get("text", "").strip()
        return transcript


# Singleton
asr_engine = ASREngine()
