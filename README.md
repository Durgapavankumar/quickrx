# QuickRx Voice — MVP

Voice-to-structured-prescription pipeline. Clinician dictates a drug in English → system extracts drug name, dose, frequency, duration → outputs structured JSON + printable PDF.

**Stack:** Python (FastAPI) · Whisper (offline ASR) · RapidFuzz (NLP) · React (Vite) · ReportLab (PDF)  
**Cost:** $0 — fully offline, no API keys required.

---

## Project Structure

```
quickrx/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI entry point
│   │   ├── core/
│   │   │   ├── config.py         # All settings in one place
│   │   │   ├── asr.py            # Whisper ASR engine
│   │   │   └── nlp/
│   │   │       ├── extractor.py  # Rule-based NLP extraction
│   │   │       ├── validator.py  # Fuzzy drug dictionary lookup
│   │   │       └── patterns.py   # Regex patterns (dose/freq/duration)
│   │   ├── models/
│   │   │   └── prescription.py   # Pydantic schema (fixed JSON contract)
│   │   ├── services/
│   │   │   ├── session_store.py  # Store singleton (backend picked by config)
│   │   │   ├── storage/          # Swappable backends: sqlite.py / memory.py
│   │   │   ├── corrections.py    # Clinician edits: merge + re-validate + verify
│   │   │   └── pdf_generator.py  # PDF prescription output
│   │   ├── api/routes/
│   │   │   ├── sessions.py       # Sessions, patient history, drug edit/delete
│   │   │   ├── transcribe.py     # Audio → transcript → DrugEntry
│   │   │   └── export.py         # PDF + JSON export
│   │   └── data/
│   │       ├── drug_dictionary.json  # 200-drug NLEM 2022 formulary
│   │       └── quickrx.db        # SQLite session store (auto-created)
│   ├── tests/
│   │   └── test_extractor.py     # 70-sentence validation suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api/client.js         # All API calls in one place
│   │   ├── hooks/useRecorder.js  # Browser mic abstraction
│   │   └── components/
│   │       ├── PatientForm/      # Session start form + returning-patient picker
│   │       ├── VoiceCapture/     # Mic button + status
│   │       ├── PrescriptionCard/ # Drug display + inline edit/verify/remove
│   │       ├── PatientHistory/   # Previous visits for the current patient
│   │       └── SessionPanel/     # Full session + history + export actions
│   ├── Dockerfile                # Vite build served by nginx (proxies /api/v1)
│   └── nginx.conf
├── docker-compose.yml            # One-command deployment (see below)
└── README.md
```

---

## Setup (macOS)

### 1. Backend

```bash
cd quickrx/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the API server
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 2. Frontend

```bash
cd quickrx/frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Open: http://localhost:5173

---

## Run with Docker (one command)

```bash
docker compose up --build
```

Open **http://localhost:8080**. The Whisper model (~145 MB) downloads on the
first transcription and is cached in a volume; the SQLite database lives in a
volume too, so sessions and patient history survive restarts.

| Container | Port | Notes |
|---|---|---|
| frontend | 8080 | nginx serves the React build and proxies `/api/v1` to the backend |
| backend  | 8000 | FastAPI + Whisper; Swagger docs at http://localhost:8000/docs |

**Always-on hosted deployment** (public HTTPS URL for everyone, no tunnels):
add a domain (or a free `<ip>.sslip.io` address) and run
`docker compose --profile prod up -d --build` — Caddy handles automatic HTTPS.
See **DEPLOYMENT.md, Part 6**.

---

## Running the NLP Validation Suite

```bash
cd quickrx/backend
source venv/bin/activate
python tests/test_extractor.py
```

Target: ≥90% field-level accuracy on all 70 sentences (currently 100%).
The script exits non-zero if any field falls below target, so it can run in CI.

---

## How It Works

```
Browser Mic → Audio Blob → POST /api/v1/transcribe
                              ↓
                         Whisper ASR (local, offline)
                              ↓
                         Raw Transcript
                              ↓
                     NLP Extraction Engine
                    (regex + fuzzy matching)
                              ↓
                     Drug Dictionary Validator
                    (200-drug NLEM 2022 formulary)
                              ↓
              DrugEntry JSON (drug, dose, freq, duration, confidence)
                              ↓
                    Appended to Session
                              ↓
              Export → PDF prescription + structured JSON
```

---

## Output Schema (DrugEntry)

```json
{
  "drug_name": "Paracetamol",
  "generic_name": "Paracetamol",
  "category": "Analgesic/Antipyretic",
  "dose": "500",
  "dose_unit": "mg",
  "frequency": "twice daily",
  "duration": "5",
  "duration_unit": "days",
  "route": "oral",
  "instructions": "after food",
  "confidence": 1.0,
  "confidence_level": "high",
  "flagged_for_review": false,
  "manually_verified": false,
  "raw_transcript": "Paracetamol 500mg twice daily for 5 days after food"
}
```

Flagged (low-confidence) entries can be corrected inline in the UI. A clinician
edit is re-validated against the formulary, marked `manually_verified`, and
unflagged — the original confidence score is preserved for the audit trail.

---

## Patient History

Sessions persist in SQLite (`STORAGE_BACKEND` in `app/core/config.py`; set
`QUICKRX_STORAGE=memory` for the old in-memory behaviour). This enables:

- `GET /api/v1/sessions?patient_name=…` — one patient's past visits
- `GET /api/v1/patients` — all patients with visit counts
- Returning-patient quick pick on the session form (prefills demographics)
- "History" toggle inside a session showing previous prescriptions

---

## Phase 2 Upgrade Path

Each module has a fixed interface — swap independently without touching the rest:

| Module | Phase 1 (current) | Phase 2 (upgrade) |
|--------|-------------------|-------------------|
| ASR | Whisper (local) | Cloud ASR API |
| NLP | Rule-based + RapidFuzz | LLM-based (Claude API) |
| Storage | SQLite (✅ done — swappable via `STORAGE_BACKEND`) | PostgreSQL |
| Formulary | 200-drug NLEM subset | Full NLEM 2022 |
