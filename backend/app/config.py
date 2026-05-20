"""Application configuration, loaded from the environment and the .env file."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# The repository root is three levels up from this file
# (backend/app/config.py -> backend/app -> backend -> repo root).
_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Settings read from environment variables, with the repo-root .env as a fallback.

    Real environment variables take precedence over the .env file. That is what
    lets the Docker container use the values from docker-compose.yml while a host
    process reads the same names from .env.
    """

    model_config = SettingsConfigDict(
        env_file=_REPO_ROOT / ".env",
        extra="ignore",
    )

    database_url: str
    log_level: str = "INFO"
    frontend_origin: str = "http://localhost:5173"


settings = Settings()
