"""Author identity resolution — mailmap + manual merges.

Layer 1 — `.mailmap`: handled automatically by git itself. Our log format
uses `%aN`/`%aE` which already applies the repo's `.mailmap`, so every
CommitRecord.author_key is mailmap-resolved before we ever see it.

Layer 2 — manual merges: the user picks N author keys in the dashboard and
collapses them into one canonical identity. We store these per-repository
and apply them to commit records before the engine aggregates, so the
brief's `𝕀(a,h) := 1 if a = h[a]` checks authorship AFTER both layers.

The merge store is in-memory (dict); swap for JSON/SQLite if it needs to
survive restarts.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from pathlib import Path

from app.core.git_service import CommitRecord
from app.models.schemas import Author, AuthorIdentity


@dataclass
class MergeRule:
    canonical_name: str
    canonical_email: str
    source_keys: set[str]  # all author_keys that collapse into this one

    @property
    def canonical_key(self) -> str:
        return f"{self.canonical_name} <{self.canonical_email}>"


class AuthorMerger:
    """Per-repository author merge state."""

    def __init__(self) -> None:
        # repo_id -> list of merge rules
        self._rules: dict[str, list[MergeRule]] = {}

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def _lookup(self, repo_id: str) -> dict[str, MergeRule]:
        """Build {source_key -> rule} map for a repo."""
        out: dict[str, MergeRule] = {}
        for rule in self._rules.get(repo_id, []):
            for k in rule.source_keys:
                out[k] = rule
            out[rule.canonical_key] = rule
        return out

    def resolve_key(self, repo_id: str, author_key: str) -> str:
        """Resolve an author_key through manual merge rules."""
        table = self._lookup(repo_id)
        rule = table.get(author_key)
        return rule.canonical_key if rule else author_key

    # ------------------------------------------------------------------
    # Apply to commits (before engine aggregation)
    # ------------------------------------------------------------------

    def apply(self, repo_id: str, commits: list[CommitRecord]) -> list[CommitRecord]:
        """Return commits with author identities resolved through merge rules.

        Returns new CommitRecord objects (the cached originals are not mutated).
        If no rules exist for this repo, the original list is returned as-is
        (zero-copy fast path).
        """
        table = self._lookup(repo_id)
        if not table:
            return commits
        out: list[CommitRecord] = []
        for c in commits:
            rule = table.get(c.author_key)
            if rule and (c.author_name != rule.canonical_name or c.author_email != rule.canonical_email):
                out.append(replace(c, author_name=rule.canonical_name, author_email=rule.canonical_email))
            else:
                out.append(c)
        return out

    # ------------------------------------------------------------------
    # List authors (after mailmap + manual merges)
    # ------------------------------------------------------------------

    def list_authors(self, repo_id: str, commits: list[CommitRecord]) -> list[Author]:
        """Unique canonical authors from the commit history, with their
        constituent raw identities collected."""
        table = self._lookup(repo_id)
        # canonical_key -> set of (name, email)
        groups: dict[str, set[tuple[str, str]]] = {}
        canonical_info: dict[str, tuple[str, str]] = {}
        for c in commits:
            raw = (c.author_name, c.author_email)
            rule = table.get(c.author_key)
            if rule:
                ckey = rule.canonical_key
                canonical_info[ckey] = (rule.canonical_name, rule.canonical_email)
            else:
                ckey = c.author_key
                canonical_info.setdefault(ckey, raw)
            groups.setdefault(ckey, set()).add(raw)

        authors: list[Author] = []
        for ckey, identities in sorted(groups.items()):
            cn, ce = canonical_info[ckey]
            authors.append(
                Author(
                    id=_author_id(ckey),
                    name=cn,
                    email=ce,
                    identities=[
                        AuthorIdentity(name=n, email=e) for n, e in sorted(identities)
                    ],
                )
            )
        return authors

    # ------------------------------------------------------------------
    # Manual merge CRUD
    # ------------------------------------------------------------------

    def add_merge(
        self,
        repo_id: str,
        source_keys: list[str],
        canonical: AuthorIdentity | None = None,
    ) -> MergeRule:
        """Merge `source_keys` into one author. If `canonical` is None, the
        first key's identity is used."""
        if len(source_keys) < 2:
            raise ValueError("Need at least two authors to merge")

        # Determine canonical identity
        if canonical:
            cname, cemail = canonical.name, canonical.email
        else:
            # Use the first key: "Name <email>" -> parse
            first = source_keys[0]
            cname, cemail = _parse_author_key(first)

        new_key = f"{cname} <{cemail}>"

        # Absorb any existing rules that overlap with source_keys
        existing = self._rules.setdefault(repo_id, [])
        all_sources: set[str] = set(source_keys)
        kept: list[MergeRule] = []
        for rule in existing:
            if rule.canonical_key in all_sources or rule.source_keys & all_sources:
                all_sources |= rule.source_keys
                all_sources.add(rule.canonical_key)
            else:
                kept.append(rule)
        # The canonical key itself shouldn't be in source_keys
        all_sources.discard(new_key)

        new_rule = MergeRule(cname, cemail, all_sources)
        kept.append(new_rule)
        self._rules[repo_id] = kept
        return new_rule

    def remove_merge(self, repo_id: str, author_key: str) -> None:
        """Remove the merge rule that contains `author_key`."""
        existing = self._rules.get(repo_id, [])
        self._rules[repo_id] = [
            r for r in existing
            if author_key not in r.source_keys and r.canonical_key != author_key
        ]


def _author_id(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()[:12]


def _parse_author_key(key: str) -> tuple[str, str]:
    """'Name <email>' -> (name, email)."""
    if " <" in key and key.endswith(">"):
        name, rest = key.rsplit(" <", 1)
        return name, rest[:-1]
    return key, ""


# Shared singleton
author_merger = AuthorMerger()
