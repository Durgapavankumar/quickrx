import { useState } from "react";

const BADGE_CLASS = {
  high: "badge-high",
  medium: "badge-medium",
  low: "badge-low",
};

function Field({ label, value }) {
  if (!value) return null;
  return (
    <div className="rx-field">
      <span className="k">{label}</span>
      <span className="v">{value}</span>
    </div>
  );
}

function EditField({ label, value, onChange, placeholder }) {
  return (
    <div>
      <label>{label}</label>
      <input value={value || ""} placeholder={placeholder}
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
    <div className={`rx-card ${flagged ? "flagged" : ""}`}>
      {/* Header: number + name + badge */}
      <div className="rx-card-top">
        <span className="rx-num">{String(index + 1).padStart(2, "0")}</span>
        <div>
          <span className="rx-name">
            {drug.generic_name || drug.drug_name || "Unknown Drug"}
          </span>
          {drug.category && <span className="rx-category">{drug.category}</span>}
        </div>
        <div className="t-spacer" />
        {drug.manually_verified ? (
          <span className="badge badge-verified">✓ Verified</span>
        ) : (
          <span className={`badge ${BADGE_CLASS[drug.confidence_level] || "badge-low"}`}>
            {flagged ? "⚠ Review" : drug.confidence_level}
            <span className="pct">{Math.round(drug.confidence * 100)}%</span>
          </span>
        )}
      </div>

      {editing ? (
        /* ---- Edit mode ---- */
        <div>
          <div className="rx-edit-grid">
            <EditField label="Drug name" value={draft.drug_name}
              onChange={(v) => setDraft((d) => ({ ...d, drug_name: v }))} />
            <EditField label="Dose" value={draft.dose} placeholder="500"
              onChange={(v) => setDraft((d) => ({ ...d, dose: v }))} />
            <EditField label="Unit" value={draft.dose_unit} placeholder="mg"
              onChange={(v) => setDraft((d) => ({ ...d, dose_unit: v }))} />
          </div>
          <div className="rx-edit-grid">
            <EditField label="Frequency" value={draft.frequency} placeholder="twice daily"
              onChange={(v) => setDraft((d) => ({ ...d, frequency: v }))} />
            <EditField label="Duration" value={draft.duration} placeholder="5"
              onChange={(v) => setDraft((d) => ({ ...d, duration: v }))} />
            <EditField label="Unit" value={draft.duration_unit} placeholder="days"
              onChange={(v) => setDraft((d) => ({ ...d, duration_unit: v }))} />
          </div>
          <div className="rx-edit-grid" style={{ gridTemplateColumns: "1fr 2fr" }}>
            <EditField label="Route" value={draft.route} placeholder="oral"
              onChange={(v) => setDraft((d) => ({ ...d, route: v }))} />
            <EditField label="Instructions" value={draft.instructions} placeholder="after food"
              onChange={(v) => setDraft((d) => ({ ...d, instructions: v }))} />
          </div>
          <div className="rx-actions">
            <button className="btn btn-accent btn-sm" onClick={handleSave}
              disabled={busy || !draft.drug_name.trim()}>
              {busy ? "Saving…" : "✓ Save & verify"}
            </button>
            <button className="btn btn-quiet btn-sm" onClick={() => setEditing(false)} disabled={busy}>
              Cancel
            </button>
          </div>
        </div>
      ) : (
        /* ---- Display mode ---- */
        <>
          <div className="rx-fields">
            <Field label="Dose" value={drug.dose ? `${drug.dose} ${drug.dose_unit || ""}`.trim() : null} />
            <Field label="Frequency" value={drug.frequency} />
            <Field label="Duration"  value={drug.duration ? `${drug.duration} ${drug.duration_unit || ""}`.trim() : null} />
            <Field label="Route"     value={drug.route} />
            <Field label="Instructions" value={drug.instructions} />
          </div>

          {flagged && (
            <div className="rx-review-note">
              ⚠ Low confidence — please verify this entry before finalising the prescription.
            </div>
          )}

          {drug.raw_transcript && (
            <div className="rx-heard">Heard: “{drug.raw_transcript}”</div>
          )}

          {/* Actions */}
          <div className="rx-actions">
            <button className="btn btn-quiet btn-sm" onClick={startEdit} disabled={busy}>
              ✎ Edit
            </button>
            {flagged && (
              <button className="btn btn-accent btn-sm" onClick={handleVerify} disabled={busy}>
                ✓ Mark verified
              </button>
            )}
            <div className="spacer" />
            <button className="btn btn-danger-quiet" onClick={handleDelete} disabled={busy}>
              Remove
            </button>
          </div>
        </>
      )}
    </div>
  );
}
