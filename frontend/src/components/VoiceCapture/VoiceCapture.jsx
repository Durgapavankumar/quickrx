import { useEffect, useState } from "react";
import { useRecorder } from "../../hooks/useRecorder";
import { useLiveTranscript } from "../../hooks/useLiveTranscript";
import { api } from "../../api/client";

// Rotating example dictations — cover the formulary's breadth so first-time
// users learn the range of phrasings the NLP understands.
const EXAMPLES = [
  "Paracetamol 500mg twice daily for 5 days after food",
  "Amoxicillin 250mg three times a day for one week",
  "Tab Pantoprazole 40mg once daily before breakfast for 2 weeks",
  "Cetirizine 10mg at bedtime for 3 days",
  "Azithromycin 500mg 1-0-1 for 3 days after meals",
  "Metformin 500mg twice daily with food for one month",
  "Ibuprofen 400mg every 8 hours for 2 days if needed",
];

function MicIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
      strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="9" y="2.5" width="6" height="11.5" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0" />
      <line x1="12" y1="18" x2="12" y2="21.5" />
    </svg>
  );
}

function StopIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <rect x="6.5" y="6.5" width="11" height="11" rx="2.5" />
    </svg>
  );
}

function Spinner() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4"
      strokeLinecap="round" aria-hidden="true"
      style={{ animation: "spin 0.9s linear infinite" }}>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      <path d="M12 3a9 9 0 1 0 9 9" />
    </svg>
  );
}

export function VoiceCapture({ sessionId, onDrugAdded, disabled }) {
  const { isRecording, start, stop, error: micError, levels } = useRecorder();
  const live = useLiveTranscript();
  const [status, setStatus] = useState("idle"); // idle | recording | processing | done | error
  const [lastTranscript, setLastTranscript] = useState("");
  const [apiError, setApiError] = useState("");
  const [exampleIdx, setExampleIdx] = useState(0);

  // rotate the example hint every 3.5s while not recording
  useEffect(() => {
    if (isRecording) return;
    const id = setInterval(() => setExampleIdx((i) => (i + 1) % EXAMPLES.length), 3500);
    return () => clearInterval(id);
  }, [isRecording]);

  const handleToggle = async () => {
    if (isRecording) {
      live.stop();
      setStatus("processing");
      const blob = await stop();
      if (!blob) { setStatus("error"); return; }

      try {
        const result = await api.transcribeAudio(sessionId, blob);
        setLastTranscript(result.transcript);
        onDrugAdded(result.drug_entry, result.transcript);
        setStatus("done");
        setTimeout(() => setStatus("idle"), 2200);
      } catch (err) {
        setApiError(err.message);
        setStatus("error");
      }
    } else {
      setApiError("");
      setLastTranscript("");
      setStatus("recording");
      await start();
      live.start();
    }
  };

  const stateLabel = {
    idle:       "Tap to dictate a drug",
    recording:  "Listening — tap to finish",
    processing: "Transcribing with Whisper…",
    done:       "✓ Added to prescription",
    error:      "Tap to try again",
  }[status];

  return (
    <div className="dictate-stage">
      <button
        className={`mic-btn ${isRecording ? "recording" : ""} ${status === "processing" ? "processing" : ""}`}
        onClick={handleToggle}
        disabled={disabled || status === "processing"}
        aria-label={isRecording ? "Stop recording" : "Start dictating"}
      >
        {status === "processing" ? <Spinner /> : isRecording ? <StopIcon /> : <MicIcon />}
      </button>

      <div className={`mic-state-label ${isRecording ? "rec" : ""}`}>{stateLabel}</div>

      {/* live waveform while recording */}
      {isRecording && (
        <div className="wave" aria-hidden="true">
          {levels.map((v, i) => (
            <span key={i} style={{ height: `${5 + v * 34}px` }} />
          ))}
        </div>
      )}

      {/* live transcript preview while recording */}
      {isRecording && live.supported && (
        <>
          <div className="live-transcript">
            {live.preview
              ? <>{live.preview}<span className="caret" /></>
              : <span className="placeholder">Start speaking — your words appear here…<span className="caret" /></span>}
          </div>
          <div className="live-note">
            Live preview — the final transcript is refined by the AI model when you stop.
          </div>
        </>
      )}

      {/* confirmation of what Whisper heard */}
      {lastTranscript && status === "done" && (
        <div className="heard-box">
          <strong>Heard:</strong> “{lastTranscript}”
        </div>
      )}

      {(micError || apiError) && (
        <div className="alert-error" style={{ display: "inline-block", marginTop: 14 }}>
          ⚠ {micError || apiError}
        </div>
      )}

      {/* rotating example hints */}
      {!isRecording && status !== "processing" && (
        <div className="hint-rotator">
          <div className="hint-title">Try saying</div>
          <div className="hint-line" key={exampleIdx}>
            “{EXAMPLES[exampleIdx]}”
          </div>
        </div>
      )}
    </div>
  );
}
