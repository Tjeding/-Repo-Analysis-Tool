"""Author listing and merging endpoints.

Identity resolution order:
1. `.mailmap` — applied automatically by git (%aN/%aE) at parse time
2. manual merges — performed here, persisted per repo in AuthorMerger
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from app.api.routes.repositories import _get_repo
from app.core.git_service import GitError, git_service
from app.core.mailmap import _author_id, author_merger
from app.models.schemas import Author, AuthorIdentity, MergeAuthorsRequest

router = APIRouter()


@router.get("", response_model=list[Author])
def list_authors(
    repository_id: str = Query(...),
    ref: str = "HEAD",
) -> list[Author]:
    """List canonical (mailmap- and merge-resolved) authors of a repository."""
    repo = _get_repo(repository_id)
    try:
        commits = git_service.iter_commits(Path(repo.path), ref)
    except GitError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return author_merger.list_authors(repository_id, commits)


@router.post("/merge", response_model=Author)
def merge_authors(payload: MergeAuthorsRequest) -> Author:
    """Manually merge several author identities into one canonical author.

    `author_ids` are author_key strings of the form "Name <email>".
    `canonical` optionally overrides the display name/email; otherwise the
    first identity is used.
    """
    repo = _get_repo(payload.repository_id)
    if len(payload.author_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least two authors to merge")
    try:
        rule = author_merger.add_merge(
            payload.repository_id,
            payload.author_ids,
            payload.canonical,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Invalidate any cached engine results for this repo (merges change author attribution)
    git_service.invalidate_cache_for_repo(str(repo.path))

    return Author(
        id=_author_id(rule.canonical_key),
        name=rule.canonical_name,
        email=rule.canonical_email,
        identities=[
            AuthorIdentity(
                name=k.rsplit(" <", 1)[0] if " <" in k else k,
                email=k.rsplit(" <", 1)[1][:-1] if " <" in k else "",
            )
            for k in sorted(rule.source_keys | {rule.canonical_key})
        ],
    )


@router.post("/unmerge", status_code=204)
def unmerge_author(
    repository_id: str = Query(...),
    author_key: str = Query(...),
) -> None:
    """Remove a previously created manual merge that contains `author_key`."""
    _get_repo(repository_id)  # validate exists
    author_merger.remove_merge(repository_id, author_key)
