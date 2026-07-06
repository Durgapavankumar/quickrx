import { useState } from "react";
import { useRecorder } from "../../hooks/useRecorder";
import { api } from "../../api/client";

export function VoiceCapture({ sessionId, onDrugAdded, disabled }) {
  const { isRecording, start, stop, error: micError } = useRecorder();
  const [status, setStatus] = useState("idle"); // idle | recording | processing | done | error
  const [lastTranscript, setLastTranscript] = useState("");
  const [apiError, setApiError] = useState("");

  const handleToggle = async () => {
    if (isRecording) {
      setStatus("processing");
      const blob = await stop();
      if (!blob) { setStatus("error"); return; }

      try {
        const result = await api.transcribeAudio(sessionId, blob);
        setLastTranscript(result.transcript);
        onDrugAdded(result.drug_entry, result.transcript);
        setStatus("done");
        setTimeout(() => setStatus("idle"), 1800);
      } catch (err) {
        setApiError(err.message);
        setStatus("error");
      }
    } else {
      setApiError("");
      setStatus("recording");
      await start();
    }
  };

  const btnColor = {
    idle:       "#2E75B6",
    recording:  "#C55A11",
    processing: "#595959",
    done:       "#2E7D32",
    error:      "#b00020",
  }[status];

  const btnLabel = {
    idle:       "🎙 Dictate Drug",
    recording:  "⏹ Stop Recording",
    processing: "⏳ Processing...",
    done:       "✓ Added",
    error:      "Try Again",
  }[status];

  return (
    <div style={{ textAlign: "center", margin: "20px 0" }}>
      <button
        onClick={handleToggle}
        disabled={disabled || status === "processing"}
        style={{
          padding: "14px 32px", background: btnColor, color: "#fff",
          border: "none", borderRadius: 32, fontSize: 16, fontWeight: 700,
          cursor: "pointer", minWidth: 210,
          boxShadow: isRecording ? "0 0 0 4px rgba(197,90,17,0.25)" : "none",
          transition: "all 0.2s",
        }}
      >
        {btnLabel}
      </button>

      {isRecording && (
        <div style={{ marginTop: 10, color: "#C55A11", fontWeight: 600, fontSize: 13 }}>
          🔴 Recording... speak clearly, then press Stop
        </div>
      )}

      {status === "processing" && (
        <div style={{ marginTop: 10, color: "#595959", fontSize: 13 }}>
          Transcribing with Whisper + extracting prescription fields...
        </div>
      )}

      {lastTranscript && status === "done" && (
        <div style={{ marginTop: 10, fontSize: 12, color: "#555",
          background: "#F7FAFD", padding: "8px 14px", borderRadius: 6,
          border: "1px solid #dce8f0", display: "inline-block" }}>
          <strong>Heard:</strong> "{lastTranscript}"
        </div>
      )}

      {(micError || apiError) && (
        <div style={{ marginTop: 10, color: "#b00020", fontSize: 13, fontWeight: 500 }}>
          ⚠ {micError || apiError}
        </div>
      )}

      <div style={{ marginTop: 8, fontSize: 11, color: "#888" }}>
        Say the drug name, dose, frequency, and duration — e.g.<br />
        <em>"Paracetamol 500mg twice daily for 5 days after food"</em>
      </div>
    </div>
  );
}
