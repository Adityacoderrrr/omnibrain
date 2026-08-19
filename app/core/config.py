"""
Enterprise Configuration Management Module for OmniBrain.

Provides centralized, environment-driven configuration with secure key masking,
type annotations, validation defaults, and cached singleton access.
"""

import logging
import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

config_logger = logging.getLogger("omnibrain.config")


def _safe_int(env_key: str, default: int) -> int:
    """Safely parse integer environment variable with fallback logging on ValueError."""
    val = os.getenv(env_key)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        config_logger.warning(
            "Invalid integer value '%s' for environment variable %s. Falling back to default %d.",
            val, env_key, default
        )
        return default


def _safe_float(env_key: str, default: float) -> float:
    """Safely parse float environment variable with fallback logging on ValueError."""
    val = os.getenv(env_key)
    if val is None:
        return default
    try:
        return float(val)
    except ValueError:
        config_logger.warning(
            "Invalid float value '%s' for environment variable %s. Falling back to default %f.",
            val, env_key, default
        )
        return default


@dataclass(frozen=True)
class Settings:
    """
    Centralized settings for the OmniBrain enterprise orchestrator platform.
    Reads from environment variables with production-ready defaults.
    """

    # --- Application Environments & Core Services ---
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    app_host: str = field(default_factory=lambda: os.getenv("APP_HOST", "0.0.0.0"))
    app_port: int = field(default_factory=lambda: _safe_int("APP_PORT", 8000))

    # --- Vector Database (Qdrant) Configuration ---
    qdrant_url: str = field(default_factory=lambda: os.getenv("QDRANT_URL", "http://localhost:6333"))
    qdrant_api_key: str | None = field(default_factory=lambda: os.getenv("QDRANT_API_KEY"))
    qdrant_text_collection: str = field(default_factory=lambda: os.getenv("QDRANT_TEXT_COLLECTION", "omnibrain_text"))
    qdrant_image_collection: str = field(default_factory=lambda: os.getenv("QDRANT_IMAGE_COLLECTION", "omnibrain_images"))
    vector_search_top_k: int = field(default_factory=lambda: _safe_int("VECTOR_SEARCH_TOP_K", 3))
    embedding_dimension_text: int = field(default_factory=lambda: _safe_int("EMBEDDING_DIM_TEXT", 1536))
    embedding_dimension_image: int = field(default_factory=lambda: _safe_int("EMBEDDING_DIM_IMAGE", 512))

    # --- LLM / VLM Providers & Models ---
    openai_api_key: str | None = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    default_llm_model: str = field(default_factory=lambda: os.getenv("DEFAULT_LLM_MODEL", "gpt-4o"))
    llm_temperature: float = field(default_factory=lambda: _safe_float("LLM_TEMPERATURE", 0.0))
    llm_timeout_seconds: float = field(default_factory=lambda: _safe_float("LLM_TIMEOUT_SECONDS", 30.0))
    max_tokens_response: int = field(default_factory=lambda: _safe_int("MAX_TOKENS_RESPONSE", 2048))

    # --- SQL Agent & Relational Data ---
    database_url: str | None = field(default_factory=lambda: os.getenv("DATABASE_URL"))
    sql_execution_timeout: float = field(default_factory=lambda: _safe_float("SQL_EXECUTION_TIMEOUT", 10.0))
    max_sql_rows: int = field(default_factory=lambda: _safe_int("MAX_SQL_ROWS", 100))

    # --- Resilience & Retries ---
    max_retries: int = field(default_factory=lambda: _safe_int("MAX_RETRIES", 3))
    retry_backoff_factor: float = field(default_factory=lambda: _safe_float("RETRY_BACKOFF_FACTOR", 1.5))

    # --- Observability (LangFuse / Tracing) ---
    langfuse_public_key: str | None = field(default_factory=lambda: os.getenv("LANGFUSE_PUBLIC_KEY"))
    langfuse_secret_key: str | None = field(default_factory=lambda: os.getenv("LANGFUSE_SECRET_KEY"))
    langfuse_host: str = field(default_factory=lambda: os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"))

    # --- Local Storage ---
    upload_dir: str = field(default_factory=lambda: os.getenv("UPLOAD_DIR", "storage/uploads"))

    def to_dict_masked(self) -> Dict[str, Any]:
        """
        Returns configuration dictionary with sensitive API keys masked for logging.
        """
        data = {k: v for k, v in self.__dict__.items()}
        for secret_field in ["openai_api_key", "qdrant_api_key", "langfuse_secret_key", "database_url"]:
            val = data.get(secret_field)
            if val and isinstance(val, str):
                data[secret_field] = f"{val[:4]}...***" if len(val) > 4 else "***"
        return data


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Returns cached, immutable thread-safe Settings instance.
    Implements Singleton pattern using lru_cache.
    """
    settings = Settings()
    if settings.app_env.lower() in ("production", "prod"):
        if not settings.openai_api_key:
            config_logger.warning("Production environment detected but OPENAI_API_KEY is not set.")
        if not settings.qdrant_api_key:
            config_logger.info("QDRANT_API_KEY is not configured; running in local/unauthenticated vector DB mode.")
    return settings


def clear_settings_cache() -> None:
    """
    Clears cached Settings singleton instance for testing or dynamic re-configuration.
    """
    get_settings.cache_clear()


