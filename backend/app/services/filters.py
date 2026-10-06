"""Commit filtering shared by every metric query.

Filter dimensions (all optional, combined):
- author        — canonical (merged) author id
- path          — file or directory prefix
- time period   — `since` / `until`
- commit list   — manually selected SHAs (takes precedence over time period)
"""

from app.models.schemas import CommitInfo, MetricFilter


def filter_commits(commits: list[CommitInfo], filters: MetricFilter) -> list[CommitInfo]:
    """Return only the commits matching the filter."""
    # TODO: implement the four filter dimensions above
    raise NotImplementedError
