import { useState } from "react";
import { api, getBackendOrigin, setBackendOrigin, activeBackendLabel } from "../../api/client";

/**
 * Compact backend indicator in the top bar, with an inline editor to point
 * the app at another URL (e.g. an ngrok tunnel). Shared links can preset
 * this via ?api=<url> — see api/client.js.
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

  if (!editing) {
    return (
      <div className="backend-bar">
        <span className="backend-dot" aria-hidden="true" />
        <span>Backend</span>
        <code>{activeBackendLabel()}</code>
        <button className="link-btn" style={{ fontSize: 12.5 }}
          onClick={() => { setValue(getBackendOrigin()); setEditing(true); setStatus(null); }}>
          change
        </button>
        {getBackendOrigin() && (
          <button className="link-btn" style={{ fontSize: 12.5 }} onClick={reset}>
            reset to default
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="backend-bar">
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="https://xxxx.ngrok-free.app"
      />
      <button className="btn btn-accent btn-sm" onClick={save} disabled={status === "checking"}>
        {status === "checking" ? "Checking…" : "Save"}
      </button>
      <button className="btn btn-quiet btn-sm" onClick={() => setEditing(false)}>Cancel</button>
      {status === "fail" && (
        <span style={{ color: "var(--danger)", fontWeight: 500 }}>
          ⚠ Could not reach that backend — is the server + tunnel running?
        </span>
      )}
      {status === "ok" && <span style={{ color: "var(--accent-deep)", fontWeight: 600 }}>✓ Connected</span>}
    </div>
  );
}
