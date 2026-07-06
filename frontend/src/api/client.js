// In local dev, Vite's proxy handles "/api" → localhost:8000 (see vite.config.js).
// In production (GitHub Pages), there is no proxy, so we call the backend directly
// via VITE_API_URL, which must point at wherever the backend is actually running.
const BASE = import.meta.env.VITE_API_URL || "/api/v1";

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
    fetch(`${BASE}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ patient_info: patientInfo }),
    }).then(handleResponse),

  getSession: (sessionId) =>
    fetch(`${BASE}/sessions/${sessionId}`).then(handleResponse),

  deleteSession: (sessionId) =>
    fetch(`${BASE}/sessions/${sessionId}`, { method: "DELETE" }).then(handleResponse),

  // Partial update — send only the changed fields. An empty object just
  // marks the entry as clinician-verified. Backend re-validates the drug
  // name and unflags the entry.
  updateDrug: (sessionId, drugIndex, changedFields = {}) =>
    fetch(`${BASE}/sessions/${sessionId}/drugs/${drugIndex}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(changedFields),
    }).then(handleResponse),

  deleteDrug: (sessionId, drugIndex) =>
    fetch(`${BASE}/sessions/${sessionId}/drugs/${drugIndex}`, {
      method: "DELETE",
    }).then(handleResponse),

  // Patient history
  listPatients: () => fetch(`${BASE}/patients`).then(handleResponse),

  getPatientHistory: (patientName, limit = 20) =>
    fetch(`${BASE}/sessions?patient_name=${encodeURIComponent(patientName)}&limit=${limit}`)
      .then(handleResponse),

  // Transcription
  transcribeAudio: (sessionId, audioBlob) => {
    const form = new FormData();
    form.append("session_id", sessionId);
    form.append("audio", audioBlob, "recording.webm");
    return fetch(`${BASE}/transcribe`, { method: "POST", body: form }).then(handleResponse);
  },

  // Export
  exportPdfUrl: (sessionId) => `${BASE}/sessions/${sessionId}/export/pdf`,
  exportJsonUrl: (sessionId) => `${BASE}/sessions/${sessionId}/export/json`,
};
