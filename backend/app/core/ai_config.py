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
    openai_api_key: str = ""
    openai_base_url: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openai_fallback_model: str = "gpt-3.5-turbo"
    
    # Stable Diffusion配置
    sd_api_url: Optional[str] = None
    sd_model: str = "sdxl-turbo"
    
    # OCR配置
    ocr_engine: str = "paddle"  # paddle 或 tesseract
    ocr_lang: str = "ch"  # ch, en, etc.
    
    # Mock模式(开发测试用)
    enable_mock_ai: bool = True
    
    # 翻译设置
    default_target_langs: list[str] = ["en", "th", "vi", "id", "ms"]
    max_translation_length: int = 2000
    translation_timeout: int = 30  # 秒
    
    # 重试配置
    max_retries: int = 3
    retry_delay: float = 1.0  # 秒
    exponential_backoff_base: float = 2.0
    
    # Rate Limit
    rate_limit_requests: int = 60  # 每分钟请求数
    rate_limit_period: int = 60  # 秒


# 全局单例
_ai_settings: Optional[AISettings] = None


def get_ai_settings() -> AISettings:
    """获取AI配置单例"""
    global _ai_settings
    if _ai_settings is None:
        _ai_settings = AISettings()
    return _ai_settings
