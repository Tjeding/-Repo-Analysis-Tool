"""Smoke test for the scaffolded app — extend per feature."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_repositories() -> None:
    response = client.get("/api/repositories")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
