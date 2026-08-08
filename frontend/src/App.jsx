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
    <div style={{ minHeight: "100vh" }}>
      {/* Top bar */}
      <header className="topbar">
        <div className="topbar-inner">
          <div className="wordmark">
            <span>Quick<span className="rx">Rx</span></span>
            <span className="wordmark-sub">Voice</span>
          </div>
          <div className="topbar-spacer" />
          <BackendSettings />
        </div>
      </header>

      <main className="shell">
        {error && (
          <div className="alert-error" style={{ marginTop: 24 }}>⚠ {error}</div>
        )}

        {!session ? (
          <>
            {/* Landing hero */}
            <section className="hero">
              <div className="hero-eyebrow">
                <span>●</span> AI prescription assistant
              </div>
              <h1>
                Speak the prescription.<br />
                <em>It writes itself.</em>
              </h1>
              <p className="hero-sub">
                Dictate naturally — QuickRx transcribes your voice, extracts the drug,
                dose, frequency and duration, validates it against the NLEM formulary,
                and hands you a clean, exportable script.
              </p>
              <div className="hero-stats">
                <span className="stat-chip"><span className="dot" />200-drug NLEM 2022 formulary</span>
                <span className="stat-chip"><span className="dot" />Whisper speech recognition</span>
                <span className="stat-chip"><span className="dot" />Confidence-scored extraction</span>
                <span className="stat-chip"><span className="dot" />PDF &amp; JSON export</span>
              </div>
            </section>

            {/* Start-session form */}
            <div className="shell-narrow">
              <div className="card card-pad">
                <PatientForm onStart={handleStart} loading={loading} />
              </div>
            </div>
          </>
        ) : (
          <div className="shell-narrow" style={{ paddingTop: 32 }}>
            <SessionPanel
              session={session}
              onSessionChange={setSession}
              onDrugAdded={handleDrugAdded}
              onNewSession={handleNewSession}
            />
          </div>
        )}

        <footer className="site-footer">
          QuickRx Voice · MVP · English · For clinical evaluation only — verify every entry before prescribing.
        </footer>
      </main>
    </div>
  );
}
