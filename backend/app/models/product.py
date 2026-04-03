"""Product, SKU, Category, Supplier and ProductImage models."""

import uuid
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ProductStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    LISTED = "listed"
    DELISTED = "delisted"


class Product(Base):
    """Product model representing a purchasable item."""

    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True
    )
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True
    )
    cost_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    sale_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), default=ProductStatus.DRAFT, index=True)
    score: Mapped[Decimal | None] = mapped_column(Numeric(3, 1), nullable=True)
    tiktok_product_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source_product_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    skus: Mapped[list["ProductSKU"]] = relationship(
        "ProductSKU", back_populates="product", cascade="all, delete-orphan"
    )
    images: Mapped[list["ProductImage"]] = relationship(
        "ProductImage", back_populates="product", cascade="all, delete-orphan"
    )
    materials: Mapped[list["Material"]] = relationship(
        "Material", back_populates="product", cascade="all, delete-orphan"
    )
    category: Mapped["Category | None"] = relationship("Category", back_populates="products")
    supplier: Mapped["Supplier | None"] = relationship("Supplier", back_populates="products")

    def __repr__(self) -> str:
        return f"<Product {self.name}>"


class ProductSKU(Base):
    """Product SKU (Stock Keeping Unit) model."""

    __tablename__ = "product_skus"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    sku_code: Mapped[str] = mapped_column(String(200), nullable=False)
    specs: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    cost_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    sale_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tiktok_sku_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="skus")

    def __repr__(self) -> str:
        return f"<ProductSKU {self.sku_code}>"


class ProductImage(Base):
    """Product image model."""

    __tablename__ = "product_images"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    image_type: Mapped[str] = mapped_column(
        String(50), default="main", nullable=False
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="images")


class Category(Base):
    """Product category model."""

    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True
    )
    tiktok_category_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    products: Mapped[list["Product"]] = relationship("Product", back_populates="category")
    children: Mapped[list["Category"]] = relationship(
        "Category", backref="parent", remote_side="Category.id"
    )


class Supplier(Base):
    """1688 supplier model."""

    __tablename__ = "suppliers"

    name: Mapped[str] = mapped_column(String(300), nullable=False)
    supplier_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 1), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    products: Mapped[list["Product"]] = relationship("Product", back_populates="supplier")

