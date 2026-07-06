import { useEffect, useState } from "react";
import { api } from "../../api/client";

const today = new Date().toISOString().split("T")[0];

const FIELD_STYLE = {
  width: "100%", padding: "8px 10px", borderRadius: 6,
  border: "1px solid #ccd6e0", fontSize: 14, boxSizing: "border-box",
};

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

  const handleSubmit = () => {
    if (!form.doctor_name.trim() || !form.patient_name.trim()) return;
    onStart(form);
  };

  return (
    <div style={{ maxWidth: 560, margin: "0 auto" }}>
      <h3 style={{ color: "#1F3864", marginBottom: 16 }}>Start Prescription Session</h3>

      <Section title="Clinician">
        <Row>
          <Field label="Doctor Name *" value={form.doctor_name} onChange={set("doctor_name")} placeholder="Dr. Surname" />
          <Field label="Clinic / Hospital" value={form.clinic_name} onChange={set("clinic_name")} placeholder="City Clinic" />
        </Row>
      </Section>

      <Section title="Patient">
        {recentPatients.length > 0 && (
          <div>
            <label style={labelStyle}>Returning patient</label>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {recentPatients.map((p) => (
                <button
                  key={p.patient_name}
                  type="button"
                  onClick={() => pickPatient(p.patient_name)}
                  title={`${p.visit_count} visit${p.visit_count > 1 ? "s" : ""} · last ${p.last_visit.slice(0, 10)}`}
                  style={{
                    background: form.patient_name === p.patient_name ? "#2E75B6" : "#fff",
                    color: form.patient_name === p.patient_name ? "#fff" : "#2E75B6",
                    border: "1px solid #2E75B6", borderRadius: 14,
                    padding: "4px 12px", fontSize: 12, cursor: "pointer",
                  }}
                >
                  {p.patient_name} · {p.visit_count}
                </button>
              ))}
            </div>
          </div>
        )}
        <Row>
          <Field label="Patient Name *" value={form.patient_name} onChange={set("patient_name")} placeholder="Full name" />
          <Field label="Age" value={form.patient_age} onChange={set("patient_age")} placeholder="e.g. 34" />
        </Row>
        <Row>
          <div style={{ flex: 1 }}>
            <label style={labelStyle}>Gender</label>
            <select value={form.patient_gender} onChange={set("patient_gender")} style={FIELD_STYLE}>
              <option value="">—</option>
              <option>Male</option><option>Female</option><option>Other</option>
            </select>
          </div>
          <Field label="Date" type="date" value={form.date} onChange={set("date")} />
        </Row>
      </Section>

      <button
        onClick={handleSubmit}
        disabled={loading || !form.doctor_name.trim() || !form.patient_name.trim()}
        style={{
          width: "100%", padding: "12px", background: "#1F3864", color: "#fff",
          border: "none", borderRadius: 8, fontSize: 15, fontWeight: 600,
          cursor: "pointer", marginTop: 8, opacity: loading ? 0.7 : 1,
        }}
      >
        {loading ? "Starting..." : "Start Session →"}
      </button>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ fontSize: 11, fontWeight: 700, color: "#2E75B6",
        textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 }}>
        {title}
      </div>
      <div style={{ background: "#F7FAFD", padding: 14, borderRadius: 8,
        border: "1px solid #dce8f0", display: "flex", flexDirection: "column", gap: 10 }}>
        {children}
      </div>
    </div>
  );
}

function Row({ children }) {
  return <div style={{ display: "flex", gap: 12 }}>{children}</div>;
}

const labelStyle = { fontSize: 12, fontWeight: 600, color: "#444", marginBottom: 4, display: "block" };

function Field({ label, value, onChange, placeholder, type = "text" }) {
  return (
    <div style={{ flex: 1 }}>
      <label style={labelStyle}>{label}</label>
      <input type={type} value={value} onChange={onChange}
        placeholder={placeholder} style={FIELD_STYLE} />
    </div>
  );
}
