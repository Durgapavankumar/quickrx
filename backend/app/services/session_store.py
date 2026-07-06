"""
Session store singleton — backend chosen by settings.STORAGE_BACKEND.
Routes import `session_store` from here; the actual implementation
(SQLite / in-memory) lives in app/services/storage/ and can be swapped
via config without touching anything else.
"""
from app.core.config import settings
from app.services.storage import create_session_store
from app.services.storage.base import SessionStoreBase

session_store: SessionStoreBase = create_session_store(
    settings.STORAGE_BACKEND,
    db_path=settings.DB_PATH,
)
