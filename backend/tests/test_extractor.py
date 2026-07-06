"""
QuickRx NLP Extraction Validation Suite
Run: python -m pytest tests/test_extractor.py -v
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.nlp.extractor import extractor

# (transcript, expected_drug_fragment, expected_dose, expected_freq, expected_duration)
VALIDATION_SET = [
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
    ("Fluconazole 150mg single dose",                     "fluconazole", "150", None,                None),
    ("Ranitidine 150mg twice a day for 2 weeks",          "ranitidine",  "150", "twice daily",       "2"),
    ("Albendazole 400mg single dose",                     "albendazole", "400", None,                None),
    ("Ibuprofen 400mg three times daily for 5 days",      "ibuprofen",   "400", "three times daily", "5"),
    ("Acyclovir 800mg five times a day for 7 days",       "acyclovir",   "800", None,                "7"),
    ("Diazepam 5mg at bedtime for 5 days",                "diazepam",    "5",   "at bedtime",        "5"),
    ("Amitriptyline 25mg at bedtime",                     "amitriptyline","25", "at bedtime",        None),
    ("Pregabalin 75mg twice daily",                       "pregabalin",  "75",  "twice daily",       None),
    ("Telmisartan 40mg once daily",                       "telmisartan", "40",  "once daily",        None),
    ("Rosuvastatin 10mg once daily at night",             "rosuvastatin","10",  "at bedtime",        None),
    ("Hydroxychloroquine 200mg twice daily",              "hydroxychloroquine","200","twice daily",   None),
    ("Colchicine 0.5mg twice a day for 5 days",          "colchicine",  None,  "twice daily",       "5"),
    ("Esomeprazole 40mg once daily",                      "esomeprazole","40",  "once daily",        None),
    ("Calcium carbonate 500mg twice daily",               "calcium carbonate","500","twice daily",   None),
    ("Tramadol 50mg three times daily",                   "tramadol",    "50",  "three times daily", None),
    ("Levofloxacin 750mg once daily for 5 days",         "levofloxacin","750", "once daily",        "5"),
    ("Cefixime 200mg twice daily for 5 days",            "cefixime",    "200", "twice daily",       "5"),
    ("Bisoprolol 5mg once daily",                         "bisoprolol",  "5",   "once daily",        None),
    ("Amiodarone 200mg once daily",                       "amiodarone",  "200", "once daily",        None),
    ("Spironolactone 25mg twice daily",                   "spironolactone","25","twice daily",       None),
    ("Vitamin D3 60000 IU once a week",                  "vitamin",     "60000",None,               None),
    ("Methylcobalamin 500 mcg twice daily",              "methylcobalamin","500","twice daily",      None),
    ("Olanzapine 5mg at bedtime",                         "olanzapine",  "5",   "at bedtime",        None),
    ("Escitalopram 10mg once daily",                     "escitalopram","10",  "once daily",        None),
    ("Glimepiride 2mg once daily before breakfast",       "glimepiride", "2",   "once daily",        None),
    ("Empagliflozin 10mg once daily",                    "empagliflozin","10", "once daily",        None),
]

def run_tests():
    total = len(VALIDATION_SET)
    passed = {f: 0 for f in ["drug", "dose", "freq", "duration"]}
    flagged = 0

    print(f"\n{'='*65}")
    print(f" QuickRx NLP Validation — {total} sentences")
    print(f"{'='*65}\n")

    for transcript, exp_drug, exp_dose, exp_freq, exp_dur in VALIDATION_SET:
        e = extractor.extract(transcript)
        if e.flagged_for_review:
            flagged += 1

        drug_ok = exp_drug is None or (
            e.generic_name and exp_drug.lower() in e.generic_name.lower()
        )
        dose_ok  = exp_dose is None or e.dose == exp_dose
        freq_ok  = exp_freq is None or e.frequency == exp_freq
        dur_ok   = exp_dur  is None or e.duration  == exp_dur

        if drug_ok: passed["drug"]     += 1
        if dose_ok: passed["dose"]     += 1
        if freq_ok: passed["freq"]     += 1
        if dur_ok:  passed["duration"] += 1

        status = "✓" if all([drug_ok, dose_ok, freq_ok, dur_ok]) else "✗"
        flag   = "⚠" if e.flagged_for_review else " "
        print(f"{flag}{status} [{e.confidence:.2f}] {transcript[:55]:<55}")
        if not all([drug_ok, dose_ok, freq_ok, dur_ok]):
            if not drug_ok: print(f"     Drug:  got={e.generic_name}  want={exp_drug}")
            if not dose_ok: print(f"     Dose:  got={e.dose}  want={exp_dose}")
            if not freq_ok: print(f"     Freq:  got={e.frequency}  want={exp_freq}")
            if not dur_ok:  print(f"     Dur:   got={e.duration}  want={exp_dur}")

    print(f"\n{'='*65}")
    print(f" RESULTS")
    print(f"{'='*65}")
    testable = {
        "drug":     sum(1 for _, d,*_ in VALIDATION_SET if d),
        "dose":     sum(1 for *_, d,_,_ in VALIDATION_SET if d),
        "freq":     sum(1 for *_, f,_ in VALIDATION_SET if f),
        "duration": sum(1 for *_, d in VALIDATION_SET if d),
    }
    for field, p in passed.items():
        t = testable.get(field, total)
        pct = p / t * 100 if t else 0
        target = "✓" if pct >= 90 else "✗ (below target)"
        print(f"  {field:<12}: {p}/{t}  ({pct:.1f}%)  {target}")

    print(f"  {'flagged':<12}: {flagged}/{total} extractions flagged for review")
    print(f"\n  Target: ≥90% field-level accuracy on all fields")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    run_tests()
