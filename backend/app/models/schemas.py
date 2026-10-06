"""Domain models shared across the API.

Metric payloads are intentionally open-ended (`metrics: dict[str, MetricValue]`)
so new metric calculators can be added without changing the API contract.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Repositories
# ---------------------------------------------------------------------------

class RepositorySource(str, Enum):
    ZIP = "zip"
    URL = "url"


class RepositoryInfo(BaseModel):
    """A repository registered with RAT (multi-repository support)."""

    id: str
    name: str
    source: RepositorySource
    path: str  # on-disk location of the clone / extracted zip
    default_branch: str | None = None


class CloneRequest(BaseModel):
    """Body for POST /api/repositories/clone — deeply cloned, never shallow."""

    url: str


# ---------------------------------------------------------------------------
# Authors
# ---------------------------------------------------------------------------

class AuthorIdentity(BaseModel):
    """One raw (name, email) pair as it appears on commits."""

    name: str
    email: str


class Author(BaseModel):
    """A canonical author, possibly merged from several raw identities
    (via .mailmap and/or manual merging in the dashboard)."""

    id: str
    name: str
    email: str
    identities: list[AuthorIdentity] = Field(default_factory=list)


class MergeAuthorsRequest(BaseModel):
    """Body for POST /api/authors/merge.

    `canonical` optionally overrides the display name/email of the merged
    author; otherwise the mailmap (or most frequent identity) wins.
    """

    repository_id: str
    author_ids: list[str]
    canonical: AuthorIdentity | None = None


# ---------------------------------------------------------------------------
# Commits & filtering
# ---------------------------------------------------------------------------

class CommitInfo(BaseModel):
    sha: str
    author: AuthorIdentity
    timestamp: datetime
    message: str


class MetricFilter(BaseModel):
    """Shared filter applied to every metric query.

    Commit selection is either a time period (`since`/`until`) or a manually
    selected list of commit SHAs (`commits`).
    """

    repository_id: str
    author_id: str | None = None
    path: str | None = None  # file or directory prefix
    since: datetime | None = None
    until: datetime | None = None
    commits: list[str] | None = None


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

class MetricCategory(str, Enum):
    FILE = "file"
    DIRECTORY = "directory"
    REPOSITORY = "repository"
    COMMIT_SET = "commit_set"


class MetricValue(BaseModel):
    value: float | int
    unit: str | None = None
    description: str | None = None


class MetricReport(BaseModel):
    """One row in a metrics response: a scope (a file path, a directory path,
    the repository itself, or a commit set) plus its computed metrics."""

    category: MetricCategory
    scope: str
    metrics: dict[str, MetricValue] = Field(default_factory=dict)
