"""Application settings, loaded from environment variables / .env."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "GameCraft AI API"
    api_version: str = "1.0.0"
    environment: Literal["development", "test", "production"] = "development"

    # --- AI provider -------------------------------------------------------
    # auto   -> Gemini if GEMINI_API_KEY is set, otherwise the offline mock
    # gemini -> Gemini only (fails at startup without a key)
    # mock   -> offline placeholder provider (no network, no key)
    ai_provider: Literal["auto", "gemini", "mock"] = "auto"
    gemini_api_key: str = ""
    # Model IDs are configurable because preview model names change often.
    # Verify these against the Gemini model list for your account.
    thinking_model: str = "gemini-3.1-pro-preview"
    fallback_model: str = "gemini-3.8-flash"
    image_model: str = "gemini-3.1-flash-lite-image"
    ai_timeout_seconds: float = 90.0
    ai_max_retries: int = 2
    ai_retry_base_delay: float = 1.0
    max_parallel_generations: int = 3

    # --- Persistence -------------------------------------------------------
    database_url: str = "sqlite:///./data/gamecraft.db"
    storage_dir: Path = Path("./data/storage")

    # --- HTTP --------------------------------------------------------------
    # Comma-separated list of allowed browser origins.
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    rate_limit_per_minute: int = 20  # per client IP on generation routes; 0 disables
    max_batch_size: int = 8

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
