import { useState } from "react";
import { api, getBackendOrigin, setBackendOrigin, activeBackendLabel } from "../../api/client";

/**
 * Slim bar under the header showing which backend the app is talking to,
 * with an inline editor to point it at another URL (e.g. an ngrok tunnel).
 * Shared links can preset this via ?api=<url> — see api/client.js.
 */
export function BackendSettings() {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(getBackendOrigin());
  const [status, setStatus] = useState(null); // null | "checking" | "ok" | "fail"

  const save = async () => {
    setStatus("checking");
    try {
      const ok = await api.ping(value || undefined);
      if (!ok) throw new Error();
      setBackendOrigin(value);
      setStatus("ok");
      // reload so every component refetches against the new backend
      setTimeout(() => window.location.reload(), 400);
    } catch {
      setStatus("fail");
    }
  };

  const reset = () => {
    setBackendOrigin("");
    window.location.reload();
  };

  return (
    <div style={{ maxWidth: 720, margin: "10px auto -18px", padding: "0 20px",
      fontSize: 12, color: "#667" }}>
      {!editing ? (
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span>
            Backend: <code style={{ background: "#e4ecf4", padding: "1px 6px",
              borderRadius: 4 }}>{activeBackendLabel()}</code>
          </span>
          <button onClick={() => { setValue(getBackendOrigin()); setEditing(true); setStatus(null); }}
            style={linkBtn}>
            change
          </button>
          {getBackendOrigin() && (
            <button onClick={reset} style={linkBtn}>reset to default</button>
          )}
        </div>
      ) : (
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <input
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="https://xxxx.ngrok-free.app"
            style={{ flex: 1, minWidth: 260, padding: "5px 8px", borderRadius: 5,
              border: "1px solid #ccd6e0", fontSize: 12 }}
          />
          <button onClick={save} disabled={status === "checking"} style={smallBtn("#2E75B6")}>
            {status === "checking" ? "Checking…" : "Save"}
          </button>
          <button onClick={() => setEditing(false)} style={smallBtn("#889")}>Cancel</button>
          {status === "fail" && (
            <span style={{ color: "#b00020" }}>
              ⚠ Could not reach that backend — is the server + tunnel running?
            </span>
          )}
          {status === "ok" && <span style={{ color: "#2E7D32" }}>✓ Connected</span>}
        </div>
      )}
    </div>
  );
}

const linkBtn = {
  background: "none", border: "none", color: "#2E75B6", cursor: "pointer",
  fontSize: 12, padding: 0, textDecoration: "underline",
};

const smallBtn = (bg) => ({
  padding: "5px 12px", background: bg, color: "#fff", border: "none",
  borderRadius: 5, fontSize: 12, fontWeight: 600, cursor: "pointer",
});
