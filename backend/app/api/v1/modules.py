"""Pricing, listing, fulfillment, customer service and finance API stubs."""

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.finance import FinanceRecord
from app.models.fulfillment import PurchaseOrder, Shipment
from app.models.user import User
from app.services.fulfillment_service import FulfillmentService
from app.services.listing_service import ListingService
from app.services.pricing_service import PricingService


# --- Schemas ---
class PricingCalculateRequest(BaseModel):
    cost_price_cny: str
    target_market: str
    logistics_cost_cny: str = "0.00"


class MatchCategoryRequest(BaseModel):
    product_name: str
    description: str = ""


class CreatePurchaseOrderRequest(BaseModel):
    supplier_id: str
    linked_order_ids: list[str] = []
    remark: str = ""


# --- Pricing ---
pricing_router = APIRouter(prefix="/v1/pricing", tags=["Pricing"])


@pricing_router.post("/calculate")
async def calculate_pricing(
    request: PricingCalculateRequest,
    current_user: User = Depends(get_current_user),
):
    """Calculate product cost and pricing."""
    result = await PricingService.calculate_cost(
        cost_price_cny=Decimal(request.cost_price_cny),
        target_market=request.target_market,
        logistics_cost_cny=Decimal(request.logistics_cost_cny),
    )
    return result


@pricing_router.get("/suggestions")
async def get_pricing_suggestions(
    product_id: str = None,
    target_market: str = "US",
    current_user: User = Depends(get_current_user),
):
    """Get pricing suggestions."""
    result = await PricingService.get_pricing_suggestions(product_id or "", target_market)
    return result


# --- Listing ---
listing_router = APIRouter(prefix="/v1/listing", tags=["Listing"])


@listing_router.post("/match-category")
async def match_category(
    request: MatchCategoryRequest,
    current_user: User = Depends(get_current_user),
):
    """Match TikTok Shop category."""
    result = await ListingService.match_category(request.product_name, request.description)
    return result


# --- Fulfillment ---
fulfillment_router = APIRouter(prefix="/v1/fulfillment", tags=["Fulfillment"])


@fulfillment_router.get("/purchase-orders")
async def list_purchase_orders(
    status: str = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List purchase orders."""
    query = select(PurchaseOrder).order_by(PurchaseOrder.created_at.desc())
    count_query = select(func.count()).select_from(PurchaseOrder)

    if status:
        query = query.where(PurchaseOrder.status == status)
        count_query = count_query.where(PurchaseOrder.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    orders = result.scalars().all()

    items = [
        {
            "id": str(po.id),
            "alibaba_order_id": po.alibaba_order_id or "",
            "status": po.status,
            "total_amount": str(po.total_amount),
            "currency": po.currency,
            "tracking_number": po.tracking_number or "",
            "created_at": po.created_at.isoformat() if po.created_at else "",
        }
        for po in orders
    ]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@fulfillment_router.post("/purchase-orders")
async def create_purchase_order(
    request: CreatePurchaseOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a 1688 purchase order."""
    po = PurchaseOrder(
        supplier_id=uuid.UUID(request.supplier_id) if request.supplier_id else None,
        linked_order_ids=request.linked_order_ids,
        remark=request.remark,
        status="pending",
        total_amount=Decimal("0.00"),
    )
    db.add(po)
    await db.flush()

    return {
        "id": str(po.id),
        "alibaba_order_id": po.alibaba_order_id or "",
        "status": po.status,
    }


@fulfillment_router.get("/shipments")
async def list_shipments(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List shipments."""
    query = (
        select(Shipment)
        .options(selectinload(Shipment.purchase_order))
        .order_by(Shipment.created_at.desc())
    )
    count_query = select(func.count()).select_from(Shipment)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    shipments = result.scalars().all()

    items = [
        {
            "id": str(s.id),
            "tracking_number": s.tracking_number,
            "status": s.status,
            "carrier": s.carrier or "",
            "origin": s.origin or "",
            "destination": s.destination or "",
            "estimated_delivery": s.estimated_delivery or "",
            "alibaba_order_id": s.purchase_order.alibaba_order_id or "" if s.purchase_order else "",
            "created_at": s.created_at.isoformat() if s.created_at else "",
        }
        for s in shipments
    ]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


# --- Customer Service ---
cs_router = APIRouter(prefix="/v1/customer-service", tags=["CustomerService"])


@cs_router.get("/sessions")
async def list_cs_sessions(
    status: str = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
):
    """List customer service sessions."""
    return {"items": [], "total": 0, "page": page, "page_size": page_size}


# --- Finance ---
finance_router = APIRouter(prefix="/v1/finance", tags=["Finance"])


@finance_router.get("/summary")
async def get_finance_summary(
    period: str = "month",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get financial summary."""
    # Income sum
    income_result = await db.execute(
        select(func.sum(FinanceRecord.amount)).where(FinanceRecord.type == "income")
    )
    total_income = income_result.scalar() or Decimal("0")

    # Cost sum
    cost_result = await db.execute(
        select(func.sum(FinanceRecord.amount)).where(FinanceRecord.type == "cost")
    )
    total_cost = cost_result.scalar() or Decimal("0")

    # Refund sum
    refund_result = await db.execute(
        select(func.sum(FinanceRecord.amount)).where(FinanceRecord.type == "refund")
    )
    total_refund = refund_result.scalar() or Decimal("0")

    # Fee sum
    fee_result = await db.execute(
        select(func.sum(FinanceRecord.amount)).where(FinanceRecord.type == "fee")
    )
    total_fee = fee_result.scalar() or Decimal("0")

    # Withdrawal sum
    withdrawal_result = await db.execute(
        select(func.sum(FinanceRecord.amount)).where(FinanceRecord.type == "withdrawal")
    )
    total_withdrawal = withdrawal_result.scalar() or Decimal("0")

    # Order count
    order_count_result = await db.execute(
        select(func.count(func.distinct(FinanceRecord.order_id))).where(
            FinanceRecord.order_id.isnot(None)
        )
    )
    order_count = order_count_result.scalar() or 0

    total_revenue = total_income
    net_profit = total_revenue - total_cost
    profit_rate = float(net_profit / total_revenue) if total_revenue > 0 else 0.0

    return {
        "total_revenue": str(total_revenue),
        "total_cost": str(total_cost),
        "total_refund": str(total_refund),
        "total_fee": str(total_fee),
        "total_withdrawal": str(total_withdrawal),
        "net_profit": str(net_profit),
        "profit_rate": profit_rate,
        "order_count": order_count,
    }


@finance_router.get("/transactions")
async def list_transactions(
    type: str = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List financial transactions."""
    query = select(FinanceRecord).order_by(FinanceRecord.created_at.desc())
    count_query = select(func.count()).select_from(FinanceRecord)

    if type:
        query = query.where(FinanceRecord.type == type)
        count_query = count_query.where(FinanceRecord.type == type)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    records = result.scalars().all()

    items = [
        {
            "id": str(r.id),
            "order_id": str(r.order_id) if r.order_id else "",
            "type": r.type,
            "amount": str(r.amount),
            "currency": r.currency,
            "exchange_rate": str(r.exchange_rate),
            "cny_amount": str(r.cny_amount),
            "description": r.description or "",
            "site": r.site or "",
            "created_at": r.created_at.isoformat() if r.created_at else "",
        }
        for r in records
    ]
    return {"items": items, "total": total, "page": page, "page_size": page_size}
