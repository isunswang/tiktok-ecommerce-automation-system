"""AI服务配置管理"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class AISettings(BaseSettings):
    """AI服务配置"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="AI_"
    )
    
    # OpenAI配置
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_FALLBACK_MODEL: str = "gpt-3.5-turbo"
    
    # Stable Diffusion配置
    SD_API_URL: Optional[str] = None
    SD_MODEL: str = "sdxl-turbo"
    
    # OCR配置
    OCR_ENGINE: str = "paddle"  # paddle 或 tesseract
    OCR_LANG: str = "ch"  # ch, en, etc.
    
    # Mock模式(开发测试用)
    ENABLE_MOCK_AI: bool = True
    
    # 翻译设置
    DEFAULT_TARGET_LANGS: list[str] = ["en", "th", "vi", "id", "ms"]
    MAX_TRANSLATION_LENGTH: int = 2000
    TRANSLATION_TIMEOUT: int = 30  # 秒
    
    # 重试配置
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0  # 秒
    EXPONENTIAL_BACKOFF_BASE: float = 2.0
    
    # Rate Limit
    RATE_LIMIT_REQUESTS: int = 60  # 每分钟请求数
    RATE_LIMIT_PERIOD: int = 60  # 秒


# 全局单例
_ai_settings: Optional[AISettings] = None


def get_ai_settings() -> AISettings:
    """获取AI配置单例"""
    global _ai_settings
    if _ai_settings is None:
        _ai_settings = AISettings()
    return _ai_settings
