"""Finance models: FinanceRecord and ExchangeRate."""

import uuid
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class FinanceRecordType(StrEnum):
    INCOME = "income"
    COST = "cost"
    REFUND = "refund"
    FEE = "fee"
    WITHDRAWAL = "withdrawal"


class FinanceRecord(Base):
    """Financial transaction record model."""

    __tablename__ = "finance_records"

    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(
        Numeric(10, 6), nullable=False, default=Decimal("1.000000")
    )
    cny_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    site: Mapped[str | None] = mapped_column(String(10), nullable=True)

    def __repr__(self) -> str:
        return f"<FinanceRecord {self.type} {self.amount} {self.currency}>"


class ExchangeRate(Base):
    """Exchange rate history model."""

    __tablename__ = "exchange_rates"

    base_currency: Mapped[str] = mapped_column(String(10), default="CNY", nullable=False)
    target_currency: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    rate: Mapped[Decimal] = mapped_column(
        Numeric(14, 6), nullable=False
    )
    source: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
