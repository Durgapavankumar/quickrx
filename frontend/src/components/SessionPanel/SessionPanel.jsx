import { useState } from "react";
import { VoiceCapture } from "../VoiceCapture/VoiceCapture";
import { PrescriptionCard } from "../PrescriptionCard/PrescriptionCard";
import { PatientHistory } from "../PatientHistory/PatientHistory";
import { api } from "../../api/client";
import { formatDoctor } from "../../utils/format";

export function SessionPanel({ session, onSessionChange, onDrugAdded, onNewSession }) {
  const { session_id, patient_info, drugs, flagged_count } = session;
  const [showHistory, setShowHistory] = useState(false);
  const [error, setError] = useState("");

  const wrap = (fn) => async (...args) => {
    setError("");
    try {
      const updated = await fn(...args);
      onSessionChange(updated);
    } catch (e) {
      setError(e.message);
      throw e;   // let the card know the action failed (keeps edit mode open)
    }
  };

  const handleSaveDrug   = wrap((index, changed) => api.updateDrug(session_id, index, changed));
  const handleVerifyDrug = wrap((index) => api.updateDrug(session_id, index, {}));
  const handleDeleteDrug = wrap((index) => api.deleteDrug(session_id, index));

  // Fetched as blobs (not plain links) so the request carries the header that
  // bypasses ngrok's browser interstitial when tunnelling the backend.
  const download = (blob, filename) => {
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const handleExportPdf = async () => {
    setError("");
    try {
      download(await api.exportPdfBlob(session_id), `prescription_${session_id.slice(0, 8)}.pdf`);
    } catch (e) {
      setError(e.message);
    }
  };

  const handleExportJson = async () => {
    setError("");
    try {
      download(await api.exportJsonBlob(session_id), `prescription_${session_id.slice(0, 8)}.json`);
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <div>
      {/* Session header */}
      <div style={{
        background: "#1F3864", color: "#fff", borderRadius: 10,
        padding: "14px 20px", marginBottom: 20,
        display: "flex", justifyContent: "space-between", alignItems: "center",
      }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 700 }}>{patient_info.patient_name}</div>
          <div style={{ fontSize: 12, opacity: 0.75 }}>
            {[patient_info.patient_age, patient_info.patient_gender].filter(Boolean).join(", ")}
            &nbsp;·&nbsp;{formatDoctor(patient_info.doctor_name)}
            {patient_info.clinic_name && ` · ${patient_info.clinic_name}`}
            &nbsp;·&nbsp;{patient_info.date}
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <button
            onClick={() => setShowHistory((v) => !v)}
            style={{
              background: showHistory ? "#2E75B6" : "rgba(255,255,255,0.12)",
              color: "#fff", border: "1px solid rgba(255,255,255,0.3)",
              borderRadius: 6, padding: "5px 12px", fontSize: 12,
              fontWeight: 600, cursor: "pointer",
            }}
          >
            {showHistory ? "Hide History" : "📋 History"}
          </button>
          <div style={{ fontSize: 11, opacity: 0.6, marginTop: 5 }}>
            Session: {session_id.slice(0, 8)}…
          </div>
        </div>
      </div>

      {/* Past visits for this patient */}
      {showHistory && (
        <PatientHistory
          patientName={patient_info.patient_name}
          currentSessionId={session_id}
        />
      )}

      {error && (
        <div style={{ background: "#FFEBEE", color: "#b00020", padding: "8px 12px",
          borderRadius: 6, marginBottom: 12, fontSize: 13 }}>
          ⚠ {error}
        </div>
      )}

      {/* Voice recorder */}
      <VoiceCapture
        sessionId={session_id}
        onDrugAdded={onDrugAdded}
        disabled={false}
      />

      {/* Drug list */}
      {drugs.length === 0 ? (
        <div style={{ textAlign: "center", color: "#999", padding: "30px 0", fontSize: 14 }}>
          No drugs added yet. Dictate the first drug above.
        </div>
      ) : (
        <div style={{ marginTop: 20 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
            <h3 style={{ color: "#1F3864", margin: 0 }}>
              Prescription ({drugs.length} drug{drugs.length > 1 ? "s" : ""})
            </h3>
            {flagged_count > 0 && (
              <span style={{ background: "#FBE5D6", color: "#C55A11",
                padding: "4px 12px", borderRadius: 12, fontSize: 12, fontWeight: 600 }}>
                ⚠ {flagged_count} flagged
              </span>
            )}
          </div>

          {drugs.map((drug, i) => (
            <PrescriptionCard
              key={i}
              index={i}
              drug={drug}
              onSave={handleSaveDrug}
              onVerify={handleVerifyDrug}
              onDelete={handleDeleteDrug}
            />
          ))}
        </div>
      )}

      {/* Actions */}
      {drugs.length > 0 && (
        <div style={{ display: "flex", gap: 12, marginTop: 24 }}>
          <button onClick={handleExportPdf} style={btnStyle("#1F3864")}>
            ⬇ Export PDF
          </button>
          <button onClick={handleExportJson} style={btnStyle("#2E75B6")}>
            {"{ }"} Export JSON
          </button>
          <button onClick={onNewSession} style={btnStyle("#595959")}>
            + New Patient
          </button>
        </div>
      )}
    </div>
  );
}

const btnStyle = (bg) => ({
  flex: 1, padding: "11px 0", background: bg, color: "#fff",
  border: "none", borderRadius: 8, fontSize: 14, fontWeight: 600,
  cursor: "pointer",
});
