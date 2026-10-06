"""All git interaction: ingestion (clone / zip) and history parsing.

History is read with ONE git command per (repo, ref):

    git log --no-merges -M50 --numstat -z \\
        --format=tformat:%x1e%H%x09%ct%x09%aN%x09%aE <ref>

yielding, per non-merge commit: sha, committer UNIX date, mailmap-resolved
author name/email (%aN/%aE honour .mailmap) and per-file added/removed lines.
Verified byte format (see backend/tests/test_engine.py):

    \\x1e <sha> TAB <ct> TAB <name> TAB <email> NUL \\n
    <added> TAB <removed> TAB <path> NUL                      (regular entry)
    <added> TAB <removed> TAB NUL <old> NUL <new> NUL         (rename entry)

Binary files show '-' for added/removed and are skipped (not measured).
Pure renames contribute 0/0 on the new path; deletions 0/removed on the
deleted path. Merge commits are excluded (H̄ is non-merge commits only).
"""

from __future__ import annotations

import shutil
import subprocess
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

_COMMIT_SEP = b"\x1e"
_LOG_FORMAT = "tformat:%x1e%H%x09%ct%x09%aN%x09%aE"


class GitError(RuntimeError):
    """Raised for any git ingestion/parsing failure (mapped to HTTP 400)."""


@dataclass
class FileChange:
    path: str  # current (post-rename) path
    added: int
    removed: int
    old_path: str | None = None  # set when this entry is a rename


@dataclass
class CommitRecord:
    sha: str
    timestamp: int  # committer date, UNIX seconds
    author_name: str
    author_email: str
    files: list[FileChange] = field(default_factory=list)

    @property
    def author_key(self) -> str:
        """Canonical identity key (mailmap already applied by git)."""
        return f"{self.author_name} <{self.author_email}>"


def parse_log(output: bytes) -> list[CommitRecord]:
    """Parse the -z numstat stream into commit records (newest first)."""
    commits: list[CommitRecord] = []
    for block in output.split(_COMMIT_SEP):
        if not block.strip():
            continue
        fields = block.split(b"\0")
        parts = fields[0].strip(b"\n").split(b"\t")
        if len(parts) < 4:
            continue  # malformed header — skip block
        sha = parts[0].decode()
        timestamp = int(parts[1])
        email = parts[-1].decode("utf-8", "replace")
        name = b"\t".join(parts[2:-1]).decode("utf-8", "replace")

        files: list[FileChange] = []
        i = 1
        while i < len(fields):
            entry = fields[i].lstrip(b"\n")
            i += 1
            if not entry:
                continue
            cols = entry.split(b"\t", 2)
            if len(cols) != 3:
                continue
            added_s, removed_s, rest = cols
            old_path: str | None = None
            if rest == b"":  # rename entry: next two fields are old/new path
                if i + 1 >= len(fields):
                    break
                old_path = fields[i].decode("utf-8", "replace")
                path_s = fields[i + 1].decode("utf-8", "replace")
                i += 2
            else:
                path_s = rest.decode("utf-8", "replace")
            if added_s == b"-":  # binary file — not measured
                continue
            files.append(
                FileChange(
                    path=path_s,
                    added=int(added_s),
                    removed=int(removed_s),
                    old_path=old_path,
                )
            )
        commits.append(CommitRecord(sha, timestamp, name, email, files))
    return commits


class GitService:
    """Ingestion and history access. Parsed logs are cached in memory per
    (repo, ref); disk caching is a later performance pass."""

    def __init__(self) -> None:
        self._log_cache: dict[tuple[str, str], list[CommitRecord]] = {}

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def clone_repository(self, url: str, dest: Path) -> Path:
        """Deep-clone (full history — no --depth) `url` into `dest`."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            ["git", "clone", url, str(dest)], capture_output=True
        )
        if proc.returncode != 0:
            raise GitError(proc.stderr.decode("utf-8", "replace").strip())
        return dest

    def extract_repository_zip(self, archive: Path, dest: Path) -> Path:
        """Extract an uploaded repo zip into `dest` and return the repo root
        (the directory containing `.git`). Rejects zips without `.git`."""
        dest.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(archive) as zf:
                for member in zf.namelist():
                    p = Path(member)
                    if p.is_absolute() or ".." in p.parts:
                        raise GitError(f"Unsafe path in zip: {member}")
                zf.extractall(dest)
        except zipfile.BadZipFile as exc:
            raise GitError("Uploaded file is not a valid zip archive") from exc

        candidates = [dest]
        top = [p for p in dest.iterdir() if p.is_dir()]
        if len(top) == 1:
            candidates.append(top[0])  # zips usually wrap everything in one dir
        for candidate in candidates:
            if (candidate / ".git").exists():
                self._run_git(candidate, ["rev-parse", "--git-dir"])  # validate
                return candidate
        raise GitError("Zip does not contain a .git directory — full history required")

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def iter_commits(self, repo_path: Path, ref: str = "HEAD") -> list[CommitRecord]:
        """Non-merge commits reachable from `ref`, newest first, with per-file
        added/removed lines (cached per repo+ref)."""
        key = (str(repo_path), ref)
        if key not in self._log_cache:
            out = self._run_git(
                repo_path,
                ["log", "--no-merges", "-M50", "--numstat", "-z",
                 f"--format={_LOG_FORMAT}", ref],
            )
            self._log_cache[key] = parse_log(out)
        return self._log_cache[key]

    def default_branch(self, repo_path: Path) -> str:
        out = self._run_git(repo_path, ["rev-parse", "--abbrev-ref", "HEAD"])
        return out.decode().strip()

    # ------------------------------------------------------------------

    @staticmethod
    def _run_git(repo: Path, args: list[str]) -> bytes:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True
        )
        if proc.returncode != 0:
            raise GitError(
                f"git {' '.join(args)} failed: "
                f"{proc.stderr.decode('utf-8', 'replace').strip()}"
            )
        return proc.stdout


# Shared instance used by the API layer.
git_service = GitService()
