import { useState } from "react";
import { PatientForm } from "./components/PatientForm/PatientForm";
import { SessionPanel } from "./components/SessionPanel/SessionPanel";
import { BackendSettings } from "./components/BackendSettings/BackendSettings";
import { api } from "./api/client";

export default function App() {
  // The server session is the single source of truth — it carries the drug
  // list, so edits/deletes just replace it with the server's response.
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  const handleStart = async (patientInfo) => {
    setLoading(true);
    setError("");
    try {
      const s = await api.createSession(patientInfo);
      setSession(s);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDrugAdded = () => {
    // Transcribe already appended the drug server-side — refresh the session.
    if (session) {
      api.getSession(session.session_id)
        .then(setSession)
        .catch(() => {});
    }
  };

  const handleNewSession = () => {
    setSession(null);
  };

  return (
    <div style={{ minHeight: "100vh", background: "#EFF4FA", fontFamily: "Arial, sans-serif" }}>
      {/* Top bar */}
      <div style={{ background: "#1F3864", color: "#fff", padding: "14px 28px",
        display: "flex", alignItems: "center", gap: 14 }}>
        <span style={{ fontSize: 22, fontWeight: 800, letterSpacing: 0.5 }}>QuickRx Voice</span>
        <span style={{ fontSize: 12, opacity: 0.6, marginTop: 2 }}>
          MVP · English · 200-drug NLEM 2022 Formulary
        </span>
      </div>

      {/* Which backend this app talks to (editable — supports ngrok links) */}
      <BackendSettings />

      {/* Main content */}
      <div style={{ maxWidth: 720, margin: "32px auto", padding: "0 20px" }}>
        <div style={{ background: "#fff", borderRadius: 12, padding: 28,
          boxShadow: "0 2px 16px rgba(0,0,0,0.08)" }}>

          {error && (
            <div style={{ background: "#FFEBEE", color: "#b00020", padding: "10px 14px",
              borderRadius: 6, marginBottom: 16, fontSize: 13 }}>
              ⚠ {error}
            </div>
          )}

          {!session ? (
            <PatientForm onStart={handleStart} loading={loading} />
          ) : (
            <SessionPanel
              session={session}
              onSessionChange={setSession}
              onDrugAdded={handleDrugAdded}
              onNewSession={handleNewSession}
            />
          )}
        </div>
      </div>
    </div>
  );
}
