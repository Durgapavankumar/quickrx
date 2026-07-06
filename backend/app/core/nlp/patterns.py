import re

# ---------------------------------------------------------------------------
# WORD NUMBERS — spoken numbers that ASR often emits as words
# Shared by dose / frequency / duration extraction.
# ---------------------------------------------------------------------------
WORD_NUMBERS = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    "eleven": "11", "twelve": "12",
    "half": "0.5",
    "a": "1", "an": "1",          # "for a week" → 1 week
}

_WORD_NUM_ALT = "|".join(k for k in WORD_NUMBERS if k not in ("a", "an", "half"))

# ---------------------------------------------------------------------------
# DOSE  — captures numeric value + unit
# Examples: "500mg", "500 mg", "5 ml", "10 mcg", "2.5 mg", "500 milligrams"
# ---------------------------------------------------------------------------
DOSE_PATTERN = re.compile(
    r"\b(\d+(?:\.\d+)?)\s*"
    r"(mg|mcg|ug|ml|g|iu|units?|drops?|puffs?|sachets?"
    r"|milligrams?|micrograms?|grams?|millilitres?|milliliters?"
    r"|international\s+units?|tablets?|tabs?|capsules?|caps?)\b",
    re.IGNORECASE
)

# Word-number doses for tablet-type units: "one tablet", "half tablet"
WORD_DOSE_PATTERN = re.compile(
    rf"\b({_WORD_NUM_ALT}|half)\s+(tablets?|tabs?|capsules?|caps?|sachets?|puffs?|drops?)\b",
    re.IGNORECASE
)

# Normalise spelled-out / variant units to canonical short forms
DOSE_UNIT_ALIASES = {
    "milligram": "mg", "milligrams": "mg",
    "microgram": "mcg", "micrograms": "mcg", "ug": "mcg",
    "gram": "g", "grams": "g",
    "millilitre": "ml", "millilitres": "ml",
    "milliliter": "ml", "milliliters": "ml",
    "international unit": "iu", "international units": "iu",
    "tab": "tablet", "tabs": "tablet", "tablets": "tablet",
    "cap": "capsule", "caps": "capsule", "capsules": "capsule",
}

# ---------------------------------------------------------------------------
# FREQUENCY — maps spoken variants to canonical labels
# NOTE: order matters — the extractor returns the FIRST matching pattern, so
# more specific patterns (e.g. Indian 1-0-1 notation) must come before looser
# ones (e.g. 1-1), and daily-count phrases before bedtime/night fallbacks.
# ---------------------------------------------------------------------------
FREQUENCY_MAP = {
    # Indian morning-noon-night shorthand (must precede the 2-part patterns)
    r"\b1\s*-\s*1\s*-\s*1\b":              "three times daily",
    r"\b1\s*-\s*0\s*-\s*1\b":              "twice daily",
    r"\b1\s*-\s*1\s*-\s*0\b":              "twice daily",
    r"\b0\s*-\s*1\s*-\s*1\b":              "twice daily",
    r"\b1\s*-\s*0\s*-\s*0\b":              "once daily",
    r"\b0\s*-\s*0\s*-\s*1\b":              "at bedtime",

    # Once daily
    r"\bonce\s+(?:a\s+)?(?:daily|day)\b":  "once daily",
    r"\bOD\b":                              "once daily",
    r"\b1\s*[\-x]\s*1\b":                  "once daily",

    # Twice daily
    r"\btwice\s+(?:a\s+)?(?:daily|day)\b": "twice daily",
    r"\b(?:two|2)\s+times\s+(?:a\s+)?(?:daily|day)\b": "twice daily",
    r"\bBD\b":                              "twice daily",
    r"\bBID\b":                             "twice daily",
    r"\b2\s*[\-x]\s*1\b":                  "twice daily",

    # Three times daily
    r"\b(?:three|3)\s+times\s+(?:a\s+)?(?:daily|day)\b": "three times daily",
    r"\bthrice\s+(?:a\s+)?(?:daily|day)\b": "three times daily",
    r"\bTDS\b":                             "three times daily",
    r"\bTID\b":                             "three times daily",
    r"\b3\s*[\-x]\s*1\b":                  "three times daily",

    # Four times daily
    r"\b(?:four|4)\s+times\s+(?:a\s+)?(?:daily|day)\b": "four times daily",
    r"\bQID\b":                             "four times daily",
    r"\bQDS\b":                             "four times daily",
    r"\b4\s*[\-x]\s*1\b":                  "four times daily",

    # Five times daily (e.g. acyclovir)
    r"\b(?:five|5)\s+times\s+(?:a\s+)?(?:daily|day)\b": "five times daily",

    # Every N hours — dynamic label, digit or word number
    rf"\bevery\s+(\d+|{_WORD_NUM_ALT})\s+hours?\b": "every {0} hours",
    r"\bq\s*(\d+)\s*h\b":                  "every {0} hours",

    # Weekly
    r"\bonce\s+(?:a\s+|every\s+)?week(?:ly)?\b": "once weekly",
    r"\btwice\s+(?:a\s+)?week(?:ly)?\b":   "twice weekly",
    r"\bweekly\b":                          "once weekly",

    # Alternate days
    r"\b(?:on\s+)?alternate\s+days?\b":    "alternate days",
    r"\bevery\s+other\s+day\b":            "alternate days",

    # Single / stat dose
    r"\bsingle\s+dose\b":                  "single dose",
    r"\bstat\b":                            "single dose",
    r"\bone\s+dose\s+only\b":              "single dose",

    # SOS / as needed
    r"\bSOS\b":                             "as needed",
    r"\bas\s+needed\b":                     "as needed",
    r"\bwhen\s+(?:needed|required)\b":      "as needed",
    r"\bif\s+(?:needed|required)\b":        "as needed",
    r"\bPRN\b":                             "as needed",

    # Bedtime (loose fallbacks — keep last so explicit daily counts win)
    r"\bat\s+bedtime\b":                    "at bedtime",
    r"\bHS\b":                              "at bedtime",
    r"\bbefore\s+bed\b":                    "at bedtime",
    r"\bat\s+night\b":                      "at bedtime",
    r"\bnight\b":                           "at bedtime",
}

