"""Application settings.

Every field can be overridden with an environment variable prefixed `RAT_`,
e.g. `RAT_STORAGE_DIR=/var/rat/repos`.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RAT_", env_file=".env")

    app_name: str = "RAT — Repo Analysis Tool"
    version: str = "0.1.0"

    # Where ingested repositories (clones / extracted zips) are stored.
    storage_dir: Path = Path(__file__).resolve().parent.parent / "data" / "repositories"

    # Dashboard dev server origin(s).
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
