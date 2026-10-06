"""Metric query endpoints — one per metric category.

All endpoints share the same filter surface (repository, author, path, time
range, explicit commit list) and discover their calculators from the metric
registry in app.core.metrics.base, so new metrics appear here automatically.
"""

from datetime import datetime

from fastapi import APIRouter, Query

from app.models.schemas import MetricReport

router = APIRouter()


def _build_filter(
    repository_id: str,
    author_id: str | None,
    path: str | None,
    since: datetime | None,
    until: datetime | None,
    commits: list[str] | None,
):
    """Assemble the shared MetricFilter from query parameters."""
    from app.models.schemas import MetricFilter

    return MetricFilter(
        repository_id=repository_id,
        author_id=author_id,
        path=path,
        since=since,
        until=until,
        commits=commits,
    )


@router.get("/files", response_model=list[MetricReport])
def file_metrics(
    repository_id: str = Query(...),
    author_id: str | None = None,
    path: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    commits: list[str] | None = Query(None),
) -> list[MetricReport]:
    """Per-file metrics for the filtered scope."""
    # TODO: run registered FILE calculators via core.metrics.base.list_metrics
    _build_filter(repository_id, author_id, path, since, until, commits)
    return []


@router.get("/directories", response_model=list[MetricReport])
def directory_metrics(
    repository_id: str = Query(...),
    author_id: str | None = None,
    path: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    commits: list[str] | None = Query(None),
) -> list[MetricReport]:
    """Per-directory metrics for the filtered scope."""
    # TODO: run registered DIRECTORY calculators
    _build_filter(repository_id, author_id, path, since, until, commits)
    return []


@router.get("/repository", response_model=list[MetricReport])
def repository_metrics(
    repository_id: str = Query(...),
    author_id: str | None = None,
    path: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    commits: list[str] | None = Query(None),
) -> list[MetricReport]:
    """Whole-repository metrics for the filtered scope."""
    # TODO: run registered REPOSITORY calculators
    _build_filter(repository_id, author_id, path, since, until, commits)
    return []


@router.get("/commit-set", response_model=list[MetricReport])
def commit_set_metrics(
    repository_id: str = Query(...),
    author_id: str | None = None,
    path: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    commits: list[str] | None = Query(None),
) -> list[MetricReport]:
    """Metrics over a set of commits — a time period or a manual selection."""
    # TODO: run registered COMMIT_SET calculators
    _build_filter(repository_id, author_id, path, since, until, commits)
    return []
