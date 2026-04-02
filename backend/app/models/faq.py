"""FAQ knowledge base model."""

from enum import StrEnum

from sqlalchemy import String, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class FAQCategory(StrEnum):
    """FAQ category."""
    PRODUCT = "product"  # 商品信息
    SHIPPING = "shipping"  # 物流发货
    RETURN = "return"  # 退换货
    PAYMENT = "payment"  # 支付
    COUPON = "coupon"  # 优惠券
    GENERAL = "general"  # 通用问题


class FAQStatus(StrEnum):
    """FAQ status."""
    ACTIVE = "active"
    INACTIVE = "inactive"


class FAQ(Base):
    """FAQ knowledge base model."""

    __tablename__ = "faqs"

    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    question: Mapped[str] = mapped_column(String(1000), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    
    # 多语言版本
    question_en: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    answer_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # 关键词标签
    keywords: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # ["shipping", "delivery", "时间"]
    
    # 匹配规则
    match_rules: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # {
    #   "exact_match": ["发货时间", "什么时候发货"],
    #   "fuzzy_match": ["发货", "配送"],
    #   "regex": ["何时.*发货"]
    # }
    
    # 使用统计
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    helpful_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    status: Mapped[str] = mapped_column(
        String(20), default=FAQStatus.ACTIVE, nullable=False, index=True
    )
    
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # 适用站点
    applicable_sites: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # ["TH", "VN", "ID", "MY"]

    def __repr__(self) -> str:
        return f"<FAQ {self.category}: {self.question[:30]}>"
