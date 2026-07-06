from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    APP_NAME: str = "QuickRx Voice"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"

    # ASR
    WHISPER_MODEL: str = "base.en"          # free, ~145MB, English-only, fast on CPU
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"      # lowest memory footprint on CPU

    # NLP
    DRUG_DICTIONARY_PATH: Path = BASE_DIR / "data" / "drug_dictionary.json"
    FUZZY_MATCH_THRESHOLD: int = 80         # minimum RapidFuzz score to accept a drug match
    CONFIDENCE_FLAG_THRESHOLD: float = 0.6  # extractions below this get flagged for review

    # Output
    PDF_OUTPUT_DIR: Path = BASE_DIR / "data" / "pdfs"
    TEMP_AUDIO_DIR: Path = BASE_DIR / "data" / "temp_audio"

    # CORS — allowed frontend origins
    # Local dev server + deployed GitHub Pages URL (update the username below
    # once you know your GitHub username / repo name).
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://YOUR-GITHUB-USERNAME.github.io",
    ]

settings = Settings()

# ensure runtime dirs exist
settings.PDF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
settings.TEMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
