"""Product service - business logic for product management."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


class ProductService:
    """Product business logic layer."""

    @staticmethod
    async def get_by_id(db: AsyncSession, product_id: UUID) -> Product | None:
        """Get product by ID."""
        result = await db.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_products(
        db: AsyncSession,
        keyword: str = "",
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Product], int]:
        """List products with filters and pagination."""
        query = select(Product)
        if keyword:
            query = query.where(Product.name.ilike(f"%{keyword}%"))
        if status:
            query = query.where(Product.status == status)

        from sqlalchemy import func
        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar() or 0

        query = query.order_by(Product.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        return list(result.scalars().all()), total

    @staticmethod
    async def create_product(db: AsyncSession, **kwargs) -> Product:
        """Create a new product."""
        product = Product(**kwargs)
        db.add(product)
        await db.commit()
        await db.refresh(product)
        return product

    @staticmethod
    async def update_product(db: AsyncSession, product: Product, **kwargs) -> Product:
        """Update an existing product."""
        for key, value in kwargs.items():
            if value is not None:
                setattr(product, key, value)
        await db.commit()
        await db.refresh(product)
        return product
