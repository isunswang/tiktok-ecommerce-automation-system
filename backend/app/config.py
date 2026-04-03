"""Application configuration using Pydantic Settings."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_name: str = "TikTok-Ops"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "DEBUG"
    secret_key: str = "change-me-in-production"

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://tiktok_ops:tiktok_ops_dev@localhost:5432/tiktok_ops",
        description="PostgreSQL async connection URL",
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_bucket_name: str = "tiktok-ops-assets"
    minio_secure: bool = False

    # RabbitMQ / Celery
    celery_broker_url: str = "amqp://tiktok_ops:tiktok_ops_dev@localhost:5672/"
    celery_result_backend: str = "redis://localhost:6379/2"

    # LLM / OpenAI
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key for LLM operations",
    )
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_temperature: float = 0.7

    # JWT
    jwt_secret_key: str = "change-me-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # TikTok Shop API
    tiktok_shop_api_url: str = "https://open-api.tiktokglobalshop.com"
    tiktok_shop_app_key: str = ""
    tiktok_shop_app_secret: str = ""
    tiktok_shop_access_token: str = ""
    tiktok_shop_mock_mode: bool = True

    # 1688 API
    alibaba_1688_app_key: str = ""
    alibaba_1688_app_secret: str = ""
    alibaba_1688_mock_mode: bool = True

    # LLM
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_temperature: float = 0.7

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper

    @property
    def sync_database_url(self) -> str:
        """Convert async database URL to sync version for Alembic."""
        return self.database_url.replace("+asyncpg", "+psycopg2")

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance for convenience
settings = get_settings()
