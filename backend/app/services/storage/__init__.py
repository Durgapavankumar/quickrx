from app.services.storage.base import SessionStoreBase
from app.services.storage.memory import InMemorySessionStore
from app.services.storage.sqlite import SQLiteSessionStore


def create_session_store(backend: str, **kwargs) -> SessionStoreBase:
    """Factory — storage stays swappable behind SessionStoreBase (see config.STORAGE_BACKEND)."""
    if backend == "sqlite":
        return SQLiteSessionStore(kwargs["db_path"])
    if backend == "memory":
        return InMemorySessionStore()
    raise ValueError(f"Unknown storage backend: {backend!r} (expected 'sqlite' or 'memory')")
