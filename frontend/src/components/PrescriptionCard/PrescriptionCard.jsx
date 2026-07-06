const CONFIDENCE_COLORS = {
  high:   { bg: "#E2F0E2", border: "#2E7D32", text: "#2E7D32", label: "HIGH" },
  medium: { bg: "#FFF8E1", border: "#F9A825", text: "#E65100", label: "MEDIUM" },
  low:    { bg: "#FFEBEE", border: "#C62828", text: "#C62828", label: "LOW" },
};

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

export function PrescriptionCard({ drug, index, transcript }) {
  const conf = CONFIDENCE_COLORS[drug.confidence_level] || CONFIDENCE_COLORS.low;

  return (
    <div style={{
      border: `1px solid ${drug.flagged_for_review ? "#C55A11" : conf.border}`,
      borderLeft: `4px solid ${drug.flagged_for_review ? "#C55A11" : conf.border}`,
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

        {/* Confidence badge */}
        <div style={{
          background: conf.bg, border: `1px solid ${conf.border}`,
          color: conf.text, padding: "2px 9px", borderRadius: 12,
          fontSize: 10, fontWeight: 700,
        }}>
          {drug.flagged_for_review ? "⚠ REVIEW" : `✓ ${conf.label}`}
          <span style={{ marginLeft: 4, opacity: 0.7 }}>
            {Math.round(drug.confidence * 100)}%
          </span>
        </div>
      </div>

      {/* Fields */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 20px" }}>
        <Field label="Dose" value={drug.dose ? `${drug.dose} ${drug.dose_unit || ""}`.trim() : null} />
        <Field label="Frequency" value={drug.frequency} />
        <Field label="Duration"  value={drug.duration ? `${drug.duration} ${drug.duration_unit || ""}`.trim() : null} />
        <Field label="Route"     value={drug.route} />
        <Field label="Instructions" value={drug.instructions} />
      </div>

      {/* Flagged warning */}
      {drug.flagged_for_review && (
        <div style={{ marginTop: 8, padding: "6px 10px", background: "#FBE5D6",
          borderRadius: 6, fontSize: 12, color: "#C55A11", fontWeight: 500 }}>
          ⚠ Low confidence — please verify this entry before finalising the prescription.
        </div>
      )}

      {/* Transcript */}
      {transcript && (
        <div style={{ marginTop: 8, fontSize: 11, color: "#888" }}>
          <em>Heard: "{transcript}"</em>
        </div>
      )}
    </div>
  );
}
