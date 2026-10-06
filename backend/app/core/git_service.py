"""All git interaction goes through GitService (backed by GitPython).

Responsibilities:
- ingestion: deep-clone a remote URL, or extract an uploaded zip that
  contains the `.git` directory
- introspection: commits, authors, trees and diffs consumed by the metric
  calculators and the author merger
"""

from pathlib import Path

from app.models.schemas import CommitInfo, MetricFilter


class GitService:
    def clone_repository(self, url: str, dest: Path) -> Path:
        """Deep-clone (full history — never `--depth`) `url` into `dest`."""
        # TODO: git.Repo.clone_from(url, dest) + validation
        raise NotImplementedError

    def extract_repository_zip(self, archive: Path, dest: Path) -> Path:
        """Extract an uploaded repository zip into `dest`.

        Must verify a `.git` directory is present; reject the upload
        otherwise (metrics need full history, not just a working tree).
        """
        # TODO: zipfile extraction + .git validation
        raise NotImplementedError

    def iter_commits(self, repo_path: Path, filters: MetricFilter) -> list[CommitInfo]:
        """Commits of the repository, narrowed by the shared filter
        (author / path / time range / explicit SHAs)."""
        # TODO: walk history via GitPython, apply services.filters
        raise NotImplementedError
