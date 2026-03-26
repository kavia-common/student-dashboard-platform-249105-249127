from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.api.core.config import get_settings

# NOTE: sync engine/session are sufficient for this monolithic backend.
# We keep pool_pre_ping enabled to gracefully handle stale connections.
_settings = get_settings()
engine = create_engine(_settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a SQLAlchemy Session and ensures it's closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
