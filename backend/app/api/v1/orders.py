"""Order API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import PaginationParams
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.order import Order
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.order import OrderResponse, OrderStatusUpdate

router = APIRouter(prefix="/v1/orders", tags=["Orders"])


@router.get("", response_model=PaginatedResponse)
async def list_orders(
    pagination: PaginationParams = Depends(),
    status: str | None = Query(None),
    search: str = Query("", description="Order ID or product name"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List orders with pagination and filters."""
    query = select(Order)

    if status:
        query = query.where(Order.status == status)
    if search:
        query = query.where(Order.tiktok_order_id.ilike(f"%{search}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Order.created_at.desc())
    query = query.offset(pagination.offset).limit(pagination.page_size)
    result = await db.execute(query)
    orders = result.scalars().all()

    items = []
    for o in orders:
        items.append({
            "id": str(o.id),
            "tiktok_order_id": o.tiktok_order_id or "",
            "status": o.status,
            "total_amount": str(o.total_amount),
            "currency": o.currency,
            "buyer_name": o.buyer_name or "",
            "shipping_address": o.shipping_address or {},
            "tracking_number": o.tracking_number or "",
            "remark": o.remark or "",
            "created_at": o.created_at.isoformat() if o.created_at else "",
            "updated_at": o.updated_at.isoformat() if o.updated_at else "",
        })
    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{order_id}")
async def get_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get order details."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "id": str(order.id),
        "tiktok_order_id": order.tiktok_order_id or "",
        "status": order.status,
        "total_amount": str(order.total_amount),
        "currency": order.currency,
        "buyer_name": order.buyer_name or "",
        "shipping_address": order.shipping_address or {},
        "tracking_number": order.tracking_number or "",
        "remark": order.remark or "",
        "created_at": order.created_at.isoformat() if order.created_at else "",
        "updated_at": order.updated_at.isoformat() if order.updated_at else "",
    }


@router.put("/{order_id}/status")
async def update_order_status(
    order_id: UUID,
    data: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update order status."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = data.status
    if data.remark:
        order.remark = data.remark

    await db.commit()
    return {"message": "Order status updated"}
