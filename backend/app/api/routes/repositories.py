"""Repository ingestion and registry endpoints (multi-repository support)."""

import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.config import settings
from app.core.git_service import GitError, git_service
from app.models.schemas import (
    AuthorIdentity,
    CloneRequest,
    CommitInfo,
    RepositoryInfo,
    RepositorySource,
)
from app.services.repository_store import store

router = APIRouter()


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "repo"


def _register(name: str, source: RepositorySource, path: Path) -> RepositoryInfo:
    repo_id = f"{_slug(name)}-{uuid.uuid4().hex[:8]}"
    info = RepositoryInfo(
        id=repo_id,
        name=name,
        source=source,
        path=str(path),
        default_branch=git_service.default_branch(path),
    )
    return store.add(info)


def _get_repo(repository_id: str) -> RepositoryInfo:
    repo = store.get(repository_id)
    if repo is None:
        raise HTTPException(status_code=404, detail=f"Unknown repository: {repository_id}")
    return repo


@router.get("", response_model=list[RepositoryInfo])
def list_repositories() -> list[RepositoryInfo]:
    """List every repository ingested so far."""
    return store.list()


@router.post("/upload", response_model=RepositoryInfo, status_code=201)
def upload_repository(file: UploadFile = File(...)) -> RepositoryInfo:
    """Ingest a zip archive of a repository. The zip must contain the `.git`
    directory so full history is available."""
    if not (file.filename or "").endswith(".zip"):
        raise HTTPException(status_code=400, detail="Upload must be a .zip file")

    work_dir = settings.storage_dir / f"upload-{uuid.uuid4().hex[:8]}"
    archive = work_dir / "upload.zip"
    try:
        work_dir.mkdir(parents=True, exist_ok=True)
        with archive.open("wb") as out:
            shutil.copyfileobj(file.file, out)
        repo_root = git_service.extract_repository_zip(archive, work_dir / "repo")
    except GitError as exc:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        archive.unlink(missing_ok=True)

    return _register(Path(file.filename).stem, RepositorySource.ZIP, repo_root)


@router.post("/clone", response_model=RepositoryInfo, status_code=201)
def clone_repository(payload: CloneRequest) -> RepositoryInfo:
    """Deep-clone (full history) a remote repository by URL."""
    name = Path(payload.url.rstrip("/")).stem.removesuffix(".git") or "repo"
    dest = settings.storage_dir / f"{_slug(name)}-{uuid.uuid4().hex[:8]}"
    try:
        git_service.clone_repository(payload.url, dest)
    except GitError as exc:
        shutil.rmtree(dest, ignore_errors=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _register(name, RepositorySource.URL, dest)


@router.get("/{repository_id}/commits", response_model=list[CommitInfo])
def list_commits(
    repository_id: str, ref: str = Query("HEAD")
) -> list[CommitInfo]:
    """Non-merge commits reachable from `ref` — feeds the dashboard's manual
    commit picker."""
    repo = _get_repo(repository_id)
    try:
        commits = git_service.iter_commits(Path(repo.path), ref)
    except GitError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [
        CommitInfo(
            sha=c.sha,
            author=AuthorIdentity(name=c.author_name, email=c.author_email),
            timestamp=datetime.fromtimestamp(c.timestamp, tz=timezone.utc),
            message="",  # not parsed from the numstat stream
        )
        for c in commits
    ]
