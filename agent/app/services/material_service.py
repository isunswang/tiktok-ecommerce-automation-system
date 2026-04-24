"""Material Agent service - AI-powered content generation for products."""

import logging
from typing import Any

from app.prompts.system_prompts import get_system_prompt
from app.services.llm_service import llm_invoke_json, llm_invoke

logger = logging.getLogger(__name__)


class MaterialAgentService:
    """Service for generating AI-powered product materials.

    Generates:
    - Localized product titles (multiple candidates)
    - Product descriptions with selling points
    - SEO keywords
    """

    # Target markets and their languages
    MARKET_LANGUAGES = {
        "US": "English",
        "UK": "English",
        "SG": "English",
        "MY": "English",
        "TH": "Thai",
        "VN": "Vietnamese",
        "PH": "English",
        "ID": "Indonesian",
    }

    def __init__(self):
        self.system_prompt = get_system_prompt("material")

    async def generate_titles(
        self,
        product: dict[str, Any],
        target_market: str = "US",
        count: int = 5,
    ) -> list[dict[str, Any]]:
        """Generate localized product titles.

        Args:
            product: Product data
            target_market: Target market code
            count: Number of title candidates

        Returns:
            List of title candidates with metadata
        """
        language = self.MARKET_LANGUAGES.get(target_market, "English")
        original_title = product.get("title", "")

        prompt = f"""请为以下商品生成{count}个{language}标题候选，用于TikTok Shop上架。

【原始商品信息】
- 中文标题: {original_title}
- 价格区间: {product.get('price_range', 'N/A')}
- 类目: {product.get('category', 'N/A')}

【标题要求】
1. 包含核心关键词，利于搜索
2. 符合TikTok Shop风格（简洁、吸引人）
3. 不超过150字符
4. 突出产品卖点
5. 符合{language}语言习惯

请返回JSON格式：
{{
    "titles": [
        {{"title": "<标题1>", "keywords": ["关键词1", "关键词2"], "style": "<concise/descriptive/catchy>"}},
        ...
    ]
}}"""

        try:
            result = await llm_invoke_json(self.system_prompt, prompt)
            return result.get("titles", [])[:count]
        except Exception as e:
            logger.error(f"Failed to generate titles: {e}")
            return self._fallback_titles(original_title, language, count)

    async def generate_description(
        self,
        product: dict[str, Any],
        target_market: str = "US",
    ) -> dict[str, Any]:
        """Generate product description with selling points.

        Args:
            product: Product data
            target_market: Target market code

        Returns:
            Description data with selling points
        """
        language = self.MARKET_LANGUAGES.get(target_market, "English")

        prompt = f"""请为以下商品生成{language}描述，用于TikTok Shop商品详情页。

【商品信息】
- 标题: {product.get('title', 'N/A')}
- 价格: {product.get('price_range', 'N/A')}
- 类目: {product.get('category', 'N/A')}
- 供应商所在地: {product.get('supplier_location', 'N/A')}

【描述要求】
1. 包含5个核心卖点，每个不超过50词
2. 突出产品优势和使用场景
3. 语言简洁有力，符合TikTok用户阅读习惯
4. 适当使用emoji增加吸引力

请返回JSON格式：
{{
    "description": "<完整描述文本>",
    "selling_points": [
        "<卖点1>",
        "<卖点2>",
        "<卖点3>",
        "<卖点4>",
        "<卖点5>"
    ],
    "features": ["<特性1>", "<特性2>", ...]
}}"""

        try:
            result = await llm_invoke_json(self.system_prompt, prompt)
            return result
        except Exception as e:
            logger.error(f"Failed to generate description: {e}")
            return self._fallback_description(product, language)

    async def generate_seo_keywords(
        self,
        product: dict[str, Any],
        target_market: str = "US",
    ) -> list[str]:
        """Generate SEO keywords for the product.

        Args:
            product: Product data
            target_market: Target market code

        Returns:
            List of SEO keywords
        """
        prompt = f"""请为以下商品生成SEO关键词，用于TikTok Shop搜索优化。

【商品信息】
- 标题: {product.get('title', 'N/A')}
- 类目: {product.get('category', 'N/A')}

【关键词要求】
1. 包含主关键词和长尾关键词
2. 符合TikTok用户搜索习惯
3. 数量10-15个
4. 按重要性排序

请返回JSON格式：
{{
    "keywords": ["关键词1", "关键词2", ...],
    "hashtags": ["#标签1", "#标签2", ...]
}}"""

        try:
            result = await llm_invoke_json(self.system_prompt, prompt)
            return result.get("keywords", [])
        except Exception as e:
            logger.error(f"Failed to generate SEO keywords: {e}")
            return []

    async def generate_full_materials(
        self,
        product: dict[str, Any],
        target_market: str = "US",
    ) -> dict[str, Any]:
        """Generate all materials for a product.

        Args:
            product: Product data
            target_market: Target market code

        Returns:
            Complete material data
        """
        # Generate in parallel
        titles_task = self.generate_titles(product, target_market)
        desc_task = self.generate_description(product, target_market)
        keywords_task = self.generate_seo_keywords(product, target_market)

        # Await all
        import asyncio
        titles, description, keywords = await asyncio.gather(
            titles_task, desc_task, keywords_task
        )

        return {
            "product_id": product.get("product_id"),
            "target_market": target_market,
            "titles": titles,
            "description": description.get("description", ""),
            "selling_points": description.get("selling_points", []),
            "features": description.get("features", []),
            "seo_keywords": keywords,
            "language": self.MARKET_LANGUAGES.get(target_market, "English"),
        }

    def _fallback_titles(
        self,
        original_title: str,
        language: str,
        count: int,
    ) -> list[dict[str, Any]]:
        """Generate fallback titles when LLM fails."""
        # Simple translation placeholder
        return [
            {"title": f"[Translation needed] {original_title[:50]}", "keywords": [], "style": "concise"}
            for _ in range(count)
        ]

    def _fallback_description(
        self,
        product: dict[str, Any],
        language: str,
    ) -> dict[str, Any]:
        """Generate fallback description when LLM fails."""
        return {
            "description": f"Product: {product.get('title', 'N/A')}",
            "selling_points": ["Quality product", "Fast shipping", "Great value"],
            "features": [],
        }


# Singleton instance
material_service = MaterialAgentService()
