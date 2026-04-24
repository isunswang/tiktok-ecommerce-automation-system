"""Database pipeline for storing scraped items into PostgreSQL."""

import logging
import sys
import os
from decimal import Decimal
from typing import Any

from itemadapter import ItemAdapter
from scrapy import Spider
from scrapy.exceptions import DropItem

from ..items import AlibabaProductItem

logger = logging.getLogger(__name__)

# Add project root to path for backend imports
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Try to import backend modules (optional - pipeline works without them)
try:
    from backend.app.core.database import async_session_factory
    from backend.app.models.product import Product, ProductImage, ProductSKU, Supplier
    DB_AVAILABLE = True
    logger.info("Database modules imported successfully")
except ImportError:
    DB_AVAILABLE = False
    logger.warning("Backend database modules not available. DatabasePipeline will be disabled.")


class DatabasePipeline:
    """Async Scrapy pipeline for storing scraped products into PostgreSQL.

    Handles:
    - Deduplication based on source_product_id
    - Creating/updating Product records
    - Creating ProductSKU records
    - Creating/updating Supplier records
    - Creating ProductImage records

    Requires backend database modules to be importable.
    """

    def __init__(self) -> None:
        self.session = None

    async def open_spider(self, spider: Spider) -> None:
        if not DB_AVAILABLE:
            logger.warning("DatabasePipeline disabled: backend modules not available")
            return
        try:
            self.session = async_session_factory()
            logger.info(f"DatabasePipeline opened for spider: {spider.name}")
        except Exception as e:
            logger.error(f"Failed to create database session: {e}")
            self.session = None

    async def close_spider(self, spider: Spider) -> None:
        if self.session:
            try:
                await self.session.close()
            except Exception as e:
                logger.error(f"Error closing database session: {e}")
            logger.info(f"DatabasePipeline closed for spider: {spider.name}")

    async def process_item(self, item: AlibabaProductItem, spider: Spider) -> AlibabaProductItem:
        if not self.session or not DB_AVAILABLE:
            return item

        adapter = ItemAdapter(item)
        product_id = adapter.get("product_id")

        if not product_id:
            logger.debug("Item missing product_id, skipping DB storage")
            return item

        try:
            existing_product = await self._get_existing_product(str(product_id))

            if existing_product:
                await self._update_product(existing_product, adapter)
                product = existing_product
                logger.debug(f"Updated existing product: {product_id}")
            else:
                product = await self._create_product(adapter)
                logger.debug(f"Created new product: {product_id}")

            supplier = await self._create_or_update_supplier(adapter)
            if supplier and product:
                product.supplier_id = supplier.id

            await self._create_skus(product, adapter)
            await self._create_images(product, adapter)

            await self.session.commit()

        except Exception as e:
            if self.session:
                await self.session.rollback()
            logger.error(f"Error processing item {product_id}: {e}", exc_info=True)

        return item

    async def _get_existing_product(self, source_product_id: str) -> Any:
        from sqlalchemy import select
        stmt = select(Product).where(Product.source_product_id == source_product_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _create_product(self, adapter: ItemAdapter) -> Any:
        min_price = adapter.get("min_price") or Decimal("0.00")
        max_price = adapter.get("max_price") or min_price

        product = Product(
            name=adapter.get("title", "")[:500],
            description=None,
            cost_price=Decimal(str(min_price)) if min_price else Decimal("0.00"),
            sale_price=Decimal(str(max_price)) if max_price else None,
            status="draft",
            source_url=adapter.get("source_url"),
            source_product_id=str(adapter.get("product_id")),
            score=Decimal(str(adapter.get("rating"))) if adapter.get("rating") else None,
        )

        self.session.add(product)
        await self.session.flush()
        return product

    async def _update_product(self, product: Any, adapter: ItemAdapter) -> None:
        if adapter.get("title"):
            product.name = adapter["title"][:500]

        min_price = adapter.get("min_price")
        if min_price:
            product.cost_price = Decimal(str(min_price))

        max_price = adapter.get("max_price")
        if max_price:
            product.sale_price = Decimal(str(max_price))

        if adapter.get("rating"):
            product.score = Decimal(str(adapter.get("rating")))

        if adapter.get("source_url"):
            product.source_url = adapter["source_url"]

    async def _create_or_update_supplier(self, adapter: ItemAdapter) -> Any:
        from sqlalchemy import select

        supplier_name = adapter.get("supplier_name")
        supplier_id = adapter.get("supplier_id")

        if not supplier_name:
            return None

        stmt = select(Supplier)
        if supplier_id:
            stmt = stmt.where(Supplier.supplier_code == str(supplier_id))
        else:
            stmt = stmt.where(Supplier.name == supplier_name)

        result = await self.session.execute(stmt)
        existing_supplier = result.scalar_one_or_none()

        if existing_supplier:
            if adapter.get("supplier_location"):
                existing_supplier.location = adapter["supplier_location"]
            if adapter.get("rating"):
                existing_supplier.rating = Decimal(str(adapter["rating"]))
            return existing_supplier

        supplier = Supplier(
            name=supplier_name[:300],
            supplier_code=str(supplier_id) if supplier_id else None,
            location=adapter.get("supplier_location"),
            rating=Decimal(str(adapter["rating"])) if adapter.get("rating") else None,
            is_active=True,
        )

        self.session.add(supplier)
        await self.session.flush()
        return supplier

    async def _create_skus(self, product: Any, adapter: ItemAdapter) -> None:
        sku_specs = adapter.get("sku_specs", [])

        if not sku_specs:
            min_price = adapter.get("min_price") or Decimal("0.00")
            default_sku = ProductSKU(
                product_id=product.id,
                sku_code=f"{product.source_product_id}-default",
                specs=None,
                cost_price=Decimal(str(min_price)),
                sale_price=Decimal(str(adapter.get("max_price"))) if adapter.get("max_price") else None,
                stock=adapter.get("min_order_qty", 0) or 0,
            )
            self.session.add(default_sku)
            return

        for idx, spec in enumerate(sku_specs):
            if isinstance(spec, dict):
                sku = ProductSKU(
                    product_id=product.id,
                    sku_code=spec.get("sku_id", f"{product.source_product_id}-{idx}"),
                    specs=spec.get("attributes"),
                    cost_price=Decimal(str(spec.get("price", adapter.get("min_price", "0.00")))),
                    sale_price=Decimal(str(spec.get("price"))) if spec.get("price") else None,
                    stock=spec.get("stock", 0),
                )
            else:
                sku = ProductSKU(
                    product_id=product.id,
                    sku_code=f"{product.source_product_id}-{idx}",
                    specs={"value": str(spec)},
                    cost_price=Decimal(str(adapter.get("min_price", "0.00"))),
                    stock=0,
                )
            self.session.add(sku)

    async def _create_images(self, product: Any, adapter: ItemAdapter) -> None:
        main_image_url = adapter.get("main_image_url")
        if main_image_url:
            main_image = ProductImage(
                product_id=product.id,
                url=main_image_url[:1000],
                image_type="main",
                sort_order=0,
            )
            self.session.add(main_image)

        image_urls = adapter.get("image_urls", [])
        if isinstance(image_urls, str):
            import json
            try:
                image_urls = json.loads(image_urls)
            except json.JSONDecodeError:
                image_urls = []

        for idx, url in enumerate(image_urls, start=1):
            if url and str(url) != main_image_url:
                image = ProductImage(
                    product_id=product.id,
                    url=str(url)[:1000],
                    image_type="gallery",
                    sort_order=idx,
                )
                self.session.add(image)
