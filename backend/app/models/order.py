"""Order, OrderItem and OrderStatusHistory models."""

from decimal import Decimal
from enum import StrEnum

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class OrderStatus(StrEnum):
    PENDING = "pending"
    MATCHED = "matched"  # 订单匹配成功
    MATCHING_FAILED = "matching_failed"  # 订单匹配失败
    CONFIRMED = "confirmed"
    PURCHASED = "purchased"
    SHIPPED = "shipped"
    DELIVERED = "delivered"  # 已送达
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Order(Base):
    """TikTok Shop order model."""

    __tablename__ = "orders"

    tiktok_order_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default=OrderStatus.PENDING, nullable=False, index=True
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    buyer_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    buyer_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    shipping_address: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    status_history: Mapped[list["OrderStatusHistory"]] = relationship(
        "OrderStatusHistory", back_populates="order", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Order {self.tiktok_order_id}>"


class OrderItem(Base):
    """Order item (product within an order) model."""

    __tablename__ = "order_items"

    order_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=True
    )
    product_name: Mapped[str] = mapped_column(String(500), nullable=False)
    sku_code: Mapped[str | None] = mapped_column(String(200), nullable=True)
    quantity: Mapped[int] = mapped_column(nullable=False, default=1)
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")


class OrderStatusHistory(Base):
    """Order status change history model."""

    __tablename__ = "order_status_history"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    from_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_status: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="status_history")
