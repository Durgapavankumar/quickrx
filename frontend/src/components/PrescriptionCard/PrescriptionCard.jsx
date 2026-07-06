import { useState } from "react";

const CONFIDENCE_COLORS = {
  high:   { bg: "#E2F0E2", border: "#2E7D32", text: "#2E7D32", label: "HIGH" },
  medium: { bg: "#FFF8E1", border: "#F9A825", text: "#E65100", label: "MEDIUM" },
  low:    { bg: "#FFEBEE", border: "#C62828", text: "#C62828", label: "LOW" },
};

const VERIFIED = { bg: "#E3F2FD", border: "#1565C0", text: "#1565C0", label: "VERIFIED" };

function Field({ label, value }) {
  if (!value) return null;
  return (
    <div style={{ display: "flex", gap: 6, fontSize: 13, marginBottom: 3 }}>
      <span style={{ color: "#2E75B6", fontWeight: 600, minWidth: 90, fontSize: 11 }}>
        {label}
      </span>
      <span style={{ color: "#222" }}>{value}</span>
    </div>
  );
}

const inputStyle = {
  width: "100%", padding: "5px 8px", borderRadius: 5, boxSizing: "border-box",
  border: "1px solid #ccd6e0", fontSize: 13,
};

function EditField({ label, value, onChange, placeholder }) {
  return (
    <div>
      <label style={{ fontSize: 10, fontWeight: 700, color: "#2E75B6",
        textTransform: "uppercase", display: "block", marginBottom: 2 }}>
        {label}
      </label>
      <input style={inputStyle} value={value || ""} placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)} />
    </div>
  );
}

const EDITABLE_FIELDS = [
  "drug_name", "dose", "dose_unit", "frequency",
  "duration", "duration_unit", "route", "instructions",
];

