"""Risk control service for purchase order management."""

import logging
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fulfillment import PurchaseOrder
from app.models.order import Order

logger = logging.getLogger(__name__)


class RiskControlService:
    """Service for risk control in automated purchasing."""

    def __init__(self, db: AsyncSession):
        self.db = db

        # 风控规则配置
        self.MAX_ORDER_AMOUNT = Decimal("10000.00")  # 单笔最大金额
        self.MAX_DAILY_AMOUNT = Decimal("100000.00")  # 日累计最大金额
        self.MAX_DAILY_ORDERS = 100  # 日最大订单数
        self.MAX_QUANTITY_PER_ITEM = 50  # 单品最大数量

    async def check_purchase_risk(
        self,
        order: Order,
        total_amount: Decimal,
        item_count: int
    ) -> dict:
        """
        采购前风控检查
        
        Args:
            order: TikTok订单
            total_amount: 采购总金额
            item_count: 商品种类数
            
        Returns:
            {
                "is_safe": bool,
                "risk_level": str,  # low, medium, high, critical
                "risks": list[str],
                "suggestions": list[str]
            }
        """
        result = {
            "is_safe": True,
            "risk_level": "low",
            "risks": [],
            "suggestions": []
        }

        # 1. 单笔金额检查
        if total_amount > self.MAX_ORDER_AMOUNT:
            result["is_safe"] = False
            result["risk_level"] = "high"
            result["risks"].append(
                f"Amount {total_amount} exceeds limit {self.MAX_ORDER_AMOUNT}"
            )
            result["suggestions"].append("Require manual approval for large orders")

        # 2. 日累计金额检查
        daily_amount = await self._get_daily_purchase_amount()
        if daily_amount + total_amount > self.MAX_DAILY_AMOUNT:
            result["is_safe"] = False
            result["risk_level"] = "critical"
            result["risks"].append(
                f"Daily amount {daily_amount + total_amount} exceeds limit {self.MAX_DAILY_AMOUNT}"
            )
            result["suggestions"].append("Wait for next day or request approval")

        # 3. 日订单数检查
        daily_orders = await self._get_daily_order_count()
        if daily_orders >= self.MAX_DAILY_ORDERS:
            result["is_safe"] = False
            result["risk_level"] = "high"
            result["risks"].append(
                f"Daily order count {daily_orders} exceeds limit {self.MAX_DAILY_ORDERS}"
            )
            result["suggestions"].append("Wait for next day")

        # 4. 异常价格检查
        price_anomaly = await self._check_price_anomaly(order, total_amount)
        if price_anomaly:
            result["risks"].append(price_anomaly)
            result["suggestions"].append("Verify pricing before proceeding")
            if result["risk_level"] == "low":
                result["risk_level"] = "medium"

        # 5. 供应商风险评估
        supplier_risk = await self._check_supplier_risk(order)
        if supplier_risk:
            result["risks"].append(supplier_risk)
            result["suggestions"].append("Consider alternative suppliers")

        # 6. 买家行为风险评估
        buyer_risk = await self._check_buyer_risk(order)
        if buyer_risk:
            result["risks"].append(buyer_risk)
            result["risk_level"] = "medium"

        # 更新风险等级
        if result["risks"] and result["risk_level"] == "low":
            result["risk_level"] = "medium"

        return result

    async def should_require_manual_approval(
        self,
        risk_level: str,
        total_amount: Decimal
    ) -> bool:
        """
        判断是否需要人工审核
        
        Args:
            risk_level: 风险等级
            total_amount: 订单金额
            
        Returns:
            是否需要人工审核
        """
        # 高风险等级必须人工审核
        if risk_level in ["high", "critical"]:
            return True

        # 大额订单需要人工审核
        if total_amount > Decimal("5000.00"):
            return True

        return False

    async def _get_daily_purchase_amount(self) -> Decimal:
        """获取当日累计采购金额"""
        from datetime import datetime, timedelta
        
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        stmt = select(PurchaseOrder).where(
            PurchaseOrder.created_at >= today_start,
            PurchaseOrder.status != "cancelled"
        )
        result = await self.db.execute(stmt)
        orders = result.scalars().all()
        
        total = sum(order.total_amount for order in orders)
        return total

    async def _get_daily_order_count(self) -> int:
        """获取当日订单数"""
        from datetime import datetime
        
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        stmt = select(PurchaseOrder).where(
            PurchaseOrder.created_at >= today_start
        )
        result = await self.db.execute(stmt)
        
        return len(result.scalars().all())

    async def _check_price_anomaly(
        self, order: Order, total_amount: Decimal
    ) -> Optional[str]:
        """检查价格异常"""
        # 对比订单金额与采购金额比例
        if order.total_amount and total_amount > order.total_amount * Decimal("1.5"):
            return f"Purchase amount {total_amount} is 1.5x higher than order amount {order.total_amount}"
        
        return None

    async def _check_supplier_risk(self, order: Order) -> Optional[str]:
        """检查供应商风险"""
        # TODO: 检查供应商历史表现、发货时效、质量问题等
        return None

    async def _check_buyer_risk(self, order: Order) -> Optional[str]:
        """检查买家风险"""
        # TODO: 检查买家历史行为、退货率、投诉率等
        return None

    async def record_risk_event(
        self,
        order_id: str,
        risk_type: str,
        risk_description: str,
        action_taken: str
    ) -> None:
        """记录风险事件"""
        # TODO: 将风险事件记录到数据库
        logger.warning(
            f"Risk event recorded - Order: {order_id}, "
            f"Type: {risk_type}, Description: {risk_description}, "
            f"Action: {action_taken}"
        )

    async def get_risk_statistics(self, days: int = 7) -> dict:
        """
        获取风险统计
        
        Args:
            days: 统计天数
            
        Returns:
            风险统计数据
        """
        # TODO: 实现风险统计逻辑
        return {
            "total_orders": 100,
            "flagged_orders": 5,
            "blocked_orders": 2,
            "manual_approvals": 3,
            "risk_breakdown": {
                "high_value": 2,
                "price_anomaly": 1,
                "supplier_risk": 1,
                "buyer_risk": 1
            }
        }
