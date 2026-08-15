import { useEffect, useState } from "react";
import { api } from "../../api/client";

const today = new Date().toISOString().split("T")[0];

export function PatientForm({ onStart, loading }) {
  const [form, setForm] = useState({
    doctor_name: "", clinic_name: "",
    patient_name: "", patient_age: "", patient_gender: "", date: today,
  });
  const [recentPatients, setRecentPatients] = useState([]);

  useEffect(() => {
    api.listPatients()
      .then((p) => setRecentPatients(p.slice(0, 8)))
      .catch(() => {});   // history is a convenience — never block the form
  }, []);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const pickPatient = async (name) => {
    setForm((f) => ({ ...f, patient_name: name }));
    try {
      // prefill demographics from the patient's most recent visit
      const [latest] = await api.getPatientHistory(name, 1);
      if (latest) {
        setForm((f) => ({
          ...f,
          patient_name: name,
          patient_age: latest.patient_info.patient_age || f.patient_age,
          patient_gender: latest.patient_info.patient_gender || f.patient_gender,
        }));
      }
    } catch {
      /* prefill only — name is already set */
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.doctor_name.trim() || !form.patient_name.trim()) return;
    onStart(form);
  };

  return (
    <form onSubmit={handleSubmit}>
      <div style={{ marginBottom: 26 }}>
        <div className="form-section-label">Clinician</div>
        <div className="form-grid">
          <div className="field">
            <label>Doctor name *</label>
            <input value={form.doctor_name} onChange={set("doctor_name")} placeholder="Dr. Surname" />
          </div>
          <div className="field">
            <label>Clinic / hospital</label>
            <input value={form.clinic_name} onChange={set("clinic_name")} placeholder="City Clinic" />
          </div>
        </div>
      </div>

      <div style={{ marginBottom: 28 }}>
        <div className="form-section-label">Patient</div>

        {recentPatients.length > 0 && (
          <div style={{ marginBottom: 14 }}>
            <div className="field"><label>Returning patient</label></div>
            <div className="chip-row">
              {recentPatients.map((p) => (
                <button
                  key={p.patient_name}
                  type="button"
                  className={`patient-chip ${form.patient_name === p.patient_name ? "active" : ""}`}
                  onClick={() => pickPatient(p.patient_name)}
                  title={`${p.visit_count} visit${p.visit_count > 1 ? "s" : ""} · last ${p.last_visit.slice(0, 10)}`}
                >
                  {p.patient_name} · {p.visit_count}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="form-grid" style={{ marginBottom: 14 }}>
          <div className="field">
            <label>Patient name *</label>
            <input value={form.patient_name} onChange={set("patient_name")} placeholder="Full name" />
          </div>
          <div className="field">
            <label>Age</label>
            <input value={form.patient_age} onChange={set("patient_age")} placeholder="e.g. 34" />
          </div>
        </div>
        <div className="form-grid">
          <div className="field">
            <label>Gender</label>
            <select value={form.patient_gender} onChange={set("patient_gender")}>
              <option value="">—</option>
              <option>Male</option><option>Female</option><option>Other</option>
            </select>
          </div>
          <div className="field">
            <label>Date</label>
            <input type="date" value={form.date} onChange={set("date")} />
          </div>
        </div>
      </div>

      <button
        type="submit"
        className="btn btn-primary btn-block"
        disabled={loading || !form.doctor_name.trim() || !form.patient_name.trim()}
      >
        {loading ? "Starting…" : "Begin consultation →"}
      </button>

      {/* one-click demo session — no typing needed */}
      <div style={{ textAlign: "center", marginTop: 14 }}>
        <button
          type="button"
          className="link-btn"
          style={{ fontSize: 13 }}
          disabled={loading}
          onClick={() => onStart({
            doctor_name: "Dr. Test",
            clinic_name: "Demo Clinic",
            patient_name: "Test Patient",
            patient_age: "30",
            patient_gender: "",
            date: today,
          })}
        >
          ⚡ or skip the form — quick demo session
        </button>
      </div>
    </form>
  );
}
