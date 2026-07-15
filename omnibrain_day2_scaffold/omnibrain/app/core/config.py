"""
Centralized configuration for the OmniBrain backend.
Values are loaded from environment variables / a local .env file.
See .env.example for the full list of supported settings.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App ---
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # --- Qdrant ---
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_text_collection: str = "omnibrain_text"
    qdrant_image_collection: str = "omnibrain_images"

    # --- LLM / VLM providers ---
    openai_api_key: str | None = None

    # --- SQL Agent ---
    database_url: str | None = None

    # --- Observability ---
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = "https://cloud.langfuse.com"

    # --- Storage ---
    upload_dir: str = "storage/uploads"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance so we don't re-parse the environment on every call."""
    return Settings()
