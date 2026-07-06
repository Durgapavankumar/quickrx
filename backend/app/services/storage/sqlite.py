import sqlite3
import threading
from pathlib import Path

from app.models.prescription import PrescriptionSession, PatientInfo, PatientSummary
from app.services.storage.base import SessionStoreBase

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id  TEXT PRIMARY KEY,
    patient_key TEXT NOT NULL,          -- normalised patient name for history lookups
    created_at  TEXT NOT NULL,
    data        TEXT NOT NULL           -- full PrescriptionSession JSON (schema = Pydantic model)
);
CREATE INDEX IF NOT EXISTS idx_sessions_patient ON sessions (patient_key);
CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions (created_at);
"""


class SQLiteSessionStore(SessionStoreBase):
    """
    SQLite-backed store. Sessions survive restarts, enabling patient history.
    The full session is stored as JSON so the Pydantic model stays the single
    source of truth for the schema; patient_key/created_at are denormalised
    columns purely for indexed lookups.
    """

    def __init__(self, db_path: Path):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        # FastAPI serves sync endpoints from a threadpool → allow cross-thread
        # use and serialise writes with a lock.
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._lock = threading.Lock()
        with self._lock, self._conn:
            self._conn.executescript(_SCHEMA)

    # ------------------------------------------------------------------
    def create(self, patient_info: PatientInfo) -> PrescriptionSession:
        session = self._new_session(patient_info)
        self.save(session)
        return session

    def get(self, session_id: str) -> PrescriptionSession | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT data FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
        return PrescriptionSession.model_validate_json(row[0]) if row else None

    def save(self, session: PrescriptionSession) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO sessions (session_id, patient_key, created_at, data) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT(session_id) DO UPDATE SET "
                "patient_key = excluded.patient_key, data = excluded.data",
                (
                    session.session_id,
                    self.patient_key(session.patient_info.patient_name),
                    session.created_at,
                    session.model_dump_json(),
                ),
            )

    def delete(self, session_id: str) -> bool:
        with self._lock, self._conn:
            cur = self._conn.execute(
                "DELETE FROM sessions WHERE session_id = ?", (session_id,)
            )
        return cur.rowcount > 0

    def list_sessions(self, patient_name: str | None = None,
                      limit: int = 50) -> list[PrescriptionSession]:
        query = "SELECT data FROM sessions"
        params: tuple = ()
        if patient_name:
            query += " WHERE patient_key = ?"
            params = (self.patient_key(patient_name),)
        query += " ORDER BY created_at DESC LIMIT ?"
        params += (limit,)
        with self._lock:
            rows = self._conn.execute(query, params).fetchall()
        return [PrescriptionSession.model_validate_json(r[0]) for r in rows]

    def list_patients(self) -> list[PatientSummary]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT patient_key, COUNT(*), MAX(created_at) FROM sessions "
                "WHERE patient_key != '' GROUP BY patient_key "
                "ORDER BY MAX(created_at) DESC"
            ).fetchall()
            # display name = as entered on the most recent visit
            display = {
                key: self._conn.execute(
                    "SELECT json_extract(data, '$.patient_info.patient_name') "
                    "FROM sessions WHERE patient_key = ? "
                    "ORDER BY created_at DESC LIMIT 1", (key,)
                ).fetchone()[0]
                for key, _, _ in rows
            }
        return [
            PatientSummary(patient_name=display[key] or key,
                           visit_count=count, last_visit=last)
            for key, count, last in rows
        ]
