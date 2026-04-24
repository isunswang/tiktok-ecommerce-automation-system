"""Agent configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    """Agent service configuration."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    backend_api_url: str = "http://localhost:8000/api/v1"
    redis_url: str = "redis://localhost:6379/1"
    debug: bool = True

    # LLM Configuration
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_temperature: float = 0.7

    # TikTok Shop API
    tiktok_app_key: str = ""
    tiktok_app_secret: str = ""
    tiktok_sandbox: bool = True
    tiktok_shop_mock_mode: bool = True

    # 1688 API
    alibaba_app_key: str = ""
    alibaba_app_secret: str = ""
    alibaba_1688_mock_mode: bool = True


agent_settings = AgentSettings()
