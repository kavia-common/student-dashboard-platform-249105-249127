"""
Minimal backend smoke tests.

These tests intentionally avoid touching the real database by overriding the
`get_db` dependency and injecting minimal auth dependencies.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_healthcheck_returns_200_and_message(app_with_overrides):
    """Smoke test: backend starts and health endpoint responds."""
    client = TestClient(app_with_overrides)
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Healthy"}
