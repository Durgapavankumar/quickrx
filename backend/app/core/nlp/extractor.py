import re
from app.core.nlp.patterns import (
    DOSE_PATTERN, WORD_DOSE_PATTERN, DOSE_UNIT_ALIASES,
    DURATION_PATTERN, FREQUENCY_MAP, ROUTE_MAP,
    INSTRUCTION_PATTERNS, WORD_NUMBERS, DRUG_NOISE_TOKENS,
)
from app.core.nlp.validator import drug_validator
from app.core.config import settings
from app.models.prescription import DrugEntry, ConfidenceLevel


class PrescriptionExtractor:
    """
    Rule-based NLP extraction pipeline.
    Input  : raw ASR transcript string
    Output : DrugEntry (Pydantic model) with all fields + confidence score
    """

    def extract(self, transcript: str) -> DrugEntry:
        text = transcript.strip()
        entry = DrugEntry(raw_transcript=text)

        drug_name, drug_record, drug_score = self._extract_drug(text)
        entry.drug_name = drug_name

        if drug_record:
            entry.generic_name = drug_record.get("generic_name")
            entry.category = drug_record.get("category")

        dose, dose_unit = self._extract_dose(text)
        entry.dose = dose
        entry.dose_unit = dose_unit

        entry.frequency = self._extract_frequency(text)
        duration, duration_unit = self._extract_duration(text)
        entry.duration = duration
        entry.duration_unit = duration_unit

        entry.route = self._extract_route(text)
        entry.instructions = self._extract_instructions(text, entry.frequency)

        entry.confidence = self._compute_confidence(entry, drug_score)
        entry.confidence_level = self._confidence_level(entry.confidence)
        entry.flagged_for_review = entry.confidence < settings.CONFIDENCE_FLAG_THRESHOLD

        return entry

    # ------------------------------------------------------------------
    # Drug name extraction
    # ------------------------------------------------------------------
    def _extract_drug(self, text: str) -> tuple[str | None, dict | None, float]:
        """
        Slide a 1–3 token window over the transcript, fuzzy-match every
        candidate against the formulary, and keep the BEST-scoring match
        (not the first one over threshold — "vitamin" alone must not beat
        "vitamin d3"). Longer candidates win ties so multi-word drug names
        aren't truncated. Dose/frequency tokens end the drug name, so
        windows stop at the first digit.
        """
        tokens = text.split()
        best: tuple[str | None, dict | None, float] = (None, None, 0.0)

        for i in range(len(tokens)):
            first = tokens[i].lower().strip(".,")
            if first in DRUG_NOISE_TOKENS or (first and first[0].isdigit()):
                continue
            for window in (1, 2, 3):
                cand_tokens = tokens[i:i + window]
                if len(cand_tokens) < window:
                    break
                # a leading digit means we've run into the dose — cut the
                # window (but keep alphanumeric name parts like "D3", "B12")
                if window > 1 and cand_tokens[-1][0].isdigit():
                    break
                candidate = " ".join(cand_tokens).strip(".,")
                record, score = drug_validator.lookup(candidate)
                if record and (
                    score > best[2]
                    or (score == best[2] and best[0] and len(candidate) > len(best[0]))
                ):
                    best = (candidate, record, score)

        return best

    # ------------------------------------------------------------------
    # Dose
    # ------------------------------------------------------------------
    def _extract_dose(self, text: str) -> tuple[str | None, str | None]:
        match = DOSE_PATTERN.search(text)
        if match:
            unit = re.sub(r"\s+", " ", match.group(2).lower())
            return match.group(1), DOSE_UNIT_ALIASES.get(unit, unit)

        # word-number tablet doses: "one tablet", "half tablet"
        match = WORD_DOSE_PATTERN.search(text)
        if match:
            number = WORD_NUMBERS.get(match.group(1).lower(), match.group(1))
            unit = match.group(2).lower()
            return number, DOSE_UNIT_ALIASES.get(unit, unit)

        return None, None

    # ------------------------------------------------------------------
    # Frequency
    # ------------------------------------------------------------------
    def _extract_frequency(self, text: str) -> str | None:
        for pattern, label in FREQUENCY_MAP.items():
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                # Handle "every N hours" dynamic label
                if "{0}" in label:
                    n = m.group(1).lower()
                    return label.format(WORD_NUMBERS.get(n, n))
                return label
        return None

    # ------------------------------------------------------------------
    # Duration
    # ------------------------------------------------------------------
    def _extract_duration(self, text: str) -> tuple[str | None, str | None]:
        match = DURATION_PATTERN.search(text)
        if match:
            number = (match.group(1) or match.group(3)).lower()
            number = WORD_NUMBERS.get(number, number)
            unit = (match.group(2) or match.group(4)).lower().rstrip("s") + "s"
            return number, unit
        return None, None

    # ------------------------------------------------------------------
    # Route
    # ------------------------------------------------------------------
    def _extract_route(self, text: str) -> str | None:
        for pattern, label in ROUTE_MAP.items():
            if re.search(pattern, text, re.IGNORECASE):
                return label
        return "oral"   # clinical default — most dictated prescriptions are oral

    # ------------------------------------------------------------------
    # Instructions
    # ------------------------------------------------------------------
    def _extract_instructions(self, text: str, frequency: str | None = None) -> str | None:
        found = []
        for pattern, label in INSTRUCTION_PATTERNS:
            if pattern.search(text) and label not in found:
                # "at bedtime" is already the frequency — don't repeat it
                if label == "at bedtime" and frequency == "at bedtime":
                    continue
                found.append(label)
        return ", ".join(found) if found else None

    # ------------------------------------------------------------------
    # Confidence scoring
    # ------------------------------------------------------------------
    def _compute_confidence(self, entry: DrugEntry, drug_score: float) -> float:
        """
        Weighted confidence score across the 5 core prescription fields.
        Drug match quality contributes the most weight.
        """
        field_weights = {
            "drug":      0.40,
            "dose":      0.25,
            "frequency": 0.20,
            "duration":  0.10,
            "route":     0.05,
        }

        scores = {
            "drug":      drug_score,
            "dose":      1.0 if entry.dose else 0.0,
            "frequency": 1.0 if entry.frequency else 0.0,
            "duration":  1.0 if entry.duration else 0.0,
            "route":     1.0 if entry.route else 0.0,
        }

        total = sum(field_weights[k] * scores[k] for k in field_weights)
        return round(total, 3)

    def _confidence_level(self, score: float) -> ConfidenceLevel:
        if score >= 0.85:
            return ConfidenceLevel.HIGH
        if score >= 0.60:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW


# Singleton extractor
extractor = PrescriptionExtractor()
