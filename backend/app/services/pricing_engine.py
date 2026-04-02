"""智能定价引擎服务"""

from decimal import Decimal
from typing import Dict, Any, List
from datetime import datetime

from app.config import get_settings


class PricingEngine:
    """智能定价引擎
    
    定价策略:
    1. 成本加成: 基础成本 + 物流 + 关税 + 平台佣金 + 利润率
    2. 竞品对标: 参考同类商品的市场价格区间
    3. 动态调价: 根据销量、库存、市场竞争情况动态调整
    """
    
    def __init__(self):
        """初始化定价引擎"""
        self.settings = get_settings()
        
        # 默认费用配置
        self.default_config = {
            # 平台佣金率 (TikTok Shop)
            "platform_commission_rate": Decimal("0.05"),  # 5%
            
            # 支付手续费率
            "payment_fee_rate": Decimal("0.03"),  # 3%
            
            # 关税税率 (根据目标市场)
            "customs_rates": {
                "US": Decimal("0.10"),  # 美国10%
                "TH": Decimal("0.07"),  # 泰国7%
                "VN": Decimal("0.10"),  # 越南10%
                "ID": Decimal("0.10"),  # 印尼10%
                "MY": Decimal("0.10"),  # 马来西亚10%
                "PH": Decimal("0.12"),  # 菲律宾12%
            },
            
            # 目标利润率范围
            "min_profit_rate": Decimal("0.15"),  # 最低15%
            "target_profit_rate": Decimal("0.25"),  # 目标25%
            "max_profit_rate": Decimal("0.40"),  # 最高40%
            
            # 物流成本估算 (根据重量)
            "logistics_per_kg": Decimal("5.00"),  # $5/kg
            
            # 汇率 (CNY to USD, 实际应从ExchangeRate表获取)
            "exchange_rate": Decimal("0.14"),  # 1 CNY = 0.14 USD
        }
    
    async def calculate_cost_breakdown(
        self,
        cost_price_cny: Decimal,
        weight_kg: Decimal = Decimal("0.5"),
        target_market: str = "US",
        customs_rate: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """计算成本明细
        
        Args:
            cost_price_cny: 采购成本(人民币)
            weight_kg: 商品重量(kg)
            target_market: 目标市场
            customs_rate: 关税税率(可选,默认从配置读取)
        
        Returns:
            成本明细字典
        """
        config = self.default_config
        
        # 1. 采购成本
        purchase_cost_cny = cost_price_cny
        
        # 2. 物流成本
        logistics_cost_usd = weight_kg * config["logistics_per_kg"]
        
        # 3. 关税 (基于商品价值)
        customs_rate = customs_rate or config["customs_rates"].get(
            target_market, Decimal("0.10")
        )
        customs_cost_usd = (purchase_cost_cny * config["exchange_rate"]) * customs_rate
        
        # 4. 总成本(USD)
        total_cost_usd = (
            purchase_cost_cny * config["exchange_rate"]
            + logistics_cost_usd
            + customs_cost_usd
        )
        
        return {
            "purchase_cost_cny": str(purchase_cost_cny),
            "purchase_cost_usd": str(purchase_cost_cny * config["exchange_rate"]),
            "logistics_cost_usd": str(logistics_cost_usd),
            "customs_cost_usd": str(customs_cost_usd),
            "customs_rate": str(customs_rate),
            "total_cost_usd": str(total_cost_usd),
            "target_market": target_market,
            "exchange_rate": str(config["exchange_rate"]),
        }
    
    async def calculate_suggested_prices(
        self,
        total_cost_usd: Decimal,
        competitor_prices: Optional[List[Decimal]] = None
    ) -> Dict[str, Any]:
        """计算建议售价
        
        Args:
            total_cost_usd: 总成本(USD)
            competitor_prices: 竞品价格列表(可选)
        
        Returns:
            建议售价字典
        """
        config = self.default_config
        
        # 1. 基于成本加成的价格
        min_price = total_cost_usd / (1 - config["platform_commission_rate"] - config["payment_fee_rate"] - config["min_profit_rate"])
        target_price = total_cost_usd / (1 - config["platform_commission_rate"] - config["payment_fee_rate"] - config["target_profit_rate"])
        max_price = total_cost_usd / (1 - config["platform_commission_rate"] - config["payment_fee_rate"] - config["max_profit_rate"])
        
        # 2. 竞品价格参考
        competitor_analysis = None
        if competitor_prices:
            avg_price = sum(competitor_prices) / len(competitor_prices)
            min_competitor = min(competitor_prices)
            max_competitor = max(competitor_prices)
            
            competitor_analysis = {
                "avg_price": str(avg_price),
                "min_price": str(min_competitor),
                "max_price": str(max_competitor),
                "price_range": f"{min_competitor} - {max_competitor}"
            }
            
            # 如果竞品平均价格低于我们的最低价格,调整建议价格
            if avg_price < min_price:
                # 警告: 可能无利润空间
                target_price = avg_price * Decimal("0.95")  # 比竞品低5%
                min_price = target_price
        
        # 3. 计算利润率
        def calc_profit_rate(price: Decimal) -> Decimal:
            revenue_after_fees = price * (1 - config["platform_commission_rate"] - config["payment_fee_rate"])
            profit = revenue_after_fees - total_cost_usd
            return profit / price
        
        return {
            "min_price": str(round(min_price, 2)),
            "target_price": str(round(target_price, 2)),
            "max_price": str(round(max_price, 2)),
            "min_profit_rate": str(round(calc_profit_rate(min_price) * 100, 2)) + "%",
            "target_profit_rate": str(round(calc_profit_rate(target_price) * 100, 2)) + "%",
            "max_profit_rate": str(round(calc_profit_rate(max_price) * 100, 2)) + "%",
            "competitor_analysis": competitor_analysis,
            "recommendation": "target_price"
        }
    
    async def get_pricing_suggestion(
        self,
        cost_price_cny: Decimal,
        weight_kg: Decimal = Decimal("0.5"),
        target_market: str = "US",
        competitor_prices: Optional[List[Decimal]] = None
    ) -> Dict[str, Any]:
        """获取完整的定价建议
        
        Args:
            cost_price_cny: 采购成本(人民币)
            weight_kg: 商品重量(kg)
            target_market: 目标市场
            competitor_prices: 竞品价格列表(可选)
        
        Returns:
            完整的定价建议
        """
        # 计算成本明细
        cost_breakdown = await self.calculate_cost_breakdown(
            cost_price_cny, weight_kg, target_market
        )
        
        # 计算建议售价
        total_cost_usd = Decimal(cost_breakdown["total_cost_usd"])
        suggested_prices = await self.calculate_suggested_prices(
            total_cost_usd, competitor_prices
        )
        
        return {
            "cost_breakdown": cost_breakdown,
            "suggested_prices": suggested_prices,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def optimize_price(
        self,
        product_id: str,
        current_price: Decimal,
        sales_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """动态价格优化
        
        基于销售数据动态调整价格:
        - 销量高: 可适当提价
        - 销量低: 降价促销
        - 库存高: 降价清仓
        - 库存低: 提价减少销售速度
        
        Args:
            product_id: 商品ID
            current_price: 当前价格
            sales_data: 销售数据(销量、库存等)
        
        Returns:
            价格优化建议
        """
        # TODO: 实现更复杂的定价算法
        # 当前使用简单规则
        
        daily_sales = sales_data.get("daily_sales", 0)
        inventory = sales_data.get("inventory", 0)
        
        suggestion = "hold"  # hold, increase, decrease
        adjustment_rate = Decimal("0")
        
        # 简单规则
        if daily_sales > 10 and inventory < 50:
            # 销量高且库存低 -> 提价5-10%
            suggestion = "increase"
            adjustment_rate = Decimal("0.05")
        elif daily_sales < 2 and inventory > 100:
            # 销量低且库存高 -> 降价10-15%
            suggestion = "decrease"
            adjustment_rate = Decimal("-0.10")
        elif daily_sales > 5 and inventory > 50:
            # 销量正常 -> 维持价格
            suggestion = "hold"
            adjustment_rate = Decimal("0")
        
        new_price = current_price * (1 + adjustment_rate)
        
        return {
            "current_price": str(current_price),
            "suggested_price": str(round(new_price, 2)),
            "adjustment_rate": str(round(adjustment_rate * 100, 2)) + "%",
            "suggestion": suggestion,
            "reason": f"Based on daily_sales={daily_sales}, inventory={inventory}"
        }
