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

  let body;
  if (error) {
    body = <span style={{ color: "var(--danger)" }}>⚠ {error}</span>;
  } else if (sessions === null) {
    body = <span style={{ color: "var(--faint)" }}>Loading history…</span>;
  } else if (sessions.length === 0) {
    body = <span style={{ color: "var(--faint)" }}>No previous visits for this patient.</span>;
  } else {
    body = sessions.map((s) => (
      <div key={s.session_id} className="history-visit">
        <div className="visit-head">
          <span className="visit-date">
            {s.patient_info.date || s.created_at.slice(0, 10)}
            {s.patient_info.doctor_name && (
              <span className="visit-doc"> · {formatDoctor(s.patient_info.doctor_name)}</span>
            )}
          </span>
          <span className="visit-count">
            {s.drugs.length} drug{s.drugs.length !== 1 ? "s" : ""}
          </span>
        </div>
        {s.drugs.map((d, i) => {
          const name = d.generic_name || d.drug_name || "Unknown";
          const dose = d.dose ? ` ${d.dose}${d.dose_unit ? " " + d.dose_unit : ""}` : "";
          const freq = d.frequency ? `, ${d.frequency}` : "";
          return <div key={i} className="visit-drug">• {name}{dose}{freq}</div>;
        })}
      </div>
    ));
  }

  return (
    <div className="history-box">
      <div className="h-title">Previous visits</div>
      {body}
    </div>
  );
}