export function PrescriptionCard({ drug, index, onSave, onVerify, onDelete }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft]     = useState({});
  const [busy, setBusy]       = useState(false);

  const conf = drug.manually_verified
    ? VERIFIED
    : (CONFIDENCE_COLORS[drug.confidence_level] || CONFIDENCE_COLORS.low);
  const flagged = drug.flagged_for_review && !drug.manually_verified;

  const startEdit = () => {
    const d = {};
    EDITABLE_FIELDS.forEach((f) => { d[f] = drug[f] || ""; });
    setDraft(d);
    setEditing(true);
  };

  const handleSave = async () => {
    // send only fields that actually changed
    const changed = {};
    EDITABLE_FIELDS.forEach((f) => {
      if (draft[f] !== (drug[f] || "")) changed[f] = draft[f];
    });
    setBusy(true);
    try {
      await onSave(index, changed);   // empty object still marks as verified
      setEditing(false);
    } catch {
      /* error shown by SessionPanel — stay in edit mode */
    } finally {
      setBusy(false);
    }
  };

  const handleVerify = async () => {
    setBusy(true);
    try { await onVerify(index); } catch {} finally { setBusy(false); }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Remove #${index + 1} ${drug.generic_name || drug.drug_name || "this entry"} from the prescription?`)) return;
    setBusy(true);
    try { await onDelete(index); } catch {} finally { setBusy(false); }
  };

  return (
    <div style={{
      border: `1px solid ${flagged ? "#C55A11" : conf.border}`,
      borderLeft: `4px solid ${flagged ? "#C55A11" : conf.border}`,
      borderRadius: 8, padding: "12px 16px", background: conf.bg,
      position: "relative", marginBottom: 10,
    }}>
      {/* Drug number + name */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
        <div>
          <span style={{ fontSize: 11, fontWeight: 700, color: "#999" }}>#{index + 1}</span>
          <span style={{ marginLeft: 8, fontSize: 16, fontWeight: 700, color: "#1F3864" }}>
            {drug.generic_name || drug.drug_name || "Unknown Drug"}
          </span>
          {drug.category && (
            <span style={{ marginLeft: 8, fontSize: 10, color: "#666",
              background: "#e0e8f0", padding: "2px 7px", borderRadius: 12 }}>
              {drug.category}
            </span>
          )}
        </div>

        {/* Confidence / verified badge */}
        <div style={{
          background: conf.bg, border: `1px solid ${conf.border}`,
          color: conf.text, padding: "2px 9px", borderRadius: 12,
          fontSize: 10, fontWeight: 700, whiteSpace: "nowrap",
        }}>
          {drug.manually_verified ? "✓ VERIFIED"
            : flagged ? "⚠ REVIEW" : `✓ ${conf.label}`}
          {!drug.manually_verified && (
            <span style={{ marginLeft: 4, opacity: 0.7 }}>
              {Math.round(drug.confidence * 100)}%
            </span>
          )}
        </div>
      </div>

      {editing ? (
        /* ---- Edit mode ---- */
        <div>
          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr", gap: 8, marginBottom: 8 }}>
            <EditField label="Drug name" value={draft.drug_name}
              onChange={(v) => setDraft((d) => ({ ...d, drug_name: v }))} />
            <EditField label="Dose" value={draft.dose} placeholder="500"
              onChange={(v) => setDraft((d) => ({ ...d, dose: v }))} />
            <EditField label="Unit" value={draft.dose_unit} placeholder="mg"
              onChange={(v) => setDraft((d) => ({ ...d, dose_unit: v }))} />
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr", gap: 8, marginBottom: 8 }}>
            <EditField label="Frequency" value={draft.frequency} placeholder="twice daily"
              onChange={(v) => setDraft((d) => ({ ...d, frequency: v }))} />
            <EditField label="Duration" value={draft.duration} placeholder="5"
              onChange={(v) => setDraft((d) => ({ ...d, duration: v }))} />
            <EditField label="Unit" value={draft.duration_unit} placeholder="days"
              onChange={(v) => setDraft((d) => ({ ...d, duration_unit: v }))} />
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 8, marginBottom: 10 }}>
            <EditField label="Route" value={draft.route} placeholder="oral"
              onChange={(v) => setDraft((d) => ({ ...d, route: v }))} />
            <EditField label="Instructions" value={draft.instructions} placeholder="after food"
              onChange={(v) => setDraft((d) => ({ ...d, instructions: v }))} />
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={handleSave} disabled={busy || !draft.drug_name.trim()}
              style={smallBtn("#2E7D32")}>
              {busy ? "Saving..." : "✓ Save & Verify"}
            </button>
            <button onClick={() => setEditing(false)} disabled={busy}
              style={smallBtn("#595959")}>
              Cancel
            </button>
          </div>
        </div>
      ) : (
        /* ---- Display mode ---- */
        <>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 20px" }}>
            <Field label="Dose" value={drug.dose ? `${drug.dose} ${drug.dose_unit || ""}`.trim() : null} />
            <Field label="Frequency" value={drug.frequency} />
            <Field label="Duration"  value={drug.duration ? `${drug.duration} ${drug.duration_unit || ""}`.trim() : null} />
            <Field label="Route"     value={drug.route} />
            <Field label="Instructions" value={drug.instructions} />
          </div>

          {flagged && (
            <div style={{ marginTop: 8, padding: "6px 10px", background: "#FBE5D6",
              borderRadius: 6, fontSize: 12, color: "#C55A11", fontWeight: 500 }}>
              ⚠ Low confidence — please verify this entry before finalising the prescription.
            </div>
          )}

          {drug.raw_transcript && (
            <div style={{ marginTop: 8, fontSize: 11, color: "#888" }}>
              <em>Heard: "{drug.raw_transcript}"</em>
            </div>
          )}

          {/* Actions */}
          <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
            <button onClick={startEdit} disabled={busy} style={smallBtn("#2E75B6")}>
              ✎ Edit
            </button>
            {flagged && (
              <button onClick={handleVerify} disabled={busy} style={smallBtn("#2E7D32")}>
                ✓ Mark Verified
              </button>
            )}
            <button onClick={handleDelete} disabled={busy}
              style={{ ...smallBtn("transparent"), color: "#C62828",
                border: "1px solid #C62828", marginLeft: "auto" }}>
              🗑 Remove
            </button>
          </div>
        </>
      )}
    </div>
  );
}

const smallBtn = (bg) => ({
  padding: "6px 14px", background: bg, color: "#fff", border: "none",
  borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: "pointer",
});
