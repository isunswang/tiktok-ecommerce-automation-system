"""Order service - business logic for order management."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatusHistory


class OrderService:
    """Order business logic layer."""

    @staticmethod
    async def get_by_id(db: AsyncSession, order_id: UUID) -> Order | None:
        result = await db.execute(select(Order).where(Order.id == order_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_status(
        db: AsyncSession, order: Order, new_status: str,
        changed_by: UUID | None = None, remark: str | None = None,
    ) -> Order:
        """Update order status and create history record."""
        old_status = order.status
        order.status = new_status
        if remark:
            order.remark = remark

        history = OrderStatusHistory(
            order_id=order.id,
            from_status=old_status,
            to_status=new_status,
            changed_by=changed_by,
            remark=remark,
        )
        db.add(history)
        await db.commit()
        await db.refresh(order)
        return order
