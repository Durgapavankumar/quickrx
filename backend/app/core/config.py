import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    APP_NAME: str = "QuickRx Voice"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"

    # ASR — Indian English optimized
    ASR_MODEL: str = "ai4bharat/indicwav2vec_v1_hindi"  # Indic model fine-tuned for Indian English
    ASR_DEVICE: str = "cpu"                 # "cpu" or "cuda" if GPU available

    # NLP
    DRUG_DICTIONARY_PATH: Path = BASE_DIR / "data" / "drug_dictionary.json"
    INTERACTION_RULES_PATH: Path = BASE_DIR / "data" / "interactions.json"
    FUZZY_MATCH_THRESHOLD: int = 80         # minimum RapidFuzz score to accept a drug match
    CONFIDENCE_FLAG_THRESHOLD: float = 0.6  # extractions below this get flagged for review

    # Storage — "sqlite" (persistent, enables patient history) or "memory"
    STORAGE_BACKEND: str = os.environ.get("QUICKRX_STORAGE", "sqlite")
    DB_PATH: Path = Path(os.environ.get("QUICKRX_DB_PATH",
                                        BASE_DIR / "data" / "quickrx.db"))

    # Output
    PDF_OUTPUT_DIR: Path = BASE_DIR / "data" / "pdfs"
    TEMP_AUDIO_DIR: Path = BASE_DIR / "data" / "temp_audio"

    # CORS — allowed frontend origins
    # Local dev server + Docker frontend + deployed GitHub Pages URL.
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080",
        "https://durgapavankumar.github.io",
    ]

settings = Settings()

# ensure runtime dirs exist
settings.PDF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
settings.TEMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
