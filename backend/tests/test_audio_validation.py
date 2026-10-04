"""
Audio Validation Tests
Run: python -m pytest tests/test_audio_validation.py -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.audio_validation import audio_validator
import tempfile


def test_empty_audio():
    """Empty audio should fail validation."""
    is_valid, error_msg = audio_validator.validate_audio_bytes(b"", "webm")
    assert not is_valid
    assert "Empty" in error_msg


def test_corrupted_audio():
    """Corrupted/too-short audio should fail validation."""
    is_valid, error_msg = audio_validator.validate_audio_bytes(b"x" * 50, "webm")
    assert not is_valid
    assert "corrupt" in error_msg.lower() or "short" in error_msg.lower()


def test_valid_wav_audio():
    """Valid WAV audio file should pass validation."""
    import soundfile as sf
    import numpy as np

    # Generate 1 second of synthetic audio at 16kHz
    sample_rate = 16000
    duration = 1.0
    frequency = 440  # A4 note
    t = np.linspace(0, duration, int(sample_rate * duration))
    waveform = 0.3 * np.sin(2 * np.pi * frequency * t)

    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, waveform, sample_rate)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()

        is_valid, error_msg = audio_validator.validate_audio_bytes(audio_bytes, "wav")
        assert is_valid, f"Valid audio failed validation: {error_msg}"
    finally:
        os.unlink(tmp_path)


def test_silence_audio():
    """Silent audio should fail validation."""
    import soundfile as sf
    import numpy as np

    # Generate 1 second of silence (very low amplitude)
    sample_rate = 16000
    duration = 1.0
    waveform = np.zeros(int(sample_rate * duration)) * 0.00001

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, waveform, sample_rate)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()

        is_valid, error_msg = audio_validator.validate_audio_bytes(audio_bytes, "wav")
        assert not is_valid
        assert "silence" in error_msg.lower() or "quiet" in error_msg.lower()
    finally:
        os.unlink(tmp_path)


def test_too_short_audio():
    """Audio shorter than minimum duration should fail."""
    import soundfile as sf
    import numpy as np

    # Generate 0.2 seconds of audio
    sample_rate = 16000
    duration = 0.2
    frequency = 440
    t = np.linspace(0, duration, int(sample_rate * duration))
    waveform = 0.3 * np.sin(2 * np.pi * frequency * t)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, waveform, sample_rate)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()

        is_valid, error_msg = audio_validator.validate_audio_bytes(audio_bytes, "wav")
        assert not is_valid
        assert "too short" in error_msg.lower()
    finally:
        os.unlink(tmp_path)


def test_audio_metrics():
    """Metrics extraction should work for valid audio."""
    import soundfile as sf
    import numpy as np

    sample_rate = 16000
    duration = 2.0
    frequency = 440
    t = np.linspace(0, duration, int(sample_rate * duration))
    waveform = 0.3 * np.sin(2 * np.pi * frequency * t)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, waveform, sample_rate)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()

        metrics = audio_validator.get_audio_metrics(audio_bytes, "wav")
        assert metrics is not None
        assert abs(metrics["duration_seconds"] - 2.0) < 0.1
        assert metrics["sample_rate_hz"] == 16000
        assert metrics["rms_amplitude"] > 0
        assert metrics["total_samples"] > 0
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    try:
        test_empty_audio()
        print("✓ Empty audio validation")

        test_corrupted_audio()
        print("✓ Corrupted audio detection")

        test_valid_wav_audio()
        print("✓ Valid WAV audio acceptance")

        test_silence_audio()
        print("✓ Silence detection")

        test_too_short_audio()
        print("✓ Too short audio detection")

        test_audio_metrics()
        print("✓ Audio metrics extraction")

        print("\n✅ All audio validation tests passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
