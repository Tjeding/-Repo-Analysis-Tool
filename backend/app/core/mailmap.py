"""Author identity resolution.

The same person often commits under several names/emails. Two sources of
truth are applied, in order:

1. the repository's `.mailmap` file (git's canonical mapping — automatic)
2. manual merges chosen by the user in the dashboard (stored overrides)

See https://git-scm.com/docs/gitmailmap for the mailmap format.
"""

from pathlib import Path

from app.models.schemas import Author, AuthorIdentity


class AuthorMerger:
    """Maps raw (name, email) identities onto canonical authors."""

    def load_mailmap(self, repo_path: Path) -> None:
        """Parse the repository's `.mailmap`, if present."""
        # TODO: parse mailmap entries into a lookup table
        raise NotImplementedError

    def resolve(self, identities: list[AuthorIdentity]) -> list[Author]:
        """Collapse raw identities into canonical authors using the loaded
        mailmap plus any persisted manual merges."""
        # TODO
        raise NotImplementedError

    def apply_manual_merge(self, author_ids: list[str]) -> Author:
        """Merge canonical authors selected by the user into one."""
        # TODO: persist the override so metric queries stay consistent
        raise NotImplementedError
