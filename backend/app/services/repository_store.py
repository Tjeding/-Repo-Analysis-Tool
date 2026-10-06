"""Registry of ingested repositories (multi-repository support).

Currently in-memory; swap for a small on-disk index (JSON/SQLite) if
registrations should survive restarts.
"""

from app.models.schemas import RepositoryInfo


class RepositoryStore:
    def __init__(self) -> None:
        self._repositories: dict[str, RepositoryInfo] = {}

    def add(self, repo: RepositoryInfo) -> RepositoryInfo:
        self._repositories[repo.id] = repo
        return repo

    def get(self, repository_id: str) -> RepositoryInfo | None:
        return self._repositories.get(repository_id)

    def list(self) -> list[RepositoryInfo]:
        return list(self._repositories.values())

    def remove(self, repository_id: str) -> None:
        self._repositories.pop(repository_id, None)


# Shared instance used by the API layer.
store = RepositoryStore()
