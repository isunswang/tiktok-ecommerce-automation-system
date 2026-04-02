"""Database pipeline for storing scraped items into PostgreSQL."""

import logging
import uuid
from decimal import Decimal
from typing import Any

from itemadapter import ItemAdapter
from scrapy import Spider
from scrapy.exceptions import DropItem
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import async_session_factory
from backend.app.models.product import Product, ProductImage, ProductSKU, Supplier
from scraper.items import AlibabaProductItem

logger = logging.getLogger(__name__)


class DatabasePipeline:
    """Async Scrapy pipeline for storing scraped products into PostgreSQL.
    
    This pipeline handles:
    - Deduplication based on source_product_id
    - Creating/updating Product records
    - Creating ProductSKU records (multiple SKUs)
    - Creating/updating Supplier records
    - Creating ProductImage records
    
    Attributes:
        session: SQLAlchemy async session for database operations.
    """
    
    def __init__(self) -> None:
        """Initialize the pipeline with a None session."""
        self.session: AsyncSession | None = None
    
    async def open_spider(self, spider: Spider) -> None:
        """Create async session when spider opens.
        
        Args:
            spider: The Scrapy spider instance.
        """
        self.session = async_session_factory()
        logger.info(f"DatabasePipeline opened for spider: {spider.name}")
    
    async def close_spider(self, spider: Spider) -> None:
        """Close async session when spider closes.
        
        Args:
            spider: The Scrapy spider instance.
        """
        if self.session:
            await self.session.close()
            logger.info(f"DatabasePipeline closed for spider: {spider.name}")
    
    async def process_item(self, item: AlibabaProductItem, spider: Spider) -> AlibabaProductItem:
        """Process and store item in database.
        
        Args:
            item: The scraped item containing product data.
            spider: The Scrapy spider instance.
            
        Returns:
            The processed item.
            
        Raises:
            DropItem: If the item is invalid or cannot be stored.
        """
        if not self.session:
            logger.error("Database session not initialized")
            return item
        
        adapter = ItemAdapter(item)
        product_id = adapter.get("product_id")
        
        if not product_id:
            logger.warning("Item missing product_id, skipping")
            return item
        
        try:
            # Check for existing product (deduplication)
            existing_product = await self._get_existing_product(str(product_id))
            
            if existing_product:
                # Update existing product
                await self._update_product(existing_product, adapter)
                product = existing_product
                logger.info(f"Updated existing product: {product_id}")
            else:
                # Create new product
                product = await self._create_product(adapter)
                logger.info(f"Created new product: {product_id}")
            
            # Create/update supplier
            supplier = await self._create_or_update_supplier(adapter)
            if supplier and product:
                product.supplier_id = supplier.id
            
            # Create SKUs
            await self._create_skus(product, adapter)
            
            # Create images
            await self._create_images(product, adapter)
            
            await self.session.commit()
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error processing item {product_id}: {e}", exc_info=True)
            # Don't drop the item, just log the error
        
        return item
    
    async def _get_existing_product(self, source_product_id: str) -> Product | None:
        """Check if product already exists by source_product_id.
        
        Args:
            source_product_id: The source platform's product ID.
            
        Returns:
            Existing Product or None.
        """
        stmt = select(Product).where(Product.source_product_id == source_product_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _create_product(self, adapter: ItemAdapter) -> Product:
        """Create a new Product record.
        
        Args:
            adapter: ItemAdapter containing product data.
            
        Returns:
            The created Product instance.
        """
        # Parse price range
        min_price = adapter.get("min_price") or Decimal("0.00")
        max_price = adapter.get("max_price") or min_price
        
        product = Product(
            name=adapter.get("title", "")[:500],
            description=None,  # Can be extracted from detail_html later
            cost_price=Decimal(str(min_price)) if min_price else Decimal("0.00"),
            sale_price=Decimal(str(max_price)) if max_price else None,
            status="draft",
            source_url=adapter.get("source_url"),
            source_product_id=str(adapter.get("product_id")),
            score=Decimal(str(adapter.get("rating"))) if adapter.get("rating") else None,
        )
        
        self.session.add(product)
        await self.session.flush()  # Get the ID
        return product
    
    async def _update_product(self, product: Product, adapter: ItemAdapter) -> None:
        """Update existing Product record with new data.
        
        Args:
            product: The existing Product instance.
            adapter: ItemAdapter containing updated product data.
        """
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
    
    async def _create_or_update_supplier(self, adapter: ItemAdapter) -> Supplier | None:
        """Create or update Supplier record.
        
        Args:
            adapter: ItemAdapter containing supplier data.
            
        Returns:
            The created or updated Supplier instance, or None.
        """
        supplier_name = adapter.get("supplier_name")
        supplier_id = adapter.get("supplier_id")
        
        if not supplier_name:
            return None
        
        # Check if supplier exists by name or supplier_code
        stmt = select(Supplier)
        if supplier_id:
            stmt = stmt.where(Supplier.supplier_code == str(supplier_id))
        else:
            stmt = stmt.where(Supplier.name == supplier_name)
        
        result = await self.session.execute(stmt)
        existing_supplier = result.scalar_one_or_none()
        
        if existing_supplier:
            # Update existing supplier
            if adapter.get("supplier_location"):
                existing_supplier.location = adapter["supplier_location"]
            if adapter.get("rating"):
                existing_supplier.rating = Decimal(str(adapter["rating"]))
            return existing_supplier
        
        # Create new supplier
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
    
    async def _create_skus(self, product: Product, adapter: ItemAdapter) -> None:
        """Create ProductSKU records for the product.
        
        Args:
            product: The Product instance.
            adapter: ItemAdapter containing SKU data.
        """
        sku_specs = adapter.get("sku_specs", [])
        
        if not sku_specs:
            # Create a default SKU if no specs provided
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
        
        # Create SKUs from specs
        for idx, spec in enumerate(sku_specs):
            sku = ProductSKU(
                product_id=product.id,
                sku_code=spec.get("sku_id", f"{product.source_product_id}-{idx}"),
                specs=spec.get("attributes"),
                cost_price=Decimal(str(spec.get("price", adapter.get("min_price", "0.00")))),
                sale_price=Decimal(str(spec.get("price"))) if spec.get("price") else None,
                stock=spec.get("stock", 0),
            )
            self.session.add(sku)
    
    async def _create_images(self, product: Product, adapter: ItemAdapter) -> None:
        """Create ProductImage records for the product.
        
        Args:
            product: The Product instance.
            adapter: ItemAdapter containing image data.
        """
        # Create main image
        main_image_url = adapter.get("main_image_url")
        if main_image_url:
            main_image = ProductImage(
                product_id=product.id,
                url=main_image_url[:1000],
                image_type="main",
                sort_order=0,
            )
            self.session.add(main_image)
        
        # Create gallery images
        image_urls = adapter.get("image_urls", [])
        if isinstance(image_urls, str):
            # Handle case where image_urls might be a string
            import json
            try:
                image_urls = json.loads(image_urls)
            except json.JSONDecodeError:
                image_urls = []
        
        for idx, url in enumerate(image_urls, start=1):
            if url and url != main_image_url:
                image = ProductImage(
                    product_id=product.id,
                    url=str(url)[:1000],
                    image_type="gallery",
                    sort_order=idx,
                )
                self.session.add(image)
