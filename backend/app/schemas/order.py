"""Pydantic schemas for orders."""

from decimal import Decimal

from pydantic import BaseModel


class OrderResponse(BaseModel):
    id: str
    tiktok_order_id: str | None = None
    status: str = "pending"
    total_amount: Decimal = Decimal("0.00")
    currency: str = "USD"
    buyer_name: str | None = None
    shipping_address: dict | None = None
    tracking_number: str | None = None
    remark: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"from_attributes": True}


class OrderStatusUpdate(BaseModel):
    status: str
    remark: str | None = None
