import { VoiceCapture } from "../VoiceCapture/VoiceCapture";
import { PrescriptionCard } from "../PrescriptionCard/PrescriptionCard";
import { api } from "../../api/client";

export function SessionPanel({ session, drugs, transcripts, onDrugAdded, onNewSession }) {
  const { session_id, patient_info, flagged_count } = session;

  const handleExportPdf = () => {
    window.open(api.exportPdfUrl(session_id), "_blank");
  };

  const handleExportJson = async () => {
    const url = api.exportJsonUrl(session_id);
    const res = await fetch(url);
    const blob = await res.blob();
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `prescription_${session_id.slice(0, 8)}.json`;
    link.click();
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
            &nbsp;·&nbsp;Dr. {patient_info.doctor_name}
            {patient_info.clinic_name && ` · ${patient_info.clinic_name}`}
            &nbsp;·&nbsp;{patient_info.date}
          </div>
        </div>
        <div style={{ fontSize: 12, opacity: 0.7 }}>
          Session: {session_id.slice(0, 8)}…
        </div>
      </div>

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
              transcript={transcripts[i]}
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
            { } Export JSON
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
