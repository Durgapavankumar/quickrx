import re

# ---------------------------------------------------------------------------
# DOSE  — captures numeric value + unit
# Examples: "500mg", "500 mg", "5 ml", "10 mcg", "2.5 mg"
# ---------------------------------------------------------------------------
DOSE_PATTERN = re.compile(
    r"\b(\d+(?:\.\d+)?)\s*(mg|mcg|ug|ml|g|iu|units?|drops?|puffs?|sachets?)\b",
    re.IGNORECASE
)

# ---------------------------------------------------------------------------
# FREQUENCY — maps spoken variants to canonical labels
# ---------------------------------------------------------------------------
FREQUENCY_MAP = {
    # Once daily
    r"\bonce\s+(?:a\s+)?daily\b":          "once daily",
    r"\bonce\s+(?:a\s+)?day\b":            "once daily",
    r"\bOD\b":                              "once daily",
    r"\b1\s*[\-x]\s*1\b":                  "once daily",

    # Twice daily
    r"\btwice\s+(?:a\s+)?daily\b":         "twice daily",
    r"\btwice\s+(?:a\s+)?day\b":           "twice daily",
    r"\bBD\b":                              "twice daily",
    r"\bBID\b":                             "twice daily",
    r"\b2\s*[\-x]\s*1\b":                  "twice daily",

    # Three times daily
    r"\bthree\s+times\s+(?:a\s+)?day\b":   "three times daily",
    r"\bthrice\s+(?:a\s+)?daily\b":        "three times daily",
    r"\bTDS\b":                             "three times daily",
    r"\bTID\b":                             "three times daily",
    r"\b3\s*[\-x]\s*1\b":                  "three times daily",

    # Four times daily
    r"\bfour\s+times\s+(?:a\s+)?day\b":    "four times daily",
    r"\bQID\b":                             "four times daily",
    r"\bQDS\b":                             "four times daily",
    r"\b4\s*[\-x]\s*1\b":                  "four times daily",

    # Every N hours
    r"\bevery\s+(\d+)\s+hours?\b":         "every {0} hours",

    # SOS / as needed
    r"\bSOS\b":                             "as needed",
    r"\bas\s+needed\b":                     "as needed",
    r"\bPRN\b":                             "as needed",

    # Bedtime
    r"\bat\s+bedtime\b":                    "at bedtime",
    r"\bHS\b":                              "at bedtime",
    r"\bbefore\s+bed\b":                    "at bedtime",
    r"\bnight\b":                           "at bedtime",
}

# ---------------------------------------------------------------------------
# DURATION — captures number + unit
# Examples: "5 days", "2 weeks", "1 month", "for 10 days"
# ---------------------------------------------------------------------------
DURATION_PATTERN = re.compile(
    r"\bfor\s+(\d+)\s+(days?|weeks?|months?)\b"
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
    r"\bnasal\b":               "nasal",
    r"\bnose\s+drops?\b":       "nasal",
    r"\brectal\b":              "rectal",
    r"\bIV\b":                  "intravenous",
    r"\bintravenous\b":         "intravenous",
    r"\bIM\b":                  "intramuscular",
    r"\bintramuscular\b":       "intramuscular",
    r"\binjection\b":           "injection",
}

# ---------------------------------------------------------------------------
# INSTRUCTIONS — post-extraction instruction fragments
# ---------------------------------------------------------------------------
INSTRUCTION_PATTERNS = [
    (re.compile(r"\bafter\s+(?:food|meals?|eating)\b", re.I),  "after food"),
    (re.compile(r"\bbefore\s+(?:food|meals?|eating)\b", re.I), "before food"),
    (re.compile(r"\bwith\s+food\b", re.I),                      "with food"),
    (re.compile(r"\bon\s+empty\s+stomach\b", re.I),             "on empty stomach"),
    (re.compile(r"\bwith\s+water\b", re.I),                     "with water"),
    (re.compile(r"\bswallow\s+whole\b", re.I),                  "swallow whole"),
    (re.compile(r"\bdo\s+not\s+crush\b", re.I),                "do not crush"),
    (re.compile(r"\bchew\b", re.I),                             "chew before swallowing"),
    (re.compile(r"\bdissolve\b", re.I),                         "dissolve in water"),
]
