"""Pydantic schemas for orders."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, field_serializer


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

    @field_serializer("id")
    def serialize_id(self, value: UUID | str) -> str:
        return str(value)

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: datetime | str | None) -> str | None:
        if value is None:
            return None
        return value.isoformat() if isinstance(value, datetime) else value


class OrderStatusUpdate(BaseModel):
    status: str
    remark: str | None = None
