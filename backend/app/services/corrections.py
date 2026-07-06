"""
Clinician corrections to extracted drug entries.

When a clinician edits or verifies an entry, the entry becomes
manually_verified and is never flagged again — human review outranks the
NLP confidence score (which is preserved untouched for the audit trail).
"""
from app.core.nlp.validator import drug_validator
from app.models.prescription import DrugEntry, DrugEntryUpdate


def apply_drug_correction(original: DrugEntry, update: DrugEntryUpdate) -> DrugEntry:
    """
    Merge the provided fields onto the original entry. If the drug name
    changed, re-validate it against the formulary so generic_name/category
    stay consistent; an off-formulary name is kept as typed (the clinician
    is the authority) but gets no dictionary metadata.
    """
    corrected = original.model_copy(deep=True)
    changed = update.model_dump(exclude_unset=True, exclude_none=True)

    for field, value in changed.items():
        if isinstance(value, str):
            value = value.strip() or None    # cleared field → None, not ""
        setattr(corrected, field, value)

    if "drug_name" in changed and corrected.drug_name:
        record, _score = drug_validator.lookup(corrected.drug_name)
        if record:
            corrected.generic_name = record.get("generic_name")
            corrected.category = record.get("category")
        else:
            corrected.generic_name = corrected.drug_name
            corrected.category = None

    corrected.manually_verified = True
    corrected.flagged_for_review = False
    return corrected
