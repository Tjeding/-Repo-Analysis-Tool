"""Metric query endpoints — one per metric category.

All endpoints share the same filter surface (ref, author, path, time range,
explicit commit list). Every category is served from ONE cached git-log
parse and ONE aggregation pass (app.core.metrics.engine), so filtering is
cheap and never re-walks the repository.
"""

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from app.api.routes.repositories import _get_repo
from app.core.git_service import GitError, git_service
from app.core.mailmap import author_merger
from app.core.metrics.engine import EngineResult, compute_metrics, to_reports
from app.models.schemas import MetricCategory, MetricReport
from app.services.filters import select_commits

router = APIRouter()


def _run(
    repository_id: str,
    ref: str,
    since: datetime | None,
    until: datetime | None,
    commits: list[str] | None,
) -> EngineResult:
    """Parse (cached) -> apply manual author merges -> select H -> aggregate."""
    repo = _get_repo(repository_id)
    try:
        history = git_service.iter_commits(Path(repo.path), ref)
    except GitError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    merged = author_merger.apply(repository_id, history)
    selected = select_commits(merged, since=since, until=until, shas=commits)
    return compute_metrics(selected)


@router.get("/files", response_model=list[MetricReport])
def file_metrics(
    repository_id: str = Query(...),
    ref: str = "HEAD",
    author_id: str | None = None,
    path: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    commits: list[str] | None = Query(None),
) -> list[MetricReport]:
    """Per-file metrics over the selected commit set. Only files with
    activity in the set appear (untouched files are all-zero by definition)."""
    result = _run(repository_id, ref, since, until, commits)
    return to_reports(result, MetricCategory.FILE, path_prefix=path, author=author_id)


@router.get("/directories", response_model=list[MetricReport])
def directory_metrics(
    repository_id: str = Query(...),
    ref: str = "HEAD",
    author_id: str | None = None,
    path: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    commits: list[str] | None = Query(None),
) -> list[MetricReport]:
    """Per-directory metrics over the selected commit set (root is "/")."""
    result = _run(repository_id, ref, since, until, commits)
    return to_reports(
        result, MetricCategory.DIRECTORY, path_prefix=path, author=author_id
    )


@router.get("/repository", response_model=list[MetricReport])
def repository_metrics(
    repository_id: str = Query(...),
    ref: str = "HEAD",
    author_id: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    commits: list[str] | None = Query(None),
) -> list[MetricReport]:
    """Whole-repository metrics: directory metrics on the tree root."""
    result = _run(repository_id, ref, since, until, commits)
    report = to_reports(result, MetricCategory.REPOSITORY, author=author_id)
    return [r for r in report if r.scope == "/"]


@router.get("/commit-set", response_model=list[MetricReport])
def commit_set_metrics(
    repository_id: str = Query(...),
    ref: str = "HEAD",
    author_id: str | None = None,
    path: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    commits: list[str] | None = Query(None),
) -> list[MetricReport]:
    """Metrics over a set of commits — a time period or a manual selection —
    for every object (files + directories incl. root) in that set."""
    result = _run(repository_id, ref, since, until, commits)
    dir_reports = to_reports(
        result, MetricCategory.COMMIT_SET, path_prefix=path, author=author_id
    )
    file_reports = to_reports(
        result, MetricCategory.FILE, path_prefix=path, author=author_id
    )
    for r in file_reports:
        r.category = MetricCategory.COMMIT_SET
    return dir_reports + file_reports
