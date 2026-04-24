"""Selection Agent service - AI-powered product selection and scoring."""

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.prompts.system_prompts import get_system_prompt
from app.services.llm_service import llm_invoke_json

logger = logging.getLogger(__name__)


@dataclass
class ProductScore:
    """Product scoring result."""
    product_id: str
    overall_score: float  # 0-100
    price_score: float    # 0-10
    profit_score: float   # 0-10
    demand_score: float   # 0-10
    supplier_score: float # 0-10
    reasoning: str
    recommendation: str   # "highly_recommended", "recommended", "neutral", "not_recommended"


class SelectionAgentService:
    """Service for AI-powered product selection.

    Uses LLM to evaluate products across multiple dimensions:
    - Price competitiveness
    - Profit margin potential
    - Market demand indicators
    - Supplier reliability
    """

    # Scoring weights (must sum to 1.0)
    WEIGHTS = {
        "price": 0.25,
        "profit": 0.30,
        "demand": 0.25,
        "supplier": 0.20,
    }

    def __init__(self):
        self.system_prompt = get_system_prompt("selection")

    async def score_product(
        self,
        product: dict[str, Any],
        market_context: dict[str, Any] | None = None,
    ) -> ProductScore:
        """Score a single product using LLM.

        Args:
            product: Product data from 1688 or database
            market_context: Optional market data (competitor prices, trends)

        Returns:
            ProductScore with detailed scoring breakdown
        """
        prompt = self._build_scoring_prompt(product, market_context)

        try:
            result = await llm_invoke_json(self.system_prompt, prompt)
            return self._parse_score_result(product.get("product_id", ""), result)
        except Exception as e:
            logger.error(f"Failed to score product {product.get('product_id')}: {e}")
            # Return fallback score
            return self._fallback_score(product)

    async def score_products_batch(
        self,
        products: list[dict[str, Any]],
        market_context: dict[str, Any] | None = None,
    ) -> list[ProductScore]:
        """Score multiple products.

        Args:
            products: List of product data
            market_context: Optional market context

        Returns:
            List of ProductScore objects
        """
        results = []
        for product in products:
            score = await self.score_product(product, market_context)
            results.append(score)
        return results

    async def rank_products(
        self,
        products: list[dict[str, Any]],
        top_n: int = 10,
        min_score: float = 60.0,
    ) -> list[tuple[dict[str, Any], ProductScore]]:
        """Rank products by score and return top candidates.

        Args:
            products: List of product data
            top_n: Number of top products to return
            min_score: Minimum score threshold

        Returns:
            List of (product, score) tuples, sorted by score descending
        """
        scores = await self.score_products_batch(products)

        # Combine and sort
        ranked = list(zip(products, scores))
        ranked.sort(key=lambda x: x[1].overall_score, reverse=True)

        # Filter by minimum score and limit
        filtered = [(p, s) for p, s in ranked if s.overall_score >= min_score]
        return filtered[:top_n]

    async def generate_selection_report(
        self,
        products: list[dict[str, Any]],
        scores: list[ProductScore],
    ) -> str:
        """Generate a human-readable selection report.

        Args:
            products: Product data
            scores: Corresponding scores

        Returns:
            Markdown report string
        """
        prompt = f"""请根据以下商品评分结果，生成一份选品分析报告。

商品数量: {len(products)}
评分结果:
{self._format_scores_for_report(products, scores)}

报告要求：
1. 总结整体选品情况
2. 列出推荐商品及理由
3. 指出需要规避的商品及原因
4. 给出选品策略建议

请用Markdown格式输出报告。"""

        from app.services.llm_service import llm_invoke
        return await llm_invoke(self.system_prompt, prompt)

    def _build_scoring_prompt(
        self,
        product: dict[str, Any],
        market_context: dict[str, Any] | None,
    ) -> str:
        """Build the scoring prompt for LLM."""
        prompt = f"""请对以下1688商品进行多维度评分，用于跨境电商选品决策。

【商品信息】
- 商品ID: {product.get('product_id', 'N/A')}
- 标题: {product.get('title', 'N/A')}
- 价格区间: {product.get('price_range', 'N/A')} 人民币
- 最低价: {product.get('min_price', 'N/A')}
- 最高价: {product.get('max_price', 'N/A')}
- 月销量: {product.get('sales_count', 'N/A')}
- 供应商: {product.get('supplier_name', 'N/A')}
- 供应商所在地: {product.get('supplier_location', 'N/A')}
- 评分: {product.get('rating', 'N/A')}
- 起订量: {product.get('min_order_qty', 'N/A')}

【市场背景】
{self._format_market_context(market_context)}

【评分要求】
请按以下维度评分（每项1-10分），并给出综合建议：

1. 价格竞争力 (price_score): 对比同类产品价格优势
2. 利润空间 (profit_score): 考虑成本、物流、佣金后的利润潜力
3. 市场需求 (demand_score): 基于销量、趋势判断需求强度
4. 供应商信誉 (supplier_score): 评分、所在地、起订量等综合判断

请返回JSON格式：
{{
    "price_score": <1-10>,
    "profit_score": <1-10>,
    "demand_score": <1-10>,
    "supplier_score": <1-10>,
    "reasoning": "<评分理由，100字以内>",
    "recommendation": "<highly_recommended/recommended/neutral/not_recommended>"
}}"""
        return prompt

    def _parse_score_result(self, product_id: str, result: dict) -> ProductScore:
        """Parse LLM response into ProductScore."""
        price_score = float(result.get("price_score", 5))
        profit_score = float(result.get("profit_score", 5))
        demand_score = float(result.get("demand_score", 5))
        supplier_score = float(result.get("supplier_score", 5))

        # Calculate weighted overall score (convert 0-10 to 0-100)
        overall = (
            price_score * self.WEIGHTS["price"] +
            profit_score * self.WEIGHTS["profit"] +
            demand_score * self.WEIGHTS["demand"] +
            supplier_score * self.WEIGHTS["supplier"]
        ) * 10

        return ProductScore(
            product_id=product_id,
            overall_score=round(overall, 1),
            price_score=round(price_score, 1),
            profit_score=round(profit_score, 1),
            demand_score=round(demand_score, 1),
            supplier_score=round(supplier_score, 1),
            reasoning=result.get("reasoning", ""),
            recommendation=result.get("recommendation", "neutral"),
        )

    def _fallback_score(self, product: dict[str, Any]) -> ProductScore:
        """Generate fallback score when LLM fails."""
        # Simple rule-based scoring
        price_score = 5.0
        profit_score = 5.0
        demand_score = min(10, (product.get("sales_count", 0) or 0) / 5000)
        supplier_score = float(product.get("rating", 4) or 4)

        overall = (
            price_score * self.WEIGHTS["price"] +
            profit_score * self.WEIGHTS["profit"] +
            demand_score * self.WEIGHTS["demand"] +
            supplier_score * self.WEIGHTS["supplier"]
        ) * 10

        return ProductScore(
            product_id=product.get("product_id", ""),
            overall_score=round(overall, 1),
            price_score=round(price_score, 1),
            profit_score=round(profit_score, 1),
            demand_score=round(demand_score, 1),
            supplier_score=round(supplier_score, 1),
            reasoning="基于基础规则的评分（LLM不可用）",
            recommendation="neutral",
        )

    def _format_market_context(self, context: dict[str, Any] | None) -> str:
        """Format market context for prompt."""
        if not context:
            return "暂无市场背景数据"

        lines = []
        if context.get("competitor_avg_price"):
            lines.append(f"- 竞品平均价格: ${context['competitor_avg_price']}")
        if context.get("market_trend"):
            lines.append(f"- 市场趋势: {context['market_trend']}")
        if context.get("target_market"):
            lines.append(f"- 目标市场: {context['target_market']}")

        return "\n".join(lines) if lines else "暂无市场背景数据"

    def _format_scores_for_report(
        self,
        products: list[dict[str, Any]],
        scores: list[ProductScore],
    ) -> str:
        """Format scores for report prompt."""
        lines = []
        for product, score in zip(products, scores):
            lines.append(
                f"- {product.get('title', 'N/A')[:30]}: "
                f"综合{score.overall_score}分, "
                f"推荐度{score.recommendation}"
            )
        return "\n".join(lines)


# Singleton instance
selection_service = SelectionAgentService()
