"""Scrapy item pipelines for data processing and storage."""

import json
import logging
from datetime import datetime, timezone

from itemadapter import ItemAdapter

logger = logging.getLogger(__name__)


class DataCleanPipeline:
    """Clean and normalize scraped data."""

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # Strip whitespace from text fields
        for field in ["title", "supplier_name", "supplier_location", "category"]:
            if adapter.get(field):
                adapter[field] = adapter[field].strip()

        # Add crawl timestamp
        if not adapter.get("crawled_at"):
            adapter["crawled_at"] = datetime.now(timezone.utc).isoformat()

        return item


class DuplicatesFilterPipeline:
    """Filter out duplicate items based on product_id."""

    def __init__(self):
        self.seen_ids: set[str] = set()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        product_id = adapter.get("product_id")
        if product_id and product_id in self.seen_ids:
            logger.debug(f"Duplicate item filtered: {product_id}")
            raise DropItem(f"Duplicate product_id: {product_id}")
        self.seen_ids.add(product_id)
        return item


class JsonWriterPipeline:
    """Write scraped items to JSON file (for development/debugging)."""

    def __init__(self, output_file: str = "output/products.json"):
        self.output_file = output_file
        self.file = None

    def open_spider(self, spider):
        self.file = open(self.output_file, "w", encoding="utf-8")

    def close_spider(self, spider):
        if self.file:
            self.file.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        line = json.dumps(dict(adapter), ensure_ascii=False, default=str) + "\n"
        self.file.write(line)
        return item


class DatabaseStoragePipeline:
    """Store scraped items into PostgreSQL database.

    This pipeline is a placeholder - actual DB storage will use
    the backend service API or direct SQLAlchemy async calls.
    """

    def process_item(self, item, spider):
        # TODO: Implement database storage
        # Will connect to backend API or use shared database
        logger.info(f"Would store item: {item.get('product_id')}")
        return item


class DropItem(Exception):
    """Raised when an item should be dropped from the pipeline."""
    pass
