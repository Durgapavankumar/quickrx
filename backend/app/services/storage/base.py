import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from app.models.prescription import (
    PrescriptionSession, PatientInfo, PatientSummary, DrugEntry
)


class SessionStoreBase(ABC):
    """
    Storage contract for prescription sessions.
    Each session = one patient visit (one clinician, one patient, N drug entries).
    Implementations must be swappable without touching routes or the NLP pipeline.
    """

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _new_session(patient_info: PatientInfo) -> PrescriptionSession:
        return PrescriptionSession(
            session_id=str(uuid.uuid4()),
            patient_info=patient_info,
            drugs=[],
            flagged_count=0,
            created_at=datetime.utcnow().isoformat() + "Z",
        )

    @staticmethod
    def _recount_flags(session: PrescriptionSession) -> None:
        session.flagged_count = sum(1 for d in session.drugs if d.flagged_for_review)

    @staticmethod
    def patient_key(name: str | None) -> str:
        """Patients are identified by normalised name (MVP — no patient IDs yet)."""
        return " ".join((name or "").lower().split())

    # ------------------------------------------------------------------
    # Interface
    # ------------------------------------------------------------------
    @abstractmethod
    def create(self, patient_info: PatientInfo) -> PrescriptionSession: ...

    @abstractmethod
    def get(self, session_id: str) -> PrescriptionSession | None: ...

    @abstractmethod
    def save(self, session: PrescriptionSession) -> None:
        """Persist a modified session (drug edits, deletions)."""

    @abstractmethod
    def delete(self, session_id: str) -> bool: ...

    @abstractmethod
    def list_sessions(self, patient_name: str | None = None,
                      limit: int = 50) -> list[PrescriptionSession]:
        """Newest-first session list, optionally filtered by patient name."""

    @abstractmethod
    def list_patients(self) -> list[PatientSummary]:
        """Distinct patients with visit counts, most recent first."""

    # ------------------------------------------------------------------
    # Convenience mutations built on get + save
    # ------------------------------------------------------------------
    def add_drug(self, session_id: str, drug: DrugEntry) -> PrescriptionSession | None:
        session = self.get(session_id)
        if not session:
            return None
        session.drugs.append(drug)
        self._recount_flags(session)
        self.save(session)
        return session

    def update_drug(self, session_id: str, index: int,
                    drug: DrugEntry) -> PrescriptionSession | None:
        session = self.get(session_id)
        if not session or not 0 <= index < len(session.drugs):
            return None
        session.drugs[index] = drug
        self._recount_flags(session)
        self.save(session)
        return session

    def remove_drug(self, session_id: str, index: int) -> PrescriptionSession | None:
        session = self.get(session_id)
        if not session or not 0 <= index < len(session.drugs):
            return None
        session.drugs.pop(index)
        self._recount_flags(session)
        self.save(session)
        return session
