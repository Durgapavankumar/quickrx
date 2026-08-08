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

  const initial = (patient_info.patient_name || "?").trim().charAt(0).toUpperCase();

  return (
    <div>
      {/* Patient banner */}
      <div className="card patient-banner">
        <div className="avatar">{initial}</div>
        <div>
          <div className="p-name">{patient_info.patient_name}</div>
          <div className="p-meta">
            {[patient_info.patient_age, patient_info.patient_gender].filter(Boolean).join(", ")}
            {(patient_info.patient_age || patient_info.patient_gender) && " · "}
            {formatDoctor(patient_info.doctor_name)}
            {patient_info.clinic_name && ` · ${patient_info.clinic_name}`}
            {" · "}{patient_info.date}
          </div>
        </div>
        <div className="b-spacer" />
        <div>
          <button className="btn btn-quiet btn-sm" onClick={() => setShowHistory((v) => !v)}>
            {showHistory ? "Hide history" : "History"}
          </button>
          <div className="session-id-tag">#{session_id.slice(0, 8)}</div>
        </div>
      </div>

      {/* Past visits for this patient */}
      {showHistory && (
        <PatientHistory
          patientName={patient_info.patient_name}
          currentSessionId={session_id}
        />
      )}

      {error && <div className="alert-error">⚠ {error}</div>}

      {/* Voice recorder */}
      <VoiceCapture
        sessionId={session_id}
        onDrugAdded={onDrugAdded}
        disabled={false}
      />

      {/* Drug list */}
      {drugs.length === 0 ? (
        <div className="empty-note">
          Nothing prescribed yet — dictate the first drug above.
        </div>
      ) : (
        <div>
          <div className="rx-list-head">
            <h3>Prescription</h3>
            <span className="count">
              {drugs.length} drug{drugs.length > 1 ? "s" : ""}
            </span>
            <div style={{ flex: 1 }} />
            {flagged_count > 0 && (
              <span className="flag-pill">⚠ {flagged_count} to review</span>
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
        <div className="actions-row">
          <button className="btn btn-primary" onClick={handleExportPdf}>
            ↓ Export PDF
          </button>
          <button className="btn btn-accent" onClick={handleExportJson}>
            {"{ }"} Export JSON
          </button>
          <button className="btn btn-quiet" onClick={onNewSession}>
            + New patient
          </button>
        </div>
      )}
    </div>
  );
}
