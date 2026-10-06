"""End-to-end API tests: both ingestion paths + wired metric endpoints."""

import io
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture(scope="module")
def cloned(synthetic_repo: Path) -> dict:
    """Clone-ingest the synthetic repo through the API (local path = URL)."""
    response = client.post("/api/repositories/clone", json={"url": str(synthetic_repo)})
    assert response.status_code == 201, response.text
    return response.json()


def _zip_dir(src: Path) -> io.BytesIO:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for path in src.rglob("*"):
            zf.write(path, path.relative_to(src))
    buf.seek(0)
    return buf


def _metric(report: dict, key: str):
    return report["metrics"][key]["value"]


# ----------------------------------------------------------------------
# Ingestion
# ----------------------------------------------------------------------

def test_clone_ingestion(cloned):
    assert cloned["source"] == "url"
    assert cloned["default_branch"] in ("master", "main")
    repos = client.get("/api/repositories").json()
    assert any(r["id"] == cloned["id"] for r in repos)


def test_zip_upload_ingestion(synthetic_repo: Path):
    buf = _zip_dir(synthetic_repo)
    response = client.post(
        "/api/repositories/upload",
        files={"file": ("repo.zip", buf, "application/zip")},
    )
    assert response.status_code == 201, response.text
    assert response.json()["source"] == "zip"


def test_upload_rejects_non_zip():
    response = client.post(
        "/api/repositories/upload",
        files={"file": ("notes.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert response.status_code == 400


def test_upload_rejects_zip_without_git(tmp_path: Path):
    plain = tmp_path / "plain"
    plain.mkdir()
    (plain / "file.txt").write_text("no history here")
    response = client.post(
        "/api/repositories/upload",
        files={"file": ("plain.zip", _zip_dir(plain), "application/zip")},
    )
    assert response.status_code == 400
    assert ".git" in response.json()["detail"]


def test_clone_rejects_bad_url():
    response = client.post(
        "/api/repositories/clone", json={"url": "/nonexistent/nowhere.git"}
    )
    assert response.status_code == 400


# ----------------------------------------------------------------------
# Metrics over the ingested repo (values proven in test_engine.py)
# ----------------------------------------------------------------------

def test_repository_metrics(cloned):
    reports = client.get(
        "/api/metrics/repository", params={"repository_id": cloned["id"]}
    ).json()
    assert len(reports) == 1 and reports[0]["scope"] == "/"
    root = reports[0]
    assert _metric(root, "added_lines") == 27
    assert _metric(root, "removed_lines") == 7
    assert _metric(root, "churn") == 34
    assert _metric(root, "growth") == 20
    assert _metric(root, "modifications") == 6
    assert _metric(root, "modification_frequency") == pytest.approx(0.75)
    assert _metric(root, "churn_rate") == pytest.approx(4.25)
    assert root["by_author"]["Alice <alice@example.com>"]["author_churn"] == 29
    assert root["by_author"]["Bob <bob@example.com>"]["author_ownership"] == pytest.approx(5 / 34)


def test_file_metrics(cloned):
    reports = client.get(
        "/api/metrics/files", params={"repository_id": cloned["id"]}
    ).json()
    by_scope = {r["scope"]: r for r in reports}
    main = by_scope["src/main.py"]
    assert _metric(main, "churn") == 21
    assert _metric(main, "modification_frequency") == pytest.approx(3 / 8)
    assert "bin.dat" not in by_scope
    assert "src/a.py" not in by_scope


def test_directory_metrics(cloned):
    reports = client.get(
        "/api/metrics/directories", params={"repository_id": cloned["id"]}
    ).json()
    by_scope = {r["scope"]: r for r in reports}
    assert _metric(by_scope["src"], "churn") == 25  # 21 (a.py/main.py) + 4 (lib/b.py)
    assert _metric(by_scope["src/lib"], "added_lines") == 4
    assert "src/util" not in by_scope


def test_path_filter(cloned):
    reports = client.get(
        "/api/metrics/files", params={"repository_id": cloned["id"], "path": "src"}
    ).json()
    assert reports and all(
        r["scope"] == "src" or r["scope"].startswith("src/") for r in reports
    )


def test_time_filter(cloned):
    reports = client.get(
        "/api/metrics/repository",
        params={"repository_id": cloned["id"], "since": "1970-01-01T01:06:40Z"},
    ).json()
    assert _metric(reports[0], "churn") == 9  # H_4000 = c4..c8


def test_manual_commit_list(cloned):
    commits = client.get(f"/api/repositories/{cloned['id']}/commits").json()
    assert len(commits) == 8
    by_ts = {c["timestamp"]: c["sha"] for c in commits}
    c4 = by_ts["1970-01-01T01:06:40Z"]
    c5 = by_ts["1970-01-01T01:23:20Z"]
    reports = client.get(
        "/api/metrics/commit-set",
        params={"repository_id": cloned["id"], "commits": [c4, c5]},
    ).json()
    root = next(r for r in reports if r["scope"] == "/")
    assert _metric(root, "churn") == 7
    assert _metric(root, "churn_rate") == pytest.approx(3.5)


def test_unknown_repository_404():
    response = client.get(
        "/api/metrics/repository", params={"repository_id": "nope"}
    )
    assert response.status_code == 404
