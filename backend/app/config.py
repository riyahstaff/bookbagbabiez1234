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
    # (also covers local Ollama/vLLM - point OPENAI_BASE_URL at them) | "auto"
    # (tries whichever of ANTHROPIC_API_KEY/OPENAI_API_KEY is actually set and
    # cheaper for this specific prompt first, falling back to the other one
    # if it errors - needs at least one of those two keys; see the cost
    # settings below to rank them)
    llm_creative_provider: str = "mock"
    llm_creative_model: str | None = None
    llm_mechanical_provider: str = "mock"
    llm_mechanical_model: str | None = None
    # Only used by "auto" above, to rank candidate providers by this specific
    # request's estimated cost - not exact billing, just enough to pick the
    # cheaper of two. The Anthropic figure is Claude Sonnet 5's real output
    # price ($15/million tokens) as of mid-2026; the OpenAI figure for
    # gpt-4o-mini is a rough estimate, not verified against a current
    # pricing page - check both against your own provider dashboards and
    # override here if either has drifted.
    llm_anthropic_cost_per_1k_tokens: float = 0.015
    llm_openai_cost_per_1k_tokens: float = 0.0006

    # "mock" (default, zero cost/setup, draws a real placeholder image) |
    # "comfyui" (self-hosted) | "fal" (hosted, pay-per-call - needs FAL_KEY)
    image_provider: str = "mock"
    comfyui_base_url: str = "http://127.0.0.1:8188"

    # "mock" (default, zero cost/setup, writes a real placeholder WAV tone) |
    # "openai_compatible" (covers self-hosted Chatterbox/CosyVoice2/Qwen3-TTS
    # servers exposing an OpenAI-style /audio/speech endpoint, or real OpenAI
    # TTS - point TTS_BASE_URL at it) | "fal" (hosted Chatterbox - needs FAL_KEY)
    voice_provider: str = "mock"
    voice_model: str | None = None

    # "mock" (default, zero cost/setup, animates the reference image into a
    # real placeholder GIF) | "comfyui" (self-hosted Wan2.2-TI2V-5B, reuses
    # comfyui_base_url) | "fal" (hosted Wan2.2-TI2V-5B - needs FAL_KEY)
    video_provider: str = "mock"

    # "mock" (default, zero cost/setup, returns the video untouched) | "fal"
    # (hosted MuseTalk by default, LatentSync for quality mode - needs FAL_KEY)
    lipsync_provider: str = "mock"
    lipsync_quality_mode: bool = False

    # "mock" (default, zero cost/setup, chroma-keys a solid corner color) |
    # "fal" (hosted BiRefNet - needs FAL_KEY). Only used by the
    # multi-character compositing pipeline (pipeline/compositing.py) to cut
    # out each character generated on a plain background before pasting them
    # onto a shared scene background - single-character shots never call it.
    background_removal_provider: str = "mock"


@lru_cache
def get_settings() -> Settings:
    return Settings()
