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
│   │   │   ├── session_store.py  # In-memory session management
│   │   │   └── pdf_generator.py  # PDF prescription output
│   │   ├── api/routes/
│   │   │   ├── sessions.py       # POST/GET/DELETE sessions
│   │   │   ├── transcribe.py     # Audio → transcript → DrugEntry
│   │   │   └── export.py         # PDF + JSON export
│   │   └── data/
│   │       └── drug_dictionary.json  # 200-drug NLEM 2022 formulary
│   ├── tests/
│   │   └── test_extractor.py     # 50-sentence validation suite
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── api/client.js         # All API calls in one place
│       ├── hooks/useRecorder.js  # Browser mic abstraction
│       └── components/
│           ├── PatientForm/      # Session start form
│           ├── VoiceCapture/     # Mic button + status
│           ├── PrescriptionCard/ # Drug display with confidence badge
│           └── SessionPanel/     # Full session + export actions
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

## Running the NLP Validation Suite

```bash
cd quickrx/backend
source venv/bin/activate
python tests/test_extractor.py
```

Target: ≥90% field-level accuracy on all 50 sentences.

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
  "raw_transcript": "Paracetamol 500mg twice daily for 5 days after food"
}
```

---

## Phase 2 Upgrade Path

Each module has a fixed interface — swap independently without touching the rest:

| Module | Phase 1 (current) | Phase 2 (upgrade) |
|--------|-------------------|-------------------|
| ASR | Whisper (local) | Cloud ASR API |
| NLP | Rule-based + RapidFuzz | LLM-based (Claude API) |
| Storage | In-memory | SQLite / PostgreSQL |
| Formulary | 200-drug NLEM subset | Full NLEM 2022 |
