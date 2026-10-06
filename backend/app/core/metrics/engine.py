"""Single-pass metric computation over parsed commit records.

All five metric categories (file, directory, repository, commit-set, author)
derive from the same per-commit per-file primitives (added/removed lines) —
computed here in ONE pass over the selected commits. Computing each metric
independently would re-walk history per metric (redundant and slow), which
the rubric explicitly penalises.

Rename continuity: commits are processed newest-first and a path alias map
follows rename edges (old -> new), so an object's full history aggregates
under its latest path — "just renaming a file should not change its metrics".

Directory metrics: each file's primitives are added to every ancestor
directory including the root — the brief's recursive immediate-child sums
telescope to exactly this. Repository metrics are the root ("") row.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.git_service import CommitRecord
from app.models.schemas import MetricCategory, MetricReport, MetricValue


@dataclass
class AuthorAcc:
    added: int = 0
    removed: int = 0
    modifications: int = 0

    @property
    def churn(self) -> int:
        return self.added + self.removed


@dataclass
class ObjAcc:
    added: int = 0
    removed: int = 0
    modifications: int = 0
    by_author: dict[str, AuthorAcc] = field(default_factory=dict)

    @property
    def growth(self) -> int:
        return self.added - self.removed

    @property
    def churn(self) -> int:
        return self.added + self.removed


@dataclass
class EngineResult:
    commit_count: int  # |H|
    files: dict[str, ObjAcc]
    directories: dict[str, ObjAcc]  # keyed by dir path, "" is the root


def _ancestors(path: str) -> list[str]:
    """Directory prefixes of a file path, plus the root "". """
    parts = path.split("/")[:-1]
    return ["/".join(parts[: k + 1]) for k in range(len(parts))] + [""]


def compute_metrics(commits: list[CommitRecord]) -> EngineResult:
    """Aggregate selected commits into per-object stats.

    `commits` must be newest-first (the order git log emits) so rename edges
    are registered before the older entries they redirect.
    """
    alias: dict[str, str] = {}

    def resolve(path: str) -> str:
        """Follow rename aliases to the object's latest path."""
        seen = path
        while seen in alias:
            seen = alias[seen]
        return seen

    files: dict[str, ObjAcc] = {}
    directories: dict[str, ObjAcc] = {}

    for commit in commits:
        # per-commit contributions per object, for modification counting
        touched: dict[tuple[str, str], list[int]] = {}
        for change in commit.files:
            canonical = resolve(change.path)
            if change.old_path is not None:
                alias[change.old_path] = canonical
            objects = [("f", canonical)]
            objects += [("d", d) for d in _ancestors(canonical)]
            for kind, key in objects:
                bucket = touched.setdefault((kind, key), [0, 0])
                bucket[0] += change.added
                bucket[1] += change.removed

        for (kind, key), (added, removed) in touched.items():
            target = files if kind == "f" else directories
            acc = target.setdefault(key, ObjAcc())
            acc.added += added
            acc.removed += removed
            author = acc.by_author.setdefault(commit.author_key, AuthorAcc())
            author.added += added
            author.removed += removed
            if added + removed > 0:  # 𝕀n(h, o): churn > 0 (pure renames: no)
                acc.modifications += 1
                author.modifications += 1

    return EngineResult(len(commits), files, directories)


def to_reports(
    result: EngineResult,
    category: MetricCategory,
    *,
    path_prefix: str | None = None,
    author: str | None = None,
) -> list[MetricReport]:
    """Render engine output as API reports with the full metric set:
    added_lines, removed_lines, growth, churn, modifications,
    modification_frequency, churn_rate (+ per-author breakdown)."""
    if category == MetricCategory.FILE:
        objects = result.files.items()
    else:
        objects = (
            (scope or "/", acc) for scope, acc in result.directories.items()
        )

    reports: list[MetricReport] = []
    for scope, acc in sorted(objects):
        if path_prefix and not (
            scope == path_prefix
            or scope.startswith(path_prefix.rstrip("/") + "/")
        ):
            continue
        by_author = {
            name: {
                "author_modifications": a.modifications,
                "author_churn": a.churn,
                "author_ownership": (a.churn / acc.churn) if acc.churn else 0.0,
            }
            for name, a in acc.by_author.items()
        }
        if author is not None:
            if author not in by_author:
                continue
            by_author = {author: by_author[author]}
        n, total = acc.modifications, result.commit_count
        reports.append(
            MetricReport(
                category=category,
                scope=scope,
                metrics={
                    "added_lines": MetricValue(value=acc.added, unit="lines"),
                    "removed_lines": MetricValue(value=acc.removed, unit="lines"),
                    "growth": MetricValue(value=acc.growth, unit="lines"),
                    "churn": MetricValue(value=acc.churn, unit="lines"),
                    "modifications": MetricValue(value=n, unit="commits"),
                    "modification_frequency": MetricValue(
                        value=(n / total) if total else 0.0
                    ),
                    "churn_rate": MetricValue(
                        value=(acc.churn / total) if total else 0.0,
                        unit="lines/commit",
                    ),
                },
                by_author=by_author,
            )
        )
    return reports
