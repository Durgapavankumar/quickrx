"""
QuickRx NLP Extraction Validation Suite
Run: python tests/test_extractor.py
Exits non-zero if any field falls below the 90% accuracy target (CI-friendly).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.nlp.extractor import extractor

# (transcript, expected_drug_fragment, expected_dose, expected_freq, expected_duration)
# None = field not asserted for that sentence.
VALIDATION_SET = [
    # ---- original 50-sentence core set -----------------------------------
    ("Paracetamol 500mg twice daily for 5 days",          "paracetamol", "500", "twice daily",       "5"),
    ("Tab Azithromycin 500 mg once daily for 3 days",     "azithromycin","500", "once daily",        "3"),
    ("Amoxicillin 250mg TDS for 7 days",                  "amoxicillin", "250", "three times daily", "7"),
    ("Metformin 1000mg twice a day",                      "metformin",   "1000","twice daily",       None),
    ("Atorvastatin 20mg at bedtime",                      "atorvastatin","20",  "at bedtime",        None),
    ("Cetirizine 10mg OD for 5 days",                     "cetirizine",  "10",  "once daily",        "5"),
    ("Ciprofloxacin 500 mg BD for 5 days",                "ciprofloxacin","500","twice daily",       "5"),
    ("Omeprazole 20mg once daily before food",            "omeprazole",  "20",  "once daily",        None),
    ("Prednisolone 10mg once daily for 7 days",           "prednisolone","10",  "once daily",        "7"),
    ("Metronidazole 400mg three times a day for 5 days",  "metronidazole","400","three times daily", "5"),
    ("give domperidone 10 mg TDS",                        "domperidone", "10",  "three times daily", None),
    ("Salbutamol 2mg twice daily",                        "salbutamol",  "2",   "twice daily",       None),
    ("Montelukast 10mg once daily at bedtime",            "montelukast", "10",  "once daily",        None),
    ("Tab amlodipine 5mg once a day",                     "amlodipine",  "5",   "once daily",        None),
    ("Pantoprazole 40mg once daily before breakfast",     "pantoprazole","40",  "once daily",        None),
    ("Ondansetron 4mg twice daily for 3 days",            "ondansetron", "4",   "twice daily",       "3"),
    ("Sertraline 50mg once daily",                        "sertraline",  "50",  "once daily",        None),
    ("Losartan 50mg once daily",                          "losartan",    "50",  "once daily",        None),
    ("Doxycycline 100mg twice daily for 7 days",          "doxycycline", "100", "twice daily",       "7"),
    ("Furosemide 40mg once daily",                        "furosemide",  "40",  "once daily",        None),
    ("Aspirin 75mg once daily",                           "aspirin",     "75",  "once daily",        None),
    ("Clopidogrel 75mg once a day",                       "clopidogrel", "75",  "once daily",        None),
    ("Levothyroxine 50 mcg once daily before breakfast",  "levothyroxine","50", "once daily",        None),
    ("Metoprolol 50mg twice daily",                       "metoprolol",  "50",  "twice daily",       None),
    ("Fluconazole 150mg single dose",                     "fluconazole", "150", "single dose",       None),
    ("Ranitidine 150mg twice a day for 2 weeks",          "ranitidine",  "150", "twice daily",       "2"),
    ("Albendazole 400mg single dose",                     "albendazole", "400", "single dose",       None),
    ("Ibuprofen 400mg three times daily for 5 days",      "ibuprofen",   "400", "three times daily", "5"),
    ("Acyclovir 800mg five times a day for 7 days",       "acyclovir",   "800", "five times daily",  "7"),
    ("Diazepam 5mg at bedtime for 5 days",                "diazepam",    "5",   "at bedtime",        "5"),
    ("Amitriptyline 25mg at bedtime",                     "amitriptyline","25", "at bedtime",        None),
    ("Pregabalin 75mg twice daily",                       "pregabalin",  "75",  "twice daily",       None),
    ("Telmisartan 40mg once daily",                       "telmisartan", "40",  "once daily",        None),
    # "once daily at night" → frequency stays "once daily"; the night timing
    # is captured under instructions ("at bedtime") instead.
    ("Rosuvastatin 10mg once daily at night",             "rosuvastatin","10",  "once daily",        None),
    ("Hydroxychloroquine 200mg twice daily",              "hydroxychloroquine","200","twice daily",   None),
    ("Colchicine 0.5mg twice a day for 5 days",          "colchicine",  "0.5", "twice daily",       "5"),
    ("Esomeprazole 40mg once daily",                      "esomeprazole","40",  "once daily",        None),
    ("Calcium carbonate 500mg twice daily",               "calcium carbonate","500","twice daily",   None),
    ("Tramadol 50mg three times daily",                   "tramadol",    "50",  "three times daily", None),
    ("Levofloxacin 750mg once daily for 5 days",         "levofloxacin","750", "once daily",        "5"),
    ("Cefixime 200mg twice daily for 5 days",            "cefixime",    "200", "twice daily",       "5"),
    ("Bisoprolol 5mg once daily",                         "bisoprolol",  "5",   "once daily",        None),
    ("Amiodarone 200mg once daily",                       "amiodarone",  "200", "once daily",        None),
    ("Spironolactone 25mg twice daily",                   "spironolactone","25","twice daily",       None),
    ("Vitamin D3 60000 IU once a week",                  "vitamin d3",  "60000","once weekly",      None),
    ("Methylcobalamin 500 mcg twice daily",              "methylcobalamin","500","twice daily",      None),
    ("Olanzapine 5mg at bedtime",                         "olanzapine",  "5",   "at bedtime",        None),
    ("Escitalopram 10mg once daily",                     "escitalopram","10",  "once daily",        None),
    ("Glimepiride 2mg once daily before breakfast",       "glimepiride", "2",   "once daily",        None),
    ("Empagliflozin 10mg once daily",                    "empagliflozin","10", "once daily",        None),

    # ---- edge cases: spelled-out numbers / units --------------------------
    ("Amoxicillin 500 milligrams three times daily for seven days",
                                                          "amoxicillin", "500", "three times daily", "7"),
    ("Prednisolone 10 mg in the morning for five days",   "prednisolone","10",  None,                "5"),
    ("Cefixime 200 mg BD for one week",                   "cefixime",    "200", "twice daily",       "1"),
    ("Doxycycline 100mg twice daily for a week",          "doxycycline", "100", "twice daily",       "1"),
    ("Levothyroxine 25 micrograms once daily",            "levothyroxine","25", "once daily",        None),

    # ---- edge cases: Indian 1-0-1 shorthand -------------------------------
    ("Paracetamol 650 mg 1-0-1 after food",               "paracetamol", "650", "twice daily",       None),
    ("Metformin 500mg 1-1-1 with food",                   "metformin",   "500", "three times daily", None),
    ("Alprazolam 0.25mg 0-0-1",                           "alprazolam",  "0.25","at bedtime",        None),

    # ---- edge cases: brand-name aliases -----------------------------------
    ("Tab Dolo 650 mg TDS for 3 days",                    "paracetamol", "650", "three times daily", "3"),
    ("Crocin 500 mg twice daily",                         "paracetamol", "500", "twice daily",       None),
    ("Brufen 400 mg three times a day after food",        "ibuprofen",   "400", "three times daily", None),

    # ---- edge cases: tablet / puff doses ----------------------------------
    ("Vitamin B complex one tablet once daily",           "vitamin b",   "1",   "once daily",        None),
    ("Domperidone one tablet three times a day before meals",
                                                          "domperidone", "1",   "three times daily", None),
    ("Salbutamol two puffs SOS",                          "salbutamol",  "2",   "as needed",         None),

    # ---- edge cases: hourly / weekly / alternate-day frequencies ----------
    ("Ibuprofen 400mg every 8 hours for 3 days",          "ibuprofen",   "400", "every 8 hours",     "3"),
    ("Amoxicillin 250mg every six hours",                 "amoxicillin", "250", "every 6 hours",     None),
    ("Vitamin D3 60000 IU once weekly for 8 weeks",       "vitamin d3",  "60000","once weekly",      "8"),
    ("Aspirin 75mg on alternate days",                    "aspirin",     "75",  "alternate days",    None),
    ("Chlorpheniramine 4mg at night",                     "chlorpheniramine","4","at bedtime",       None),

    # ---- edge cases: filler words before the drug --------------------------
    ("Give patient ondansetron 4 mg before food",         "ondansetron", "4",   None,                None),
]


def evaluate():
    """Run the extractor over the validation set; returns (results, records)."""
    field_names = ["drug", "dose", "freq", "duration"]
    passed = {f: 0 for f in field_names}
    testable = {f: 0 for f in field_names}
    flagged = 0
    records = []

    for transcript, exp_drug, exp_dose, exp_freq, exp_dur in VALIDATION_SET:
        e = extractor.extract(transcript)
        if e.flagged_for_review:
            flagged += 1

        checks = {
            "drug":     (exp_drug, e.generic_name and exp_drug and exp_drug.lower() in e.generic_name.lower()),
            "dose":     (exp_dose, e.dose == exp_dose),
            "freq":     (exp_freq, e.frequency == exp_freq),
            "duration": (exp_dur,  e.duration == exp_dur),
        }

        failures = {}
        for field, (expected, ok) in checks.items():
            if expected is None:
                continue
            testable[field] += 1
            if ok:
                passed[field] += 1
            else:
                got = {"drug": e.generic_name, "dose": e.dose,
                       "freq": e.frequency, "duration": e.duration}[field]
                failures[field] = (got, expected)

        records.append((transcript, e, failures))

    return passed, testable, flagged, records


def run_tests() -> bool:
    passed, testable, flagged, records = evaluate()
    total = len(VALIDATION_SET)

    print(f"\n{'='*65}")
    print(f" QuickRx NLP Validation — {total} sentences")
    print(f"{'='*65}\n")

    for transcript, e, failures in records:
        status = "✓" if not failures else "✗"
        flag = "⚠" if e.flagged_for_review else " "
        print(f"{flag}{status} [{e.confidence:.2f}] {transcript[:55]:<55}")
        for field, (got, want) in failures.items():
            print(f"     {field.capitalize()+':':<6} got={got}  want={want}")

    print(f"\n{'='*65}")
    print(f" RESULTS")
    print(f"{'='*65}")
    all_on_target = True
    for field in passed:
        t = testable[field]
        pct = passed[field] / t * 100 if t else 100.0
        on_target = pct >= 90
        all_on_target = all_on_target and on_target
        print(f"  {field:<12}: {passed[field]}/{t}  ({pct:.1f}%)  "
              f"{'✓' if on_target else '✗ (below target)'}")

    print(f"  {'flagged':<12}: {flagged}/{total} extractions flagged for review")
    print(f"\n  Target: ≥90% field-level accuracy on all fields")
    print(f"{'='*65}\n")
    return all_on_target


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
