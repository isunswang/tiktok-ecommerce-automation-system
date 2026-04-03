"""Fulfillment models: PurchaseOrder and Shipment."""

import uuid
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PurchaseOrderStatus(StrEnum):
    PENDING = "pending"
    ORDERED = "ordered"
    SHIPPED = "shipped"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class PurchaseOrder(Base):
    """1688 purchase order model."""

    __tablename__ = "purchase_orders"

    alibaba_order_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default=PurchaseOrderStatus.PENDING, nullable=False, index=True
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )
    currency: Mapped[str] = mapped_column(String(10), default="CNY", nullable=False)
    linked_order_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    shipments: Mapped[list["Shipment"]] = relationship(
        "Shipment", back_populates="purchase_order", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.alibaba_order_id}>"


class ShipmentStatus(StrEnum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    RETURNED = "returned"
    EXCEPTION = "exception"


class Forwarder(Base):
    """Forwarder/Logistics provider model."""

    __tablename__ = "forwarders"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False, index=True)
    
    # 联系信息
    contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    
    # 仓库地址
    province: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # API配置
    api_endpoint: Mapped[str | None] = mapped_column(String(500), nullable=True)
    api_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    api_secret: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # 服务配置
    supported_countries: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # ["US", "TH", "VN", "ID", "MY"]
    
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Forwarder {self.code} - {self.name}>"


class Shipment(Base):
    """Shipment/logistics tracking model."""

    __tablename__ = "shipments"

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True
    )
    carrier: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tracking_number: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default=ShipmentStatus.PENDING, nullable=False, index=True
    )
    origin: Mapped[str | None] = mapped_column(String(200), nullable=True)
    destination: Mapped[str | None] = mapped_column(String(200), nullable=True)
    estimated_delivery: Mapped[str | None] = mapped_column(String(50), nullable=True)
    logistics_events: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder", back_populates="shipments"
    )
