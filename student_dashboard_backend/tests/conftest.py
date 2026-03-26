from __future__ import annotations

import os
import sys
from pathlib import Path
from collections.abc import Generator
from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest

# Ensure the backend package root is importable in tests (so `import src...` works)
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))


@dataclass(frozen=True)
class _DummyUser:
    """Minimal stand-in for src.api.models.User, just enough for dependency injection."""
    id: UUID
    email: str = "test@example.com"
    is_active: bool = True


@pytest.fixture(scope="session", autouse=True)
def _set_required_env_vars() -> None:
    """
    Ensure required env vars exist for import-time Settings loading.

    The backend's src.api.core.config.get_settings() is evaluated during import
    of src.api.main and src.api.core.db, so we must define these early.
    """
    os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
    # Use an in-memory sqlite URL as a placeholder; we override get_db anyway.
    os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")


@pytest.fixture()
def app_with_overrides() -> Generator:
    """
    Provide a FastAPI app instance with dependency overrides for tests.

    - Overrides get_db to avoid any real DB connection.
    - Overrides get_current_user and require_roles(...) so endpoints can be called
      without JWT setup in minimal smoke tests.
    """
    # Import after env vars are set (see session autouse fixture above).
    from src.api.main import app
    from src.api.core.auth import get_current_user, require_roles
    from src.api.core.db import get_db

    def _fake_db():
        # Yield a simple object; our smoke tests won't touch it.
        yield object()

    def _fake_current_user():
        return _DummyUser(id=uuid4())

    def _fake_require_roles(_: set[str]):
        def _dep():
            return _DummyUser(id=uuid4())

        return _dep

    # Apply overrides
    app.dependency_overrides[get_db] = _fake_db
    app.dependency_overrides[get_current_user] = _fake_current_user
    # require_roles is a factory, so override the factory itself.
    app.dependency_overrides[require_roles] = _fake_require_roles

    try:
        yield app
    finally:
        app.dependency_overrides.clear()
