from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR.parent / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="ACS_", extra="ignore")

    database_url: str = f"sqlite:///{DATA_DIR / 'db.sqlite3'}"
    cors_origins: list[str] = ["http://localhost:3000"]
    environment: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
