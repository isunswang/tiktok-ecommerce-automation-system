"""Product API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import PaginationParams
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.product import Product
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter(prefix="/v1/products", tags=["Products"])


@router.get("", response_model=PaginatedResponse)
async def list_products(
    pagination: PaginationParams = Depends(),
    keyword: str = Query("", description="Search keyword"),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List products with pagination and filters."""
    query = select(Product)

    if keyword:
        query = query.where(Product.name.ilike(f"%{keyword}%"))
    if status:
        query = query.where(Product.status == status)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.order_by(Product.created_at.desc())
    query = query.offset(pagination.offset).limit(pagination.page_size)
    result = await db.execute(query)
    products = result.scalars().all()

    items = []
    for p in products:
        items.append({
            "id": str(p.id),
            "name": p.name,
            "description": p.description or "",
            "category_id": str(p.category_id) if p.category_id else None,
            "cost_price": str(p.cost_price),
            "sale_price": str(p.sale_price) if p.sale_price else None,
            "status": p.status,
            "score": str(p.score) if p.score else None,
            "tiktok_product_id": p.tiktok_product_id or "",
            "source_url": p.source_url or "",
            "created_at": p.created_at.isoformat() if p.created_at else "",
            "updated_at": p.updated_at.isoformat() if p.updated_at else "",
        })
    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.post("")
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new product."""
    product = Product(**data.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return {
        "id": str(product.id),
        "name": product.name,
        "description": product.description or "",
        "category_id": str(product.category_id) if product.category_id else None,
        "cost_price": str(product.cost_price),
        "sale_price": str(product.sale_price) if product.sale_price else None,
        "status": product.status,
        "score": str(product.score) if product.score else None,
        "tiktok_product_id": product.tiktok_product_id or "",
        "source_url": product.source_url or "",
        "created_at": product.created_at.isoformat() if product.created_at else "",
        "updated_at": product.updated_at.isoformat() if product.updated_at else "",
    }


@router.get("/{product_id}")
async def get_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get product by ID."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return {
        "id": str(product.id),
        "name": product.name,
        "description": product.description or "",
        "category_id": str(product.category_id) if product.category_id else None,
        "cost_price": str(product.cost_price),
        "sale_price": str(product.sale_price) if product.sale_price else None,
        "status": product.status,
        "score": str(product.score) if product.score else None,
        "tiktok_product_id": product.tiktok_product_id or "",
        "source_url": product.source_url or "",
        "created_at": product.created_at.isoformat() if product.created_at else "",
        "updated_at": product.updated_at.isoformat() if product.updated_at else "",
    }


@router.put("/{product_id}")
async def update_product(
    product_id: UUID,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update product."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)

    await db.commit()
    await db.refresh(product)
    return {
        "id": str(product.id),
        "name": product.name,
        "description": product.description or "",
        "category_id": str(product.category_id) if product.category_id else None,
        "cost_price": str(product.cost_price),
        "sale_price": str(product.sale_price) if product.sale_price else None,
        "status": product.status,
        "score": str(product.score) if product.score else None,
        "tiktok_product_id": product.tiktok_product_id or "",
        "source_url": product.source_url or "",
        "created_at": product.created_at.isoformat() if product.created_at else "",
        "updated_at": product.updated_at.isoformat() if product.updated_at else "",
    }
