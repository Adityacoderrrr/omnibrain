"""
Configuration for OmniBrain backend using standard library only.
"""
import os
from dataclasses import dataclass
from functools import lru_cache

@dataclass
class Settings:
    # --- App ---
    app_env: str = os.getenv("APP_ENV", "development")
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))

    # --- Qdrant ---
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key: str | None = os.getenv("QDRANT_API_KEY")
    qdrant_text_collection: str = os.getenv("QDRANT_TEXT_COLLECTION", "omnibrain_text")
    qdrant_image_collection: str = os.getenv("QDRANT_IMAGE_COLLECTION", "omnibrain_images")

    # --- LLM / VLM providers ---
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")

    # --- SQL Agent ---
    database_url: str | None = os.getenv("DATABASE_URL")

    # --- Observability ---
    langfuse_public_key: str | None = os.getenv("LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str | None = os.getenv("LANGFUSE_SECRET_KEY")
    langfuse_host: str = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    # --- Storage ---
    upload_dir: str = os.getenv("UPLOAD_DIR", "storage/uploads")

@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
