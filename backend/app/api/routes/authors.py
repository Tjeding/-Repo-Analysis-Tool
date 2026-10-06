"""Author listing and merging endpoints.

Identity resolution order:
1. the repository's `.mailmap` (applied automatically on ingestion)
2. manual merges performed here (user overrides)
"""

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import Author, MergeAuthorsRequest

router = APIRouter()


@router.get("", response_model=list[Author])
def list_authors(repository_id: str = Query(...)) -> list[Author]:
    """List canonical (mailmap- and merge-resolved) authors of a repository."""
    # TODO: core.mailmap.AuthorMerger over the repo's commit history
    return []


@router.post("/merge", response_model=Author)
def merge_authors(payload: MergeAuthorsRequest) -> Author:
    """Manually merge several author identities into one canonical author."""
    # TODO: persist the merge so subsequent metric queries use it
    raise HTTPException(status_code=501, detail="Manual author merging not implemented yet")