# ---------------------------------------------------------------------------
# DURATION — captures number (digit or word) + unit
# Examples: "5 days", "for five days", "for a week", "1 month"
# Word numbers (incl. "a"/"an") require the "for" prefix so that frequency
# phrases like "twice a day" are never captured as a duration.
# ---------------------------------------------------------------------------
DURATION_PATTERN = re.compile(
    rf"\bfor\s+(\d+|{_WORD_NUM_ALT}|a|an)\s+(days?|weeks?|months?)\b"
    r"|\b(\d+)\s+(days?|weeks?|months?)\b",
    re.IGNORECASE
)

# ---------------------------------------------------------------------------
# ROUTE — canonical route terms
# ---------------------------------------------------------------------------
ROUTE_MAP = {
    r"\boral(?:ly)?\b":         "oral",
    r"\bby\s+mouth\b":          "oral",
    r"\bPO\b":                  "oral",
    r"\btopical(?:ly)?\b":      "topical",
    r"\bapply\s+locally\b":     "topical",
    r"\binhale[d]?\b":          "inhaled",
    r"\binhaler\b":             "inhaled",
    r"\bsublingual\b":          "sublingual",
    r"\bunder\s+tongue\b":      "sublingual",
    r"\bSL\b":                  "sublingual",
    r"\beye\s+drops?\b":        "ophthalmic",
    r"\bear\s+drops?\b":        "otic",
    r"\bnasal\b":               "nasal",
    r"\bnose\s+drops?\b":       "nasal",
    r"\brectal\b":              "rectal",
    r"\bIV\b":                  "intravenous",
    r"\bintravenous\b":         "intravenous",
    r"\bIM\b":                  "intramuscular",
    r"\bintramuscular\b":       "intramuscular",
    r"\bsubcutaneous\b":        "subcutaneous",
    r"\binjection\b":           "injection",
}

# ---------------------------------------------------------------------------
# INSTRUCTIONS — post-extraction instruction fragments
# ---------------------------------------------------------------------------
INSTRUCTION_PATTERNS = [
    (re.compile(r"\bafter\s+(?:food|meals?|eating)\b", re.I),  "after food"),
    (re.compile(r"\bbefore\s+(?:food|meals?|eating)\b", re.I), "before food"),
    (re.compile(r"\bbefore\s+breakfast\b", re.I),               "before breakfast"),
    (re.compile(r"\bwith\s+food\b", re.I),                      "with food"),
    (re.compile(r"\bon\s+empty\s+stomach\b", re.I),             "on empty stomach"),
    (re.compile(r"\bwith\s+water\b", re.I),                     "with water"),
    (re.compile(r"\bwith\s+milk\b", re.I),                      "with milk"),
    (re.compile(r"\bswallow\s+whole\b", re.I),                  "swallow whole"),
    (re.compile(r"\bdo\s+not\s+crush\b", re.I),                "do not crush"),
    (re.compile(r"\bchew\b", re.I),                             "chew before swallowing"),
    (re.compile(r"\bdissolve\b", re.I),                         "dissolve in water"),
    (re.compile(r"\bin\s+the\s+morning\b", re.I),               "in the morning"),
    # timing hint — the extractor drops this if frequency itself is "at bedtime"
    (re.compile(r"\bat\s+(?:bedtime|night)\b|\bbefore\s+bed\b", re.I), "at bedtime"),
]

# ---------------------------------------------------------------------------
# NOISE TOKENS — leading words that are not part of a drug name
# ---------------------------------------------------------------------------
DRUG_NOISE_TOKENS = {
    "tab", "tabs", "tablet", "tablets", "cap", "caps", "capsule", "capsules",
    "syp", "syrup", "inj", "injection", "give", "start", "prescribe",
    "patient", "the", "on", "take",
}
