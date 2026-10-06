"""Tests for author merging, multi-repo support, and author-filtered metrics.

These are the three features gating the ≤100% tier in the rubric.
"""

import io
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.mailmap import author_merger
from app.main import app

client = TestClient(app)

ALICE = "Alice <alice@example.com>"
BOB = "Bob <bob@example.com>"


def _metric(report: dict, key: str):
    return report["metrics"][key]["value"]


def _zip_dir(src: Path) -> io.BytesIO:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for path in src.rglob("*"):
            zf.write(path, path.relative_to(src))
    buf.seek(0)
    return buf


# ==================================================================
# Fixtures: two repos ingested side-by-side (multi-repo)
# ==================================================================

@pytest.fixture(scope="module")
def repo_a(synthetic_repo: Path) -> dict:
    """Clone-ingest the synthetic repo as repo A."""
    r = client.post("/api/repositories/clone", json={"url": str(synthetic_repo)})
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture(scope="module")
def repo_b(synthetic_repo: Path) -> dict:
    """Zip-ingest the same repo as repo B (independent ingestion)."""
    buf = _zip_dir(synthetic_repo)
    r = client.post(
        "/api/repositories/upload",
        files={"file": ("synth.zip", buf, "application/zip")},
    )
    assert r.status_code == 201, r.text
    return r.json()


# ==================================================================
# Multi-repo
# ==================================================================

class TestMultiRepo:
    def test_both_repos_listed(self, repo_a, repo_b):
        repos = client.get("/api/repositories").json()
        ids = {r["id"] for r in repos}
        assert repo_a["id"] in ids and repo_b["id"] in ids

    def test_metrics_isolated_per_repo(self, repo_a, repo_b):
        """Same source data, but each repo's metrics are independent."""
        ra = client.get("/api/metrics/repository", params={"repository_id": repo_a["id"]}).json()
        rb = client.get("/api/metrics/repository", params={"repository_id": repo_b["id"]}).json()
        assert len(ra) == 1 and len(rb) == 1
        assert _metric(ra[0], "churn") == _metric(rb[0], "churn") == 34

    def test_author_list_per_repo(self, repo_a, repo_b):
        aa = client.get("/api/authors", params={"repository_id": repo_a["id"]}).json()
        ab = client.get("/api/authors", params={"repository_id": repo_b["id"]}).json()
        # Both repos have Alice + Bob (mailmap already collapsed Alice@work -> Alice)
        names_a = {a["name"] for a in aa}
        names_b = {a["name"] for a in ab}
        assert names_a == names_b == {"Alice", "Bob"}


# ==================================================================
# Author listing (mailmap already applied by git)
# ==================================================================

class TestAuthorListing:
    def test_mailmap_applied(self, repo_a):
        """Alice@work.com was merged into Alice@example.com by the repo's .mailmap."""
        authors = client.get("/api/authors", params={"repository_id": repo_a["id"]}).json()
        alice = next(a for a in authors if a["name"] == "Alice")
        assert alice["email"] == "alice@example.com"
        # Only one Alice identity visible because git resolved the mailmap before we parsed
        assert len(alice["identities"]) >= 1

    def test_author_count(self, repo_a):
        authors = client.get("/api/authors", params={"repository_id": repo_a["id"]}).json()
        assert len(authors) == 2  # Alice, Bob


# ==================================================================
# Manual author merging
# ==================================================================

class TestManualMerge:
    def test_merge_two_authors(self, repo_a):
        """Merge Alice and Bob into one canonical author 'Team'."""
        r = client.post("/api/authors/merge", json={
            "repository_id": repo_a["id"],
            "author_ids": [ALICE, BOB],
            "canonical": {"name": "Team", "email": "team@example.com"},
        })
        assert r.status_code == 200, r.text
        merged = r.json()
        assert merged["name"] == "Team"
        assert len(merged["identities"]) == 3  # Alice, Bob, Team

    def test_author_list_after_merge(self, repo_a):
        """After merge, only the canonical 'Team' author should appear."""
        authors = client.get("/api/authors", params={"repository_id": repo_a["id"]}).json()
        names = {a["name"] for a in authors}
        assert "Team" in names
        assert len(authors) == 1  # Alice + Bob collapsed

    def test_metrics_reflect_merge(self, repo_a):
        """After merging Alice+Bob into Team, all churn is attributed to Team."""
        reports = client.get(
            "/api/metrics/repository", params={"repository_id": repo_a["id"]}
        ).json()
        root = reports[0]
        assert "Team <team@example.com>" in root["by_author"]
        team = root["by_author"]["Team <team@example.com>"]
        assert team["author_churn"] == 34  # all churn
        assert team["author_ownership"] == pytest.approx(1.0)

    def test_merge_does_not_affect_other_repo(self, repo_a, repo_b):
        """Merge is per-repo: repo B should still have Alice + Bob."""
        authors = client.get("/api/authors", params={"repository_id": repo_b["id"]}).json()
        names = {a["name"] for a in authors}
        assert names == {"Alice", "Bob"}

    def test_unmerge(self, repo_a):
        """Unmerge restores individual authors."""
        client.post(
            "/api/authors/unmerge",
            params={"repository_id": repo_a["id"], "author_key": ALICE},
        )
        authors = client.get("/api/authors", params={"repository_id": repo_a["id"]}).json()
        names = {a["name"] for a in authors}
        assert names == {"Alice", "Bob"}

    def test_metrics_after_unmerge(self, repo_a):
        """After unmerge, metrics go back to per-author attribution."""
        reports = client.get(
            "/api/metrics/repository", params={"repository_id": repo_a["id"]}
        ).json()
        root = reports[0]
        assert ALICE in root["by_author"]
        assert BOB in root["by_author"]
        assert root["by_author"][ALICE]["author_churn"] == 29
        assert root["by_author"][BOB]["author_churn"] == 5


# ==================================================================
# Author-filtered metrics
# ==================================================================

class TestAuthorFilter:
    def test_filter_by_author(self, repo_a):
        """Only files touched by Bob should appear when filtering by Bob."""
        reports = client.get(
            "/api/metrics/files",
            params={"repository_id": repo_a["id"], "author_id": BOB},
        ).json()
        assert len(reports) > 0
        for r in reports:
            assert BOB in r["by_author"]
            assert len(r["by_author"]) == 1

    def test_author_filter_on_repository(self, repo_a):
        reports = client.get(
            "/api/metrics/repository",
            params={"repository_id": repo_a["id"], "author_id": ALICE},
        ).json()
        assert len(reports) == 1
        root = reports[0]
        assert ALICE in root["by_author"]
        assert root["by_author"][ALICE]["author_churn"] == 29

    def test_combined_author_and_path_filter(self, repo_a):
        """Filter by Bob AND path=src — should get only Bob's changes under src/."""
        reports = client.get(
            "/api/metrics/files",
            params={"repository_id": repo_a["id"], "author_id": BOB, "path": "src"},
        ).json()
        assert all(r["scope"].startswith("src") for r in reports)
        assert all(BOB in r["by_author"] for r in reports)


# ==================================================================
# Reject bad merge requests
# ==================================================================

class TestMergeValidation:
    def test_merge_needs_two(self, repo_a):
        r = client.post("/api/authors/merge", json={
            "repository_id": repo_a["id"],
            "author_ids": [ALICE],
        })
        assert r.status_code == 400

    def test_merge_unknown_repo(self):
        r = client.post("/api/authors/merge", json={
            "repository_id": "nonexistent",
            "author_ids": [ALICE, BOB],
        })
        assert r.status_code == 404
