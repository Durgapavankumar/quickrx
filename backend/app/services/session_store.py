import uuid
from datetime import datetime
from app.models.prescription import PrescriptionSession, PatientInfo, DrugEntry


class SessionStore:
    """
    In-memory store for active prescription sessions.
    Each session = one patient visit (one clinician, one patient, N drug entries).
    For MVP: stored in memory. Ready to swap for SQLite/PostgreSQL later.
    """

    def __init__(self):
        self._sessions: dict[str, PrescriptionSession] = {}

    def create(self, patient_info: PatientInfo) -> PrescriptionSession:
        session_id = str(uuid.uuid4())
        session = PrescriptionSession(
            session_id=session_id,
            patient_info=patient_info,
            drugs=[],
            flagged_count=0,
            created_at=datetime.utcnow().isoformat() + "Z",
        )
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> PrescriptionSession | None:
        return self._sessions.get(session_id)

    def add_drug(self, session_id: str, drug: DrugEntry) -> PrescriptionSession | None:
        session = self.get(session_id)
        if not session:
            return None
        session.drugs.append(drug)
        session.flagged_count = sum(1 for d in session.drugs if d.flagged_for_review)
        return session

    def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def all_sessions(self) -> list[PrescriptionSession]:
        return list(self._sessions.values())


# Singleton
session_store = SessionStore()
