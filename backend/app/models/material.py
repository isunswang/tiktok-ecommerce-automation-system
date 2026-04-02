"""AI generated material model for products"""

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
import uuid


class Material(Base):
    """AI生成的商品素材"""
    __tablename__ = "materials"
    
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("products.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    material_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "title", "description", "image"
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)  # 文本内容
    file_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)  # 图片/视频URL
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # 额外元数据
    
    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="materials")
