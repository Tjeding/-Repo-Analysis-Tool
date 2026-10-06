"""Metric engine arithmetic, proven on the synthetic repo (see conftest).

All expected values below are hand-computed from the fixture history —
this is the correctness gate for the rubric's "all metrics" tier.
"""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.core.git_service import git_service
from app.core.metrics.engine import compute_metrics
from app.services.filters import select_commits

ALICE = "Alice <alice@example.com>"
BOB = "Bob <bob@example.com>"


def ts(seconds: int) -> datetime:
    return datetime.fromtimestamp(seconds, tz=timezone.utc)


@pytest.fixture(scope="module")
def commits(synthetic_repo: Path):
    return git_service.iter_commits(synthetic_repo)


@pytest.fixture(scope="module")
def full(commits):
    return compute_metrics(commits)


# ----------------------------------------------------------------------
# Parsing
# ----------------------------------------------------------------------

def test_merge_commits_excluded_and_newest_first(commits):
    assert [c.timestamp for c in commits] == [8000, 7000, 6000, 5000, 4000, 3000, 2000, 1000]


def test_mailmap_resolves_author(commits):
    c2 = next(c for c in commits if c.timestamp == 2000)
    assert (c2.author_name, c2.author_email) == ("Alice", "alice@example.com")
    assert c2.author_key == ALICE


def test_binary_commit_has_no_file_entries(commits):
    c6 = next(c for c in commits if c.timestamp == 6000)
    assert c6.files == []


def test_pure_rename_entry(commits):
    c3 = next(c for c in commits if c.timestamp == 3000)
    assert len(c3.files) == 1
    f = c3.files[0]
    assert (f.path, f.old_path, f.added, f.removed) == (
        "src/lib/b.py", "src/util/b.py", 0, 0,
    )


def test_rename_with_modification_entry(commits):
    c4 = next(c for c in commits if c.timestamp == 4000)
    f = next(f for f in c4.files if f.path == "src/main.py")
    assert (f.old_path, f.added, f.removed) == ("src/a.py", 2, 2)


# ----------------------------------------------------------------------
# Aggregation over the full H̄ (8 non-merge commits)
# ----------------------------------------------------------------------

def test_file_metrics_with_rename_continuity(full):
    main = full.files["src/main.py"]  # history of a.py follows the rename
    assert (main.added, main.removed) == (17, 4)
    assert main.churn == 21 and main.growth == 13
    assert main.modifications == 3  # c1, c2, c4
    assert main.by_author[ALICE].churn == 17
    assert main.by_author[BOB].churn == 4
    assert main.by_author[ALICE].modifications == 2


def test_deleted_file_keeps_its_path(full):
    readme = full.files["README.md"]
    assert (readme.added, readme.removed, readme.modifications) == (3, 3, 2)


def test_binary_and_renamed_away_paths_absent(full):
    assert "bin.dat" not in full.files
    assert "src/a.py" not in full.files
    assert "src/util/b.py" not in full.files


def test_pure_rename_is_not_a_modification(full):
    lib_b = full.files["src/lib/b.py"]
    assert (lib_b.added, lib_b.removed, lib_b.modifications) == (4, 0, 1)


def test_directory_aggregation(full):
    root, src, lib = full.directories[""], full.directories["src"], full.directories["src/lib"]
    assert (root.added, root.removed, root.churn) == (27, 7, 34)
    assert root.modifications == 6  # c1,c2,c4,c5,c7,c8 — not c3 (λ=0), not c6 (binary)
    # src = a.py/main.py history (17/4) + lib/b.py (+4) — all descendants
    assert (src.added, src.removed, src.modifications) == (21, 4, 3)
    assert (lib.added, lib.modifications) == (4, 1)
    assert "src/util" not in full.directories  # b.py's history moved to src/lib


def test_root_author_metrics(full):
    root = full.directories[""]
    alice, bob = root.by_author[ALICE], root.by_author[BOB]
    assert (alice.added, alice.removed, alice.churn, alice.modifications) == (24, 5, 29, 4)
    assert (bob.added, bob.removed, bob.churn, bob.modifications) == (3, 2, 5, 2)


# ----------------------------------------------------------------------
# Commit set selection (H_t, H_i,j, manual list)
# ----------------------------------------------------------------------

def test_since_inclusive(commits):
    result = compute_metrics(select_commits(commits, since=ts(4000)))
    assert result.commit_count == 5  # c4..c8
    assert result.directories[""].churn == 9  # 4+3+0+1+1


def test_until_exclusive(commits):
    result = compute_metrics(select_commits(commits, until=ts(4000)))
    assert result.commit_count == 3  # c1,c2,c3
    assert result.directories[""].churn == 25  # 13+12+0
    # the a.py -> main.py rename is outside the set: a.py keeps its own row
    assert result.files["src/a.py"].added == 15
    assert "src/main.py" not in result.files


def test_time_window(commits):
    result = compute_metrics(select_commits(commits, since=ts(2000), until=ts(6000)))
    assert result.commit_count == 4
    assert result.directories[""].churn == 19  # 12+0+4+3


def test_manual_commit_selection(commits):
    by_ts = {c.timestamp: c.sha for c in commits}
    result = compute_metrics(select_commits(commits, shas=[by_ts[4000], by_ts[5000]]))
    assert result.commit_count == 2
    root = result.directories[""]
    assert (root.added, root.removed, root.churn) == (2, 5, 7)
    assert result.files["src/main.py"].modifications == 1
