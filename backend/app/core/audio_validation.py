import soundfile as sf
import numpy as np
import tempfile
import os
from typing import Tuple, Optional


class AudioValidator:
    """Validates audio quality before ASR processing."""

    # Minimum duration in seconds
    MIN_DURATION = 0.5
    # Maximum duration in seconds (prevent processing very long files without transcription)
    MAX_DURATION = 300  # 5 minutes
    # Minimum sample rate (Hz)
    MIN_SAMPLE_RATE = 8000
    # Expected sample rate for ASR
    TARGET_SAMPLE_RATE = 16000
    # Minimum RMS amplitude (detect silence)
    MIN_RMS = 0.01

    @staticmethod
    def validate_audio_bytes(audio_bytes: bytes, audio_format: str = "webm") -> Tuple[bool, Optional[str]]:
        """
        Validate audio quality.
        Returns (is_valid, error_message)
        """
        if not audio_bytes:
            return False, "Empty audio data"

        if len(audio_bytes) < 100:
            return False, "Audio too short (corrupt or incomplete)"

        try:
            suffix = f".{audio_format}"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            try:
                waveform, sample_rate = sf.read(tmp_path)

                # Check duration
                duration = len(waveform) / sample_rate
                if duration < AudioValidator.MIN_DURATION:
                    return False, f"Audio too short ({duration:.1f}s, minimum {AudioValidator.MIN_DURATION}s)"

                if duration > AudioValidator.MAX_DURATION:
                    return False, f"Audio too long ({duration:.0f}s, maximum {AudioValidator.MAX_DURATION}s)"

                # Check sample rate
                if sample_rate < AudioValidator.MIN_SAMPLE_RATE:
                    return False, f"Sample rate too low ({sample_rate} Hz)"

                # Check for silence (RMS energy)
                rms = float(np.sqrt(np.mean(waveform ** 2)))
                if rms < AudioValidator.MIN_RMS:
                    return False, "Audio appears to be silence or too quiet"

                return True, None

            finally:
                os.unlink(tmp_path)

        except Exception as e:
            return False, f"Failed to read audio: {str(e)}"

    @staticmethod
    def get_audio_metrics(audio_bytes: bytes, audio_format: str = "webm") -> Optional[dict]:
        """
        Extract audio metrics for logging/debugging.
        Returns dict with duration, sample_rate, rms, or None if invalid.
        """
        try:
            suffix = f".{audio_format}"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            try:
                waveform, sample_rate = sf.read(tmp_path)
                duration = len(waveform) / sample_rate
                rms = float(np.sqrt(np.mean(waveform ** 2)))

                return {
                    "duration_seconds": round(duration, 2),
                    "sample_rate_hz": int(sample_rate),
                    "rms_amplitude": round(rms, 4),
                    "total_samples": len(waveform)
                }
            finally:
                os.unlink(tmp_path)

        except Exception as e:
            return None


audio_validator = AudioValidator()
