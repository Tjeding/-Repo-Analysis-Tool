"""Shared fixtures: a synthetic repo exercising every parsing edge case
(rename, rename+modify, binary, deletion, merge, mailmap, fixed dates)
and a session-scoped storage dir so tests never touch real ingested data.
"""

import os
import subprocess
from pathlib import Path

import pytest

from app.config import settings

ALICE = ("Alice", "alice@example.com")
ALICE_WORK = ("Alice", "alice@work.com")  # mailmapped -> ALICE
BOB = ("Bob", "bob@example.com")


def _git(repo: Path, *args: str, who: tuple[str, str] = ALICE, date: int | None = None) -> None:
    env = os.environ.copy()
    env.update(
        GIT_AUTHOR_NAME=who[0],
        GIT_AUTHOR_EMAIL=who[1],
        GIT_COMMITTER_NAME=who[0],
        GIT_COMMITTER_EMAIL=who[1],
    )
    if date is not None:
        env["GIT_AUTHOR_DATE"] = f"@{date} +0000"
        env["GIT_COMMITTER_DATE"] = f"@{date} +0000"
    subprocess.run(
        ["git", "-C", str(repo), *args], env=env, check=True, capture_output=True
    )


def _write(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


@pytest.fixture(scope="session")
def synthetic_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """History (committer dates t=1000..9000, merge excluded from H̄):

    c1 1000 Alice      add src/a.py(10), README.md(3), bin.dat(binary)
    c2 2000 Alice@work a.py +5/-2, add src/util/b.py(4), add .mailmap(1)
    c3 3000 Alice      pure rename b.py -> src/lib/b.py
    c4 4000 Bob        rename+modify a.py -> src/main.py (+2/-2)
    c5 5000 Alice      delete README.md (-3)
    c6 6000 Bob        binary-only change on bin.dat
    c7 7000 Alice      (feature branch) add feat.txt(1)
    c8 8000 Bob        (main) add main.txt(1)
       9000            merge commit (excluded from H̄)
    """
    repo = tmp_path_factory.mktemp("synthetic") / "repo"
    repo.mkdir(parents=True)
    _git(repo, "init", "-q")

    # c1
    _write(repo / "src/a.py", [f"l{i}" for i in range(1, 11)])
    _write(repo / "README.md", ["r1", "r2", "r3"])
    (repo / "bin.dat").write_bytes(b"a\0b\0c\0")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "c1 initial", who=ALICE, date=1000)

    # c2 (work identity, resolved via .mailmap committed in this commit)
    _write(repo / "src/a.py", [f"l{i}" for i in range(3, 16)])
    _write(repo / "src/util/b.py", ["b1", "b2", "b3", "b4"])
    _write(repo / ".mailmap", ["Alice <alice@example.com> <alice@work.com>"])
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "c2 modify a, add b, mailmap", who=ALICE_WORK, date=2000)

    # c3 pure rename
    (repo / "src/lib").mkdir()
    _git(repo, "mv", "src/util/b.py", "src/lib/b.py")
    _git(repo, "commit", "-qm", "c3 pure rename b", who=ALICE, date=3000)

    # c4 rename + modify (2 removed, 2 added, >50% similar)
    _write(repo / "src/main.py", [f"l{i}" for i in range(3, 14)] + ["X1", "X2"])
    _git(repo, "rm", "-q", "src/a.py")
    _git(repo, "add", "src/main.py")
    _git(repo, "commit", "-qm", "c4 rename+modify a->main", who=BOB, date=4000)

    # c5 deletion
    _git(repo, "rm", "-q", "README.md")
    _git(repo, "commit", "-qm", "c5 delete readme", who=ALICE, date=5000)

    # c6 binary-only change
    (repo / "bin.dat").write_bytes(b"x\0y\0z\0w\0")
    _git(repo, "add", "bin.dat")
    _git(repo, "commit", "-qm", "c6 binary change", who=BOB, date=6000)

    # c7 on feature branch, c8 on main, then a merge (excluded)
    _git(repo, "checkout", "-qb", "feature")
    _write(repo / "feat.txt", ["f1"])
    _git(repo, "add", "feat.txt")
    _git(repo, "commit", "-qm", "c7 feat", who=ALICE, date=7000)
    _git(repo, "checkout", "-q", "master")
    _write(repo / "main.txt", ["m1"])
    _git(repo, "add", "main.txt")
    _git(repo, "commit", "-qm", "c8 main", who=BOB, date=8000)
    _git(repo, "merge", "-q", "--no-ff", "feature", "-m", "merge", date=9000)

    return repo


@pytest.fixture(scope="session", autouse=True)
def isolated_storage(tmp_path_factory: pytest.TempPathFactory):
    """Redirect ingestion storage to a session temp dir."""
    settings.storage_dir = tmp_path_factory.mktemp("storage") / "repositories"
