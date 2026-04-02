"""Pydantic schemas for products."""

from decimal import Decimal

from pydantic import BaseModel, Field


class ProductResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    category_id: str | None = None
    cost_price: Decimal = Decimal("0.00")
    sale_price: Decimal | None = None
    status: str = "draft"
    score: Decimal | None = None
    tiktok_product_id: str | None = None
    source_url: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"from_attributes": True}


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    category_id: str | None = None
    supplier_id: str | None = None
    cost_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    sale_price: Decimal | None = Field(default=None, ge=0)
    source_url: str | None = None
    source_product_id: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    sale_price: Decimal | None = Field(default=None, ge=0)
    status: str | None = None
    score: Decimal | None = Field(default=None, ge=0, le=10)
