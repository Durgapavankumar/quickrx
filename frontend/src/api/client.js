// Backend URL resolution — in priority order:
//   1. ?api=<url> in the page URL (captured + persisted on load). This lets you
//      share a ready-to-use link, e.g. .../quickrx/?api=https://xxxx.ngrok-free.app
//   2. localStorage override set via the "Backend" settings panel.
//   3. Build-time VITE_API_URL (Docker/same-origin default = "/api/v1").
//
// In local dev, Vite's proxy handles "/api" → localhost:8000 (see vite.config.js).
// On GitHub Pages there is no proxy, so the backend must be reachable directly —
// point it at your ngrok HTTPS URL (see below).
const STORAGE_KEY = "quickrx_backend";
const BUILD_DEFAULT = import.meta.env.VITE_API_URL || "/api/v1";

// Strip trailing slashes and a trailing "/api/v1" so we always store a bare origin.
function normalizeOrigin(value) {
  return (value || "").trim().replace(/\/+$/, "").replace(/\/api\/v1$/, "");
}

// Capture ?api= once on load, persist it, then remove it from the address bar
// so a stale value isn't copied around.
(function captureApiFromQuery() {
  try {
    const params = new URLSearchParams(window.location.search);
    const q = params.get("api");
    if (q) {
      setBackendOrigin(q);
      params.delete("api");
      const clean =
        window.location.pathname +
        (params.toString() ? `?${params}` : "") +
        window.location.hash;
      window.history.replaceState({}, "", clean);
    }
  } catch {
    /* non-browser env — ignore */
  }
})();

export function getBackendOrigin() {
  try {
    return localStorage.getItem(STORAGE_KEY) || "";
  } catch {
    return "";
  }
}

export function setBackendOrigin(value) {
  try {
    const origin = normalizeOrigin(value);
    if (origin) localStorage.setItem(STORAGE_KEY, origin);
    else localStorage.removeItem(STORAGE_KEY);
  } catch {
    /* ignore */
  }
}

// Where the app is currently talking to (for display).
export function activeBackendLabel() {
  const o = getBackendOrigin();
  return o || BUILD_DEFAULT;
}

function apiBase() {
  const o = getBackendOrigin();
  return o ? `${o}/api/v1` : BUILD_DEFAULT;
}

function backendRoot() {
  const o = getBackendOrigin();
  return o || BUILD_DEFAULT.replace(/\/api\/v1$/, "");
}

// Sent on every request. "ngrok-skip-browser-warning" makes ngrok's free tier
// proxy the request instead of returning its HTML interstitial. Harmless on any
// other backend.
const EXTRA_HEADERS = { "ngrok-skip-browser-warning": "true" };

async function handleResponse(res) {
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

export const api = {
  // Sessions
  createSession: (patientInfo) =>
    fetch(`${apiBase()}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...EXTRA_HEADERS },
      body: JSON.stringify({ patient_info: patientInfo }),
    }).then(handleResponse),

  getSession: (sessionId) =>
    fetch(`${apiBase()}/sessions/${sessionId}`, { headers: EXTRA_HEADERS }).then(handleResponse),

  deleteSession: (sessionId) =>
    fetch(`${apiBase()}/sessions/${sessionId}`, { method: "DELETE", headers: EXTRA_HEADERS }).then(handleResponse),

  // Partial update — send only the changed fields. An empty object just
  // marks the entry as clinician-verified. Backend re-validates the drug
  // name and unflags the entry.
  updateDrug: (sessionId, drugIndex, changedFields = {}) =>
    fetch(`${apiBase()}/sessions/${sessionId}/drugs/${drugIndex}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", ...EXTRA_HEADERS },
      body: JSON.stringify(changedFields),
    }).then(handleResponse),

  deleteDrug: (sessionId, drugIndex) =>
    fetch(`${apiBase()}/sessions/${sessionId}/drugs/${drugIndex}`, {
      method: "DELETE",
      headers: EXTRA_HEADERS,
    }).then(handleResponse),

  // Patient history
  listPatients: () => fetch(`${apiBase()}/patients`, { headers: EXTRA_HEADERS }).then(handleResponse),

  getPatientHistory: (patientName, limit = 20) =>
    fetch(`${apiBase()}/sessions?patient_name=${encodeURIComponent(patientName)}&limit=${limit}`, {
      headers: EXTRA_HEADERS,
    }).then(handleResponse),

  // Transcription (multipart — let the browser set Content-Type + boundary)
  transcribeAudio: (sessionId, audioBlob) => {
    const form = new FormData();
    form.append("session_id", sessionId);
    form.append("audio", audioBlob, "recording.webm");
    return fetch(`${apiBase()}/transcribe`, {
      method: "POST",
      headers: EXTRA_HEADERS,
      body: form,
    }).then(handleResponse);
  },

  // Connectivity check for the Backend settings panel. Returns true if the
  // given origin's /health responds ok.
  ping: async (origin) => {
    const root = normalizeOrigin(origin) || backendRoot();
    const res = await fetch(`${root}/health`, { headers: EXTRA_HEADERS });
    return res.ok;
  },

  // Export — fetched as blobs so the ngrok header applies (a plain link/tab
  // navigation would hit ngrok's interstitial instead of the file).
  exportPdfBlob: (sessionId) =>
    fetch(`${apiBase()}/sessions/${sessionId}/export/pdf`, { headers: EXTRA_HEADERS }).then((r) => r.blob()),

  exportJsonBlob: (sessionId) =>
    fetch(`${apiBase()}/sessions/${sessionId}/export/json`, { headers: EXTRA_HEADERS }).then((r) => r.blob()),
};
