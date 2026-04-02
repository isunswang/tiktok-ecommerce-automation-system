"""Pricing, listing, fulfillment, customer service and finance API stubs."""

from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.models.user import User

# --- Pricing ---
pricing_router = APIRouter(prefix="/v1/pricing", tags=["Pricing"])


@pricing_router.post("/calculate")
async def calculate_pricing(request: dict, current_user: User = Depends(get_current_user)):
    """Calculate product cost and pricing."""
    # TODO: Implement pricing calculation
    return {
        "cost_breakdown": {"purchase_cost_cny": 0, "logistics_cost_cny": 0, "total_cost_cny": 0},
        "suggested_prices": {"minimum_price": 0, "recommended_price": 0},
        "profit_simulation": [],
    }


@pricing_router.get("/suggestions")
async def get_pricing_suggestions(
    product_id: str = None,
    target_market: str = "US",
    current_user: User = Depends(get_current_user),
):
    """Get pricing suggestions."""
    return {"suggested_price": 0, "competitor_avg_price": 0}


# --- Listing ---
listing_router = APIRouter(prefix="/v1/listing", tags=["Listing"])


@listing_router.post("/match-category")
async def match_category(
    request: dict,
    current_user: User = Depends(get_current_user),
):
    """Match TikTok Shop category."""
    return {"candidates": [], "confidence": 0}


# --- Fulfillment ---
fulfillment_router = APIRouter(prefix="/v1/fulfillment", tags=["Fulfillment"])


@fulfillment_router.get("/purchase-orders")
async def list_purchase_orders(
    status: str = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
):
    """List purchase orders."""
    return {"items": [], "total": 0, "page": page, "page_size": page_size}


@fulfillment_router.post("/purchase-orders")
async def create_purchase_order(
    request: dict,
    current_user: User = Depends(get_current_user),
):
    """Create a 1688 purchase order."""
    return {"alibaba_order_id": "", "status": "pending"}


@fulfillment_router.get("/shipments")
async def list_shipments(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
):
    """List shipments."""
    return {"items": [], "total": 0, "page": page, "page_size": page_size}


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
):
    """Get financial summary."""
    return {
        "total_revenue": 0,
        "total_cost": 0,
        "net_profit": 0,
        "profit_rate": 0,
        "order_count": 0,
    }


@finance_router.get("/transactions")
async def list_transactions(
    type: str = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
):
    """List financial transactions."""
    return {"items": [], "total": 0, "page": page, "page_size": page_size}
