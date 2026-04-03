"""文本翻译服务"""

import asyncio
import json
import logging
from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI, APIError, RateLimitError, APIConnectionError

from app.core.ai_config import get_ai_settings

logger = logging.getLogger(__name__)


class TranslationService:
    """文本翻译服务，使用OpenAI GPT-4o"""
    
    # Prompt模板
    PROMPT_TEMPLATES = {
        "product_title": {
            "system": "You are a professional e-commerce translator specializing in cross-border trade. Translate product titles to be concise, keyword-rich, and attractive to international buyers.",
            "requirements": [
                "Keep the translation concise and impactful",
                "Include relevant keywords for search optimization",
                "Maintain marketing appeal",
                "Follow target language conventions for e-commerce titles"
            ]
        },
        "description": {
            "system": "You are a professional e-commerce translator. Translate product descriptions to be natural, fluent, and culturally appropriate for the target market.",
            "requirements": [
                "Make the description natural and fluent",
                "Adapt to local consumer preferences and cultural norms",
                "Highlight product benefits and features",
                "Use appropriate formatting and structure"
            ]
        },
        "bullet_point": {
            "system": "You are a professional e-commerce translator specializing in product marketing. Translate bullet points to highlight product advantages and appeal to buyers.",
            "requirements": [
                "Make each point clear and compelling",
                "Highlight product advantages and unique selling points",
                "Use marketing language appropriate for the target market",
                "Keep the format as bullet points"
            ]
        }
    }
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """初始化翻译服务"""
        self.settings = get_ai_settings()
        self.api_key = api_key or self.settings.openai_api_key
        self.base_url = base_url or self.settings.openai_base_url
        self.model = self.settings.openai_model
        self.fallback_model = self.settings.openai_fallback_model
        
        if not self.settings.enable_mock_ai and not self.api_key:
            raise ValueError("OpenAI API key is required when Mock mode is disabled")
        
        self.client = None
        if not self.settings.enable_mock_ai:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.settings.TRANSLATION_TIMEOUT
            )
    
    async def translate_text(
        self,
        text: str,
        source_lang: str = "zh",
        target_lang: str = "en",
        context: str = "product_title"
    ) -> Dict[str, Any]:
        """翻译文本"""
        # 验证输入
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        if len(text) > self.settings.MAX_TRANSLATION_LENGTH:
            raise ValueError(f"Text exceeds maximum length of {self.settings.MAX_TRANSLATION_LENGTH}")
        
        # Mock模式
        if self.settings.enable_mock_ai:
            return self._mock_translate(text, source_lang, target_lang, context)
        
        # 获取prompt模板
        template = self.PROMPT_TEMPLATES.get(context, self.PROMPT_TEMPLATES["product_title"])
        
        # 构造prompt
        prompt = self._build_translation_prompt(text, source_lang, target_lang, template)
        
        # 调用API（带重试和降级）
        try:
            result = await self._call_openai_with_retry(prompt, template["system"])
            
            # 解析结果
            translated_text, confidence = self._parse_translation_result(result)
            
            return {
                "original_text": text,
                "translated_text": translated_text,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise
    
    async def batch_translate(
        self,
        texts: List[str],
        source_lang: str = "zh",
        target_lang: str = "en",
        context: str = "product_title"
    ) -> List[Dict[str, Any]]:
        """批量翻译"""
        if not texts:
            return []
        
        # Mock模式
        if self.settings.enable_mock_ai:
            return [
                self._mock_translate(text, source_lang, target_lang, context)
                for text in texts
            ]
        
        # 批量处理
        batch_prompt = self._build_batch_prompt(texts, source_lang, target_lang, context)
        template = self.PROMPT_TEMPLATES.get(context, self.PROMPT_TEMPLATES["product_title"])
        
        try:
            result = await self._call_openai_with_retry(batch_prompt, template["system"])
            translations = self._parse_batch_result(result, texts)
            
            return [
                {
                    "original_text": text,
                    "translated_text": translations[i],
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                    "confidence": 0.9
                }
                for i, text in enumerate(texts)
            ]
            
        except Exception as e:
            logger.error(f"Batch translation failed: {e}")
            # 失败时逐个翻译
            logger.info("Falling back to individual translation")
            results = []
            for text in texts:
                try:
                    result = await self.translate_text(text, source_lang, target_lang, context)
                    results.append(result)
                except Exception as e2:
                    logger.error(f"Failed to translate text: {text[:50]}... Error: {e2}")
                    results.append({
                        "original_text": text,
                        "translated_text": text,
                        "source_lang": source_lang,
                        "target_lang": target_lang,
                        "confidence": 0.0,
                        "error": str(e2)
                    })
            return results
    
    def _build_translation_prompt(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        template: Dict[str, Any]
    ) -> str:
        """构造翻译prompt"""
        requirements = "\n".join(f"- {r}" for r in template["requirements"])
        
        prompt = f"""Translate the following {source_lang} text to {target_lang}.

Requirements:
{requirements}

Original text:
{text}

Return a JSON object with the following format:
{{
  "translation": "translated text here",
  "confidence": 0.95
}}

The confidence should be between 0 and 1, indicating how confident you are about the translation quality."""
        
        return prompt
    
    def _build_batch_prompt(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str,
        context: str
    ) -> str:
        """构造批量翻译prompt"""
        numbered_texts = "\n".join(f"{i+1}. {text}" for i, text in enumerate(texts))
        
        prompt = f"""Translate the following {source_lang} texts to {target_lang}.
Translate each line and maintain the numbering.

Texts to translate:
{numbered_texts}

Return a JSON array with translations:
[
  "translation 1",
  "translation 2",
  ...
]

Only return the JSON array, no other text."""
        
        return prompt
    
    async def _call_openai_with_retry(
        self,
        prompt: str,
        system_prompt: str,
        use_fallback: bool = False
    ) -> str:
        """调用OpenAI API（带重试和降级）"""
        model = self.fallback_model if use_fallback else self.model
        max_retries = self.settings.MAX_RETRIES
        
        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2000
                )
                
                return response.choices[0].message.content
                
            except RateLimitError as e:
                # Rate limit - exponential backoff
                if attempt < max_retries - 1:
                    delay = self.settings.RETRY_DELAY * (
                        self.settings.EXPONENTIAL_BACKOFF_BASE ** attempt
                    )
                    logger.warning(f"Rate limit hit, retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(delay)
                else:
                    raise
                    
            except APIConnectionError as e:
                # 连接错误 - 重试
                if attempt < max_retries - 1:
                    delay = self.settings.RETRY_DELAY
                    logger.warning(f"Connection error, retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(delay)
                else:
                    raise
                    
            except APIError as e:
                # API错误 - 如果还没使用降级模型，尝试降级
                if not use_fallback and attempt == max_retries - 1:
                    logger.warning(f"API error with {model}, trying fallback model {self.fallback_model}")
                    return await self._call_openai_with_retry(prompt, system_prompt, use_fallback=True)
                raise
        
        raise RuntimeError("Max retries exceeded")
    
    def _parse_translation_result(self, result: str) -> tuple[str, float]:
        """解析翻译结果"""
        try:
            # 尝试解析JSON
            parsed = json.loads(result)
            translation = parsed.get("translation", result)
            confidence = float(parsed.get("confidence", 0.9))
            return translation, confidence
        except (json.JSONDecodeError, ValueError):
            # 如果不是JSON，直接返回文本
            return result.strip(), 0.8
    
    def _parse_batch_result(self, result: str, original_texts: List[str]) -> List[str]:
        """解析批量翻译结果"""
        try:
            translations = json.loads(result)
            if isinstance(translations, list):
                # 确保数量匹配
                if len(translations) != len(original_texts):
                    logger.warning(f"Translation count mismatch: expected {len(original_texts)}, got {len(translations)}")
                    # 补齐或截断
                    if len(translations) < len(original_texts):
                        translations.extend(original_texts[len(translations):])
                    else:
                        translations = translations[:len(original_texts)]
                return translations
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse batch result: {e}")
        
        # 解析失败，返回原文
        return original_texts
    
    def _mock_translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        context: str
    ) -> Dict[str, Any]:
        """Mock翻译（用于测试）"""
        # 简单的Mock逻辑
        mock_translations = {
            "en": f"[MOCK EN] {text}",
            "th": f"[MOCK TH] {text}",
            "vi": f"[MOCK VI] {text}",
            "id": f"[MOCK ID] {text}",
            "ms": f"[MOCK MS] {text}"
        }
        
        translated = mock_translations.get(target_lang, f"[MOCK {target_lang.upper()}] {text}")
        
        return {
            "original_text": text,
            "translated_text": translated,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "confidence": 0.95
        }
