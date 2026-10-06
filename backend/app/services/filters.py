"""Commit selection shared by every metric query.

Selects the commit set H out of H̄ (the parsed non-merge commits):
- explicit `shas`  — manually selected list (takes precedence over time)
- `since` / `until` — H_t / H_i,j: since INCLUSIVE, until EXCLUSIVE
- neither          — H = H̄ (whole history reachable from the ref)

Author and path filtering happen at report level
(app.core.metrics.engine.to_reports), not here.
"""

from datetime import datetime

from app.core.git_service import CommitRecord


def select_commits(
    commits: list[CommitRecord],
    *,
    since: datetime | None = None,
    until: datetime | None = None,
    shas: list[str] | None = None,
) -> list[CommitRecord]:
    """Return the subset of `commits` (order preserved, newest first)."""
    if shas:
        wanted = set(shas)
        return [c for c in commits if c.sha in wanted]

    since_ts = since.timestamp() if since else None
    until_ts = until.timestamp() if until else None
    return [
        c
        for c in commits
        if (since_ts is None or since_ts <= c.timestamp)
        and (until_ts is None or c.timestamp < until_ts)
    ]
