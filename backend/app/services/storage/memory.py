from app.models.prescription import PrescriptionSession, PatientInfo, PatientSummary
from app.services.storage.base import SessionStoreBase


class InMemorySessionStore(SessionStoreBase):
    """Dict-backed store — sessions vanish on restart. Useful for tests/dev."""

    def __init__(self):
        self._sessions: dict[str, PrescriptionSession] = {}

    def create(self, patient_info: PatientInfo) -> PrescriptionSession:
        session = self._new_session(patient_info)
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> PrescriptionSession | None:
        return self._sessions.get(session_id)

    def save(self, session: PrescriptionSession) -> None:
        self._sessions[session.session_id] = session

    def delete(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None

    def list_sessions(self, patient_name: str | None = None,
                      limit: int = 50) -> list[PrescriptionSession]:
        sessions = sorted(self._sessions.values(),
                          key=lambda s: s.created_at, reverse=True)
        if patient_name:
            key = self.patient_key(patient_name)
            sessions = [s for s in sessions
                        if self.patient_key(s.patient_info.patient_name) == key]
        return sessions[:limit]

    def list_patients(self) -> list[PatientSummary]:
        patients: dict[str, PatientSummary] = {}
        for s in sorted(self._sessions.values(), key=lambda s: s.created_at):
            key = self.patient_key(s.patient_info.patient_name)
            if not key:
                continue
            existing = patients.get(key)
            patients[key] = PatientSummary(
                patient_name=s.patient_info.patient_name,
                visit_count=(existing.visit_count + 1) if existing else 1,
                last_visit=s.created_at,
            )
        return sorted(patients.values(), key=lambda p: p.last_visit, reverse=True)
