"""Repository ingestion and registry endpoints (multi-repository support)."""

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.schemas import CloneRequest, RepositoryInfo

router = APIRouter()


@router.get("", response_model=list[RepositoryInfo])
def list_repositories() -> list[RepositoryInfo]:
    """List every repository ingested so far."""
    # TODO: serve from services.repository_store.RepositoryStore
    return []


@router.post("/upload", response_model=RepositoryInfo, status_code=201)
def upload_repository(file: UploadFile = File(...)) -> RepositoryInfo:
    """Ingest a zip archive of a repository. The zip must contain the `.git`
    directory so full history is available."""
    # TODO: core.git_service.GitService.extract_repository_zip + register
    raise HTTPException(status_code=501, detail="Zip ingestion not implemented yet")


@router.post("/clone", response_model=RepositoryInfo, status_code=201)
def clone_repository(payload: CloneRequest) -> RepositoryInfo:
    """Deep-clone (full history) a remote repository by URL."""
    # TODO: core.git_service.GitService.clone_repository + register
    raise HTTPException(status_code=501, detail="Clone ingestion not implemented yet")
