import json
from rapidfuzz import process, fuzz
from app.core.config import settings


class DrugValidator:
    """
    Loads the 200-drug formulary and exposes fuzzy lookup.
    Returns matched drug metadata + a match score used in confidence calculation.
    """

    def __init__(self):
        with open(settings.DRUG_DICTIONARY_PATH) as f:
            raw = json.load(f)

        self._drugs: list[dict] = raw["drugs"]

        # Build a flat lookup map: every name/alias → drug record
        self._name_map: dict[str, dict] = {}
        for drug in self._drugs:
            key = drug["generic_name"].lower()
            self._name_map[key] = drug
            for alias in drug.get("aliases", []):
                self._name_map[alias.lower()] = drug

        self._all_names = list(self._name_map.keys())

    def lookup(self, raw_name: str) -> tuple[dict | None, float]:
        """
        Fuzzy-match raw_name against all known drug names + aliases.
        Returns (drug_record, score_0_to_1) — (None, 0.0) if below threshold.
        """
        if not raw_name or not raw_name.strip():
            return None, 0.0

        result = process.extractOne(
            raw_name.lower(),
            self._all_names,
            scorer=fuzz.token_sort_ratio,
        )

        if result is None:
            return None, 0.0

        matched_name, score, _ = result
        normalized_score = score / 100.0

        if score < settings.FUZZY_MATCH_THRESHOLD:
            return None, normalized_score

        return self._name_map[matched_name], normalized_score

    def all_drug_names(self) -> list[str]:
        return self._all_names


# Singleton — loaded once at startup
drug_validator = DrugValidator()
