import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { formatDoctor } from "../../utils/format";

/**
 * Past visits for one patient — shown inside the session panel.
 * Excludes the session currently in progress.
 */
export function PatientHistory({ patientName, currentSessionId }) {
  const [sessions, setSessions] = useState(null);   // null = loading
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    api.getPatientHistory(patientName)
      .then((all) => {
        if (!cancelled) {
          setSessions(all.filter((s) => s.session_id !== currentSessionId));
        }
      })
      .catch((e) => !cancelled && setError(e.message));
    return () => { cancelled = true; };
  }, [patientName, currentSessionId]);

  if (error) {
    return <HistoryBox><span style={{ color: "#b00020" }}>⚠ {error}</span></HistoryBox>;
  }
  if (sessions === null) {
    return <HistoryBox><span style={{ color: "#888" }}>Loading history…</span></HistoryBox>;
  }
  if (sessions.length === 0) {
    return <HistoryBox><span style={{ color: "#888" }}>No previous visits for this patient.</span></HistoryBox>;
  }

  return (
    <HistoryBox>
      {sessions.map((s) => (
        <div key={s.session_id} style={{
          padding: "8px 0", borderBottom: "1px solid #e4ecf4",
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
            <span style={{ fontWeight: 700, color: "#1F3864" }}>
              {s.patient_info.date || s.created_at.slice(0, 10)}
              {s.patient_info.doctor_name && (
                <span style={{ fontWeight: 400, color: "#666" }}>
                  {" "}· {formatDoctor(s.patient_info.doctor_name)}
                </span>
              )}
            </span>
            <span style={{ color: "#888" }}>
              {s.drugs.length} drug{s.drugs.length !== 1 ? "s" : ""}
            </span>
          </div>
          {s.drugs.length > 0 && (
            <div style={{ fontSize: 12, color: "#444", marginTop: 3 }}>
              {s.drugs.map((d, i) => {
                const name = d.generic_name || d.drug_name || "Unknown";
                const dose = d.dose ? ` ${d.dose}${d.dose_unit ? " " + d.dose_unit : ""}` : "";
                const freq = d.frequency ? `, ${d.frequency}` : "";
                return <div key={i}>• {name}{dose}{freq}</div>;
              })}
            </div>
          )}
        </div>
      ))}
    </HistoryBox>
  );
}

function HistoryBox({ children }) {
  return (
    <div style={{
      background: "#F7FAFD", border: "1px solid #dce8f0", borderRadius: 8,
      padding: "10px 16px", marginBottom: 16, maxHeight: 260, overflowY: "auto",
    }}>
      <div style={{ fontSize: 11, fontWeight: 700, color: "#2E75B6",
        textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 }}>
        Previous Visits
      </div>
      {children}
    </div>
  );
}
