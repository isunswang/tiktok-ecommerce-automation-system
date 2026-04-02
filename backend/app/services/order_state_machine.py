"""Order state machine for managing order status transitions."""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus, OrderStatusHistory

logger = logging.getLogger(__name__)


class OrderStateMachine:
    """
    订单状态机
    
    状态转换规则:
    PENDING -> MATCHED (订单匹配成功)
    PENDING -> MATCHING_FAILED (订单匹配失败)
    MATCHED -> PURCHASED (已生成采购单)
    PURCHASED -> SHIPPED (已发货)
    SHIPPED -> DELIVERED (已送达)
    DELIVERED -> COMPLETED (已完成)
    
    任何状态 -> CANCELLED (取消)
    """

    # 定义允许的状态转换
    ALLOWED_TRANSITIONS = {
        OrderStatus.PENDING: [
            OrderStatus.MATCHED,
            OrderStatus.MATCHING_FAILED,
            OrderStatus.CANCELLED
        ],
        OrderStatus.MATCHED: [
            OrderStatus.PURCHASED,
            OrderStatus.CANCELLED
        ],
        OrderStatus.MATCHING_FAILED: [
            OrderStatus.MATCHED,  # 可以重新匹配
            OrderStatus.CANCELLED
        ],
        OrderStatus.PURCHASED: [
            OrderStatus.SHIPPED,
            OrderStatus.CANCELLED
        ],
        OrderStatus.SHIPPED: [
            OrderStatus.DELIVERED,
            OrderStatus.CANCELLED
        ],
        OrderStatus.DELIVERED: [
            OrderStatus.COMPLETED,
            OrderStatus.CANCELLED
        ],
        OrderStatus.COMPLETED: [],  # 终态,不允许转换
        OrderStatus.CANCELLED: []  # 终态,不允许转换
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def transition(
        self,
        order_id: str,
        to_status: OrderStatus,
        changed_by: Optional[str] = None,
        remark: Optional[str] = None
    ) -> Optional[Order]:
        """
        执行状态转换
        
        Args:
            order_id: 订单ID
            to_status: 目标状态
            changed_by: 操作人ID
            remark: 备注
            
        Returns:
            更新后的订单,失败返回None
        """
        # 获取订单
        order = await self._get_order(order_id)
        if not order:
            logger.error(f"Order {order_id} not found")
            return None

        from_status = OrderStatus(order.status)
        
        # 验证状态转换是否允许
        if not self._is_valid_transition(from_status, to_status):
            logger.error(
                f"Invalid transition from {from_status} to {to_status} for order {order_id}"
            )
            return None

        # 执行状态转换
        try:
            # 更新订单状态
            order.status = to_status
            order.updated_at = datetime.utcnow()
            
            # 创建状态历史记录
            history = OrderStatusHistory(
                order_id=order.id,
                from_status=from_status,
                to_status=to_status,
                changed_by=changed_by,
                remark=remark
            )
            self.db.add(history)
            
            await self.db.commit()
            await self.db.refresh(order)
            
            logger.info(
                f"Order {order_id} transitioned from {from_status} to {to_status}"
            )
            return order
            
        except Exception as e:
            logger.error(f"Failed to transition order {order_id}: {e}", exc_info=True)
            await self.db.rollback()
            return None

    def _is_valid_transition(
        self, from_status: OrderStatus, to_status: OrderStatus
    ) -> bool:
        """验证状态转换是否合法"""
        allowed = self.ALLOWED_TRANSITIONS.get(from_status, [])
        return to_status in allowed

    async def get_order_status_history(
        self, order_id: str
    ) -> list[OrderStatusHistory]:
        """获取订单状态历史"""
        stmt = select(OrderStatusHistory).where(
            OrderStatusHistory.order_id == order_id
        ).order_by(OrderStatusHistory.created_at.desc())
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_order(self, order_id: str) -> Optional[Order]:
        """获取订单"""
        stmt = select(Order).where(Order.id == order_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def can_transition(
        self, order_id: str, to_status: OrderStatus
    ) -> bool:
        """
        检查是否可以转换到指定状态
        
        Args:
            order_id: 订单ID
            to_status: 目标状态
            
        Returns:
            是否可以转换
        """
        order = await self._get_order(order_id)
        if not order:
            return False

        from_status = OrderStatus(order.status)
        return self._is_valid_transition(from_status, to_status)

    async def get_allowed_transitions(self, order_id: str) -> list[OrderStatus]:
        """
        获取订单允许的下一步状态
        
        Args:
            order_id: 订单ID
            
        Returns:
            允许转换的状态列表
        """
        order = await self._get_order(order_id)
        if not order:
            return []

        current_status = OrderStatus(order.status)
        return self.ALLOWED_TRANSITIONS.get(current_status, [])

    async def bulk_transition(
        self,
        order_ids: list[str],
        to_status: OrderStatus,
        changed_by: Optional[str] = None,
        remark: Optional[str] = None
    ) -> tuple[list[Order], list[str]]:
        """
        批量状态转换
        
        Args:
            order_ids: 订单ID列表
            to_status: 目标状态
            changed_by: 操作人ID
            remark: 备注
            
        Returns:
            (成功的订单列表, 失败的订单ID列表)
        """
        success_orders = []
        failed_order_ids = []

        for order_id in order_ids:
            order = await self.transition(order_id, to_status, changed_by, remark)
            if order:
                success_orders.append(order)
            else:
                failed_order_ids.append(order_id)

        return success_orders, failed_order_ids

    async def auto_transition_purchased_to_shipped(
        self, tracking_number: str
    ) -> int:
        """
        自动将已采购订单转换为已发货状态
        
        Args:
            tracking_number: 物流单号
            
        Returns:
            更新的订单数量
        """
        # 查找有该物流单号的订单
        stmt = select(Order).where(
            Order.tracking_number == tracking_number,
            Order.status == OrderStatus.PURCHASED
        )
        result = await self.db.execute(stmt)
        orders = result.scalars().all()

        count = 0
        for order in orders:
            success = await self.transition(
                str(order.id),
                OrderStatus.SHIPPED,
                remark=f"Auto transition: tracking number {tracking_number}"
            )
            if success:
                count += 1

        return count
