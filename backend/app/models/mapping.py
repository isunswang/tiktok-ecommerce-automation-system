"""SKU mapping and match record models for order fulfillment."""

import uuid
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import ForeignKey, Numeric, String, Text, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class MappingStatus(StrEnum):
    """Status of SKU mapping."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class MatchMethod(StrEnum):
    """Methods used for matching SKUs."""
    SKU_CODE = "sku_code"  # SKU编码精确匹配
    NAME_SIMILARITY = "name_similarity"  # 名称相似度匹配
    IMAGE_SIMILARITY = "image_similarity"  # 图片相似度匹配
    SPEC_MATCH = "spec_match"  # 规格匹配
    MANUAL = "manual"  # 人工匹配


class SKUMapping(Base):
    """SKU mapping between TikTok product and 1688 product."""

    __tablename__ = "sku_mappings"

    tiktok_product_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    tiktok_sku_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    tiktok_sku_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    alibaba_product_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    alibaba_sku_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    alibaba_sku_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True
    )
    
    status: Mapped[str] = mapped_column(
        String(50), default=MappingStatus.ACTIVE, nullable=False, index=True
    )
    
    match_method: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # 规格映射关系 (TikTok规格 -> 1688规格)
    spec_mapping: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    # 价格映射
    tiktok_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    alibaba_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    
    # 图片URL用于相似度计算
    tiktok_image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    alibaba_image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Relationships
    match_records: Mapped[list["MatchRecord"]] = relationship(
        "MatchRecord", back_populates="sku_mapping", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SKUMapping {self.tiktok_sku_id} -> {self.alibaba_sku_id}>"


class MatchRecord(Base):
    """Record of SKU matching attempts and results."""

    __tablename__ = "match_records"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sku_mapping_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sku_mappings.id"), nullable=True, index=True
    )
    
    match_method: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # 匹配结果
    is_matched: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)
    
    # 匹配详情
    match_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # {
    #   "name_similarity": 0.85,
    #   "image_similarity": 0.92,
    #   "spec_match_score": 0.80,
    #   "sku_code_match": true
    # }
    
    # 失败原因
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Relationships
    sku_mapping: Mapped["SKUMapping"] = relationship("SKUMapping", back_populates="match_records")

    def __repr__(self) -> str:
        return f"<MatchRecord order={self.order_id} matched={self.is_matched}>"
