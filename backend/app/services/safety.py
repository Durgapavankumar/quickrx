"""
Prescription safety checks — decision support, not a substitute for judgment.

Two independent checks:
  1. Dose sanity  — is the dictated strength wildly outside the formulary's
                    common strengths for that drug? (catches ASR errors like
                    "5 mg" heard for "500 mg")
  2. Interactions — clinically significant pairs within one prescription,
                    from data/interactions.json, plus duplicate-drug detection.
"""
import json
import re

from app.core.config import settings
from app.models.prescription import DrugEntry, InteractionAlert, PrescriptionSession

# ---------------------------------------------------------------------------
# Dose sanity
# ---------------------------------------------------------------------------

# convert weight units to mg for comparison
_TO_MG = {"mg": 1.0, "g": 1000.0, "mcg": 0.001}

_DOSE_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*(mg|mcg|g)\b", re.IGNORECASE)


def _parse_mg(value: str, unit: str) -> float | None:
    try:
        return float(value) * _TO_MG[unit.lower()]
    except (KeyError, ValueError, TypeError, AttributeError):
        return None


def _common_doses_mg(record: dict) -> list[float]:
    """Parse the formulary's common_doses ("500 mg", "0.5 mg", "20 mg dispersible
    tablet") into mg values. Combination strengths ("100/10 mg") and non-weight
    forms ("1% cream", "60000 IU") are skipped — no basis for comparison."""
    out = []
    for s in record.get("common_doses", []):
        if "/" in s:
            continue
        m = _DOSE_RE.match(s.strip())
        if m:
            mg = _parse_mg(m.group(1), m.group(2))
            if mg is not None:
                out.append(mg)
    return out


def check_dose(record: dict | None, dose: str | None, dose_unit: str | None) -> str | None:
    """
    Returns a warning string when the dictated dose is far outside the
    formulary's usual strengths (>2× the highest or <¼ of the lowest),
    else None. Deliberately loose — it exists to catch transcription
    errors, not to police therapeutic choices.
    """
    if not record or not dose or not dose_unit:
        return None

    dictated_mg = _parse_mg(dose, dose_unit)
    if dictated_mg is None:
        return None

    usual = _common_doses_mg(record)
    if not usual:
        return None

    lo, hi = min(usual), max(usual)
    strengths = " / ".join(record["common_doses"])

    if dictated_mg > hi * 2:
        return (f"Dose looks unusually HIGH — usual strengths for "
                f"{record['generic_name']} are {strengths}. Please confirm.")
    if dictated_mg < lo * 0.25:
        return (f"Dose looks unusually LOW — usual strengths for "
                f"{record['generic_name']} are {strengths}. Please confirm.")
    return None


# ---------------------------------------------------------------------------
# Interactions
# ---------------------------------------------------------------------------

def _load_rules() -> dict[frozenset, tuple[str, str]]:
    """Expand groups/rules from interactions.json into a pair-lookup map:
    frozenset({name_a, name_b}) → (severity, note). First rule wins on
    duplicates, so order in the JSON is priority order."""
    with open(settings.INTERACTION_RULES_PATH) as f:
        raw = json.load(f)

    groups = {k: [n.lower() for n in v] for k, v in raw["groups"].items()}

    def expand(side: list[str]) -> list[str]:
        names = []
        for item in side:
            if item.startswith("@"):
                names.extend(groups[item[1:]])
            else:
                names.append(item.lower())
        return names

    pair_map: dict[frozenset, tuple[str, str]] = {}
    for rule in raw["rules"]:
        for a in expand(rule["a"]):
            for b in expand(rule["b"]):
                if a == b:
                    continue        # same drug twice is the duplicate check's job
                key = frozenset((a, b))
                if key not in pair_map:
                    pair_map[key] = (rule["severity"], rule["note"])
    return pair_map


_PAIR_MAP = _load_rules()


def check_interactions(drugs: list[DrugEntry]) -> list[InteractionAlert]:
    """All alerts for the current drug list: known interacting pairs plus
    the same generic appearing twice. Sorted major-first."""
    named = [(d.generic_name or d.drug_name or "").strip() for d in drugs]
    alerts: list[InteractionAlert] = []
    seen_pairs: set[frozenset] = set()

    for i in range(len(named)):
        for j in range(i + 1, len(named)):
            a, b = named[i], named[j]
            if not a or not b:
                continue
            key = frozenset((a.lower(), b.lower()))
            if key in seen_pairs:
                continue

            if a.lower() == b.lower():
                seen_pairs.add(key)
                alerts.append(InteractionAlert(
                    drug_a=a, drug_b=b, severity="major",
                    note="Duplicate entry — the same drug appears twice in this prescription.",
                ))
                continue

            hit = _PAIR_MAP.get(key)
            if hit:
                seen_pairs.add(key)
                alerts.append(InteractionAlert(
                    drug_a=a, drug_b=b, severity=hit[0], note=hit[1],
                ))

    alerts.sort(key=lambda x: 0 if x.severity == "major" else 1)
    return alerts


def with_safety(session: PrescriptionSession) -> PrescriptionSession:
    """Attach freshly computed interaction alerts to a session (in place)."""
    session.interactions = check_interactions(session.drugs)
    return session
