"""Pricing Agent service - AI-powered pricing strategy."""

import logging
from decimal import Decimal
from typing import Any

from app.prompts.system_prompts import get_system_prompt
from app.services.llm_service import llm_invoke_json

logger = logging.getLogger(__name__)

# Default cost parameters
DEFAULT_PLATFORM_COMMISSION = Decimal("0.05")  # 5% TikTok commission
DEFAULT_CUSTOMS_RATE = Decimal("0.10")  # 10% customs
DEFAULT_LOGISTICS_RATE = Decimal("0.15")  # 15% of cost
DEFAULT_EXCHANGE_RATE = Decimal("0.14")  # CNY to USD


class PricingAgentService:
    """Service for AI-powered pricing strategy.

    Calculates:
    - Full cost breakdown
    - Competitor price analysis
    - Pricing recommendations (low/medium/high)
    - Profit simulation
    """

    def __init__(self):
        self.system_prompt = get_system_prompt("pricing")

    async def calculate_full_cost(
        self,
        cost_price_cny: Decimal,
        logistics_cost_cny: Decimal = Decimal("0"),
        customs_rate: Decimal = DEFAULT_CUSTOMS_RATE,
        platform_commission: Decimal = DEFAULT_PLATFORM_COMMISSION,
        exchange_rate: Decimal = DEFAULT_EXCHANGE_RATE,
    ) -> dict[str, Any]:
        """Calculate full cost breakdown for a product.

        Args:
            cost_price_cny: Purchase price in CNY
            logistics_cost_cny: Shipping cost in CNY
            customs_rate: Customs duty rate
            platform_commission: Platform commission rate
            exchange_rate: CNY to target currency rate

        Returns:
            Cost breakdown dictionary
        """
        # Estimate logistics if not provided
        if logistics_cost_cny == 0:
            logistics_cost_cny = cost_price_cny * DEFAULT_LOGISTICS_RATE

        customs_cost = cost_price_cny * customs_rate
        total_cost_cny = cost_price_cny + logistics_cost_cny + customs_cost
        total_cost_local = total_cost_cny * exchange_rate
        platform_fee = total_cost_local * platform_commission

        return {
            "cost_breakdown": {
                "purchase_cny": str(cost_price_cny),
                "logistics_cny": str(logistics_cost_cny),
                "customs_cny": str(customs_cost),
                "total_cost_cny": str(total_cost_cny),
                "exchange_rate": str(exchange_rate),
                "total_cost_local": str(total_cost_local),
                "platform_fee_local": str(platform_fee),
                "all_in_cost_local": str(total_cost_local + platform_fee),
            },
            "rates": {
                "customs_rate": str(customs_rate),
                "platform_commission": str(platform_commission),
                "exchange_rate": str(exchange_rate),
            },
        }

    async def generate_pricing_suggestions(
        self,
        product: dict[str, Any],
        market_context: dict[str, Any] | None = None,
        target_profit_rates: list[float] | None = None,
    ) -> dict[str, Any]:
        """Generate pricing suggestions using LLM.

        Args:
            product: Product data with cost info
            market_context: Competitor prices, market data
            target_profit_rates: Target profit rates (e.g., [0.20, 0.30, 0.40])

        Returns:
            Pricing suggestions with low/medium/high strategies
        """
        if target_profit_rates is None:
            target_profit_rates = [0.20, 0.30, 0.40]

        # Calculate base cost
        min_price = Decimal(str(product.get("min_price", 0) or 0))
        cost_data = await self.calculate_full_cost(min_price)
        all_in_cost = Decimal(cost_data["cost_breakdown"]["all_in_cost_local"])

        # Generate pricing strategies
        strategies = []
        for rate in target_profit_rates:
            price = all_in_cost / (1 - rate) if rate < 1 else all_in_cost * 2
            profit = price - all_in_cost
            strategies.append({
                "label": "budget" if rate < 0.25 else "standard" if rate < 0.35 else "premium",
                "price_local": str(round(price, 2)),
                "profit_local": str(round(profit, 2)),
                "profit_rate": f"{rate * 100:.0f}%",
            })

        # Use LLM for market-aware pricing if available
        if market_context:
            try:
                llm_suggestion = await self._llm_pricing_analysis(
                    product, cost_data, market_context
                )
            except Exception as e:
                logger.error(f"LLM pricing analysis failed: {e}")
                llm_suggestion = None
        else:
            llm_suggestion = None

        return {
            "product_id": product.get("product_id"),
            "cost_data": cost_data,
            "pricing_strategies": strategies,
            "llm_suggestion": llm_suggestion,
            "recommended_strategy": strategies[1] if len(strategies) > 1 else strategies[0],
        }

    async def _llm_pricing_analysis(
        self,
        product: dict[str, Any],
        cost_data: dict[str, Any],
        market_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Use LLM for market-aware pricing analysis."""
        prompt = f"""请基于成本和市场数据，为以下商品提供定价建议。

【商品信息】
- 标题: {product.get('title', 'N/A')}
- 采购价: {cost_data['cost_breakdown']['purchase_cny']} 人民币
- 到岸成本: {cost_data['cost_breakdown']['all_in_cost_local']} 美元

【市场数据】
- 竞品平均价: {market_context.get('competitor_avg_price', 'N/A')}
- 竞品价格区间: {market_context.get('competitor_price_range', 'N/A')}
- 目标市场: {market_context.get('target_market', 'US')}

请返回JSON格式：
{{
    "market_analysis": "<市场分析，100字内>",
    "recommended_price": "<建议售价>",
    "confidence": <0-1>,
    "price_positioning": "<budget/standard/premium>",
    "risk_warnings": ["<风险提示1>", ...]
}}"""

        return await llm_invoke_json(self.system_prompt, prompt)


# Singleton instance
pricing_service = PricingAgentService()
