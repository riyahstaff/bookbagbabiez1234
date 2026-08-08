from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR.parent / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="ACS_", extra="ignore")

    database_url: str = f"sqlite:///{DATA_DIR / 'db.sqlite3'}"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    environment: str = "development"

    # "mock" (default, zero cost/setup) | "anthropic" | "openai_compatible"
    # (also covers local Ollama/vLLM - point OPENAI_BASE_URL at them)
    llm_creative_provider: str = "mock"
    llm_creative_model: str | None = None
    llm_mechanical_provider: str = "mock"
    llm_mechanical_model: str | None = None

    # "mock" (default, zero cost/setup, draws a real placeholder image) | "comfyui"
    image_provider: str = "mock"
    comfyui_base_url: str = "http://127.0.0.1:8188"

    # "mock" (default, zero cost/setup, writes a real placeholder WAV tone) | "openai_compatible"
    # (covers self-hosted Chatterbox/CosyVoice2/Qwen3-TTS servers exposing an
    # OpenAI-style /audio/speech endpoint, or real OpenAI TTS - point TTS_BASE_URL at it)
    voice_provider: str = "mock"
    voice_model: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
