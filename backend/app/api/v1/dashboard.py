"""Dashboard API endpoints."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, desc, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.order import Order
from app.models.product import Product
from app.models.user import User

router = APIRouter(prefix="/v1/dashboard", tags=["Dashboard"])

# Status name mapping for Chinese labels
STATUS_NAME_MAP = {
    "pending": "待处理",
    "matched": "已匹配",
    "confirmed": "已确认",
    "purchased": "已采购",
    "shipped": "已发货",
    "delivered": "已送达",
    "completed": "已完成",
    "cancelled": "已取消",
    "matching_failed": "匹配失败",
}


@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Dashboard statistics cards."""
    today = datetime.now(timezone.utc).date()
    today_start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)

    # Today's order count
    today_orders_result = await db.execute(
        select(func.count()).select_from(Order).where(
            cast(Order.created_at, Date) == today
        )
    )
    today_orders = today_orders_result.scalar() or 0

    # Today's sales total
    today_sales_result = await db.execute(
        select(func.sum(Order.total_amount)).where(
            cast(Order.created_at, Date) == today
        )
    )
    today_sales = today_sales_result.scalar() or Decimal("0")

    # Pending orders count
    pending_result = await db.execute(
        select(func.count()).select_from(Order).where(Order.status == "pending")
    )
    pending_orders = pending_result.scalar() or 0

    # Total products count
    products_result = await db.execute(
        select(func.count()).select_from(Product)
    )
    total_products = products_result.scalar() or 0

    # If no data at all, return mock data for demo purposes
    has_data = today_orders > 0 or total_products > 0
    if not has_data:
        return {
            # NOTE: mock data returned when database has no records
            "today_orders": 128,
            "today_sales": "32680.00",
            "pending_orders": 23,
            "total_products": 1056,
            "order_trend": 12.5,
            "sales_trend": 8.2,
            "pending_trend": -3.1,
            "product_trend": 2.4,
        }

    return {
        "today_orders": today_orders,
        "today_sales": str(today_sales),
        "pending_orders": pending_orders,
        "total_products": total_products,
        # NOTE: trend values are mocked until historical data is available
        "order_trend": 12.5,
        "sales_trend": 8.2,
        "pending_trend": -3.1,
        "product_trend": 2.4,
    }


@router.get("/recent-orders")
async def get_recent_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Recent 10 orders."""
    query = (
        select(Order)
        .order_by(desc(Order.created_at))
        .limit(10)
    )
    result = await db.execute(query)
    orders = result.scalars().all()

    items = [
        {
            "id": str(o.id),
            "tiktok_order_id": o.tiktok_order_id or "",
            "status": o.status,
            "total_amount": str(o.total_amount),
            "currency": o.currency,
            "buyer_name": o.buyer_name or "",
            "created_at": o.created_at.isoformat() if o.created_at else "",
        }
        for o in orders
    ]
    return items


@router.get("/sales-trend")
async def get_sales_trend(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Last 7 days daily sales."""
    today = datetime.now(timezone.utc).date()
    dates = []
    sales = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        dates.append(day.strftime("%m-%d"))

        result = await db.execute(
            select(func.sum(Order.total_amount)).where(
                cast(Order.created_at, Date) == day
            )
        )
        day_total = result.scalar() or Decimal("0")
        sales.append(float(day_total))

    # If all zeros, return mock data
    if all(s == 0 for s in sales):
        return {
            "dates": dates,
            # NOTE: mock data returned when database has no order records
            "sales": [28200, 31500, 26800, 35600, 32100, 42300, 32680],
        }

    return {"dates": dates, "sales": sales}


@router.get("/order-status-distribution")
async def get_order_status_distribution(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Order count by status."""
    query = (
        select(Order.status, func.count())
        .group_by(Order.status)
        .order_by(func.count().desc())
    )
    result = await db.execute(query)
    rows = result.all()

    # If no data, return mock data
    if not rows:
        return {
            "data": [
                {"name": "待处理", "value": 23},
                {"name": "已匹配", "value": 15},
                {"name": "已确认", "value": 10},
                {"name": "已采购", "value": 8},
                {"name": "已发货", "value": 56},
                {"name": "已送达", "value": 38},
                {"name": "已完成", "value": 20},
                {"name": "已取消", "value": 11},
            ]
        }

    data = []
    for status, count in rows:
        data.append({
            "name": STATUS_NAME_MAP.get(status, status),
            "value": count,
        })
    return {"data": data}
