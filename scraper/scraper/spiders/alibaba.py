"""1688 product search spider with real HTML parsing support."""

import logging
import random
from typing import AsyncIterator, Optional
from urllib.parse import urlencode

import scrapy
from scrapy.http import Response

from scraper.items import AlibabaProductItem
from scraper.parsers.alibaba_parser import AlibabaParser

logger = logging.getLogger(__name__)


class AlibabaSpider(scrapy.Spider):
    """Spider for crawling 1688.com product listings and details.

    Supports two modes:
    - HTTP mode: Direct HTTP requests with HTML parsing
    - Playwright mode: Browser rendering for dynamic content

    Usage:
        # Basic search
        scrapy crawl alibaba -a keyword="手机壳"

        # With pagination
        scrapy crawl alibaba -a keyword="手机壳" -a max_pages=10

        # With Playwright rendering
        scrapy crawl alibaba -a keyword="手机壳" -a use_playwright=true
    """

    name = "alibaba"
    allowed_domains = ["1688.com", "s.1688.com", "detail.1688.com", "m.1688.com"]

    # URL templates
    SEARCH_URL = "https://s.1688.com/selloffer/offer_search.htm"
    DETAIL_URL = "https://detail.1688.com/offer/{product_id}.html"
    MOBILE_SEARCH_URL = "https://m.1688.com/offer_search/-{keyword}.html"

    # Custom settings for this spider
    custom_settings = {
        "CONCURRENT_REQUESTS": 2,
        "DOWNLOAD_DELAY": 3.0,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "COOKIES_ENABLED": False,
        "RETRY_TIMES": 3,
        "RETRY_HTTP_CODES": [500, 502, 503, 504, 403, 429],
    }

    def __init__(
        self,
        keyword: str = "",
        max_pages: int = 5,
        use_playwright: bool = False,
        mock_mode: bool = False,
        crawl_details: bool = False,
        **kwargs,
    ):
        """Initialize spider.

        Args:
            keyword: Search keyword (required for real crawling)
            max_pages: Maximum number of pages to crawl
            use_playwright: Whether to use Playwright for rendering
            mock_mode: Whether to use mock data instead of real crawling
            crawl_details: Whether to crawl product detail pages
        """
        super().__init__(**kwargs)
        self.keyword = keyword
        self.max_pages = int(max_pages)
        self.use_playwright = use_playwright
        self.mock_mode = mock_mode
        self.crawl_details = crawl_details
        self.stats = {"pages_crawled": 0, "products_found": 0, "products_saved": 0}

    def start_requests(self) -> AsyncIterator[scrapy.Request]:
        """Generate initial search requests."""
        if self.mock_mode:
            yield from self._generate_mock_data()
            return

        if not self.keyword:
            self.logger.error("No search keyword provided. Use -a keyword='your keyword'")
            return

        self.logger.info(
            f"Starting crawl for keyword: '{self.keyword}', "
            f"max_pages: {self.max_pages}, playwright: {self.use_playwright}"
        )

        # Generate search requests for each page
        for page in range(1, self.max_pages + 1):
            params = {
                "keywords": self.keyword,
                "n": "y",
                "netType": "1%2C11",
                "spm": "a260k.home2024search.0",
                "beginPage": page,
            }
            url = f"{self.SEARCH_URL}?{urlencode(params)}"

            request = scrapy.Request(
                url=url,
                callback=self.parse_search,
                meta={
                    "page": page,
                    "keyword": self.keyword,
                    "dont_merge_cookies": True,
                },
                errback=self.errback_handler,
            )

            if self.use_playwright:
                request.meta["playwright"] = True
                request.meta["playwright_include_page"] = True
                request.meta["playwright_page_goto_kwargs"] = {
                    "wait_until": "networkidle",
                    "timeout": 30000,
                }

            yield request

    def parse_search(self, response: Response) -> AsyncIterator[scrapy.Request | AlibabaProductItem]:
        """Parse search results page and extract product listings.

        Args:
            response: Scrapy response object

        Yields:
            Product items or detail page requests
        """
        page = response.meta.get("page", 1)
        self.stats["pages_crawled"] += 1

        self.logger.info(f"Parsing search page {page} for keyword: {self.keyword}")

        # Parse products using our parser
        products = AlibabaParser.parse_search_results(response.text, self.keyword)

        if not products:
            self.logger.warning(f"No products found on page {page}, trying fallback selectors")
            # Try alternative parsing approaches
            products = self._fallback_parse(response)

        self.logger.info(f"Found {len(products)} products on page {page}")
        self.stats["products_found"] += len(products)

        for product in products:
            self.stats["products_saved"] += 1

            # Yield item for pipeline processing
            item = AlibabaProductItem()
            item.update(product)

            # Optionally crawl detail page for more data
            if self.crawl_details and product.get("product_id"):
                detail_url = self.DETAIL_URL.format(product_id=product["product_id"])
                yield scrapy.Request(
                    url=detail_url,
                    callback=self.parse_detail,
                    meta={"item": item, "dont_merge_cookies": True},
                    errback=self.errback_handler,
                    priority=10,  # Lower priority than search pages
                )
            else:
                yield item

    def parse_detail(self, response: Response) -> AlibabaProductItem:
        """Parse product detail page for additional information.

        Args:
            response: Scrapy response object

        Returns:
            Enhanced product item with detail data
        """
        item = response.meta.get("item", AlibabaProductItem())
        product_id = item.get("product_id", "")

        self.logger.debug(f"Parsing detail page for product: {product_id}")

        # Parse detail page
        detail_data = AlibabaParser.parse_product_detail(response.text, product_id)

        # Merge detail data into item
        if detail_data.get("sku_specs"):
            item["sku_specs"] = detail_data["sku_specs"]
        if detail_data.get("image_urls"):
            # Merge images, deduplicate
            existing_images = item.get("image_urls", [])
            all_images = list(set(existing_images + detail_data["image_urls"]))
            item["image_urls"] = all_images
        if detail_data.get("detail_html") and not item.get("detail_html"):
            item["detail_html"] = detail_data["detail_html"]

        return item

    def _fallback_parse(self, response: Response) -> list[dict]:
        """Fallback parsing when main parser fails.

        Uses simpler, more generic selectors.
        """
        products = []

        # Try to find any product-like elements
        for card in response.css("div[class*='item'], div[class*='offer'], div[class*='product']"):
            title = card.css("a[title]::attr(title)").get() or card.css("a::attr(title)").get()
            if not title:
                continue

            href = card.css("a[href*='detail.1688.com']::attr(href)").get() or card.css("a::attr(href)").get()
            product_id = AlibabaParser._extract_product_id(href) if href else ""

            if not product_id:
                continue

            price_text = card.css("[class*='price']::text").get() or ""
            price_range, min_price, max_price = AlibabaParser._parse_price(price_text)

            products.append({
                "product_id": product_id,
                "title": title.strip(),
                "source_url": f"https://detail.1688.com/offer/{product_id}.html",
                "price_range": price_range,
                "min_price": min_price,
                "max_price": max_price,
                "sales_count": 0,
                "supplier_name": card.css("[class*='company']::text").get() or "",
                "supplier_location": card.css("[class*='location']::text").get() or "",
                "main_image_url": card.css("img::attr(src)").get() or card.css("img::attr(data-src)").get() or "",
            })

        return products

    def _generate_mock_data(self) -> AsyncIterator[AlibabaProductItem]:
        """Generate mock product items for development/testing."""
        from datetime import datetime, timezone

        from faker import Faker

        self.logger.info("Generating mock product data")

        fake = Faker("zh_CN")
        categories = ["电子产品", "家居用品", "服装鞋帽", "美妆个护", "运动户外"]
        locations = ["广州", "深圳", "义乌", "杭州", "温州", "东莞", "佛山", "宁波"]

        for i in range(20):
            product_id = fake.random_int(min=100000000, max=999999999)
            min_p = round(random.uniform(5, 200), 2)
            max_p = round(min_p * random.uniform(1.2, 3.0), 2)

            item = AlibabaProductItem({
                "source_url": f"https://detail.1688.com/offer/{product_id}.html",
                "product_id": str(product_id),
                "title": f"{self.keyword or '商品'} {fake.sentence(nb_words=6)} 批发",
                "price_range": f"{min_p}-{max_p}",
                "min_price": min_p,
                "max_price": max_p,
                "sales_count": fake.random_int(min=10, max=50000),
                "supplier_name": f"{fake.company()}（{random.choice(locations)}）",
                "supplier_id": str(fake.random_int(min=10000, max=99999)),
                "supplier_location": random.choice(locations),
                "min_order_qty": random.choice([1, 2, 5, 10, 50, 100]),
                "delivery_days": random.choice([1, 2, 3, 5, 7, 15]),
                "rating": round(random.uniform(3.5, 5.0), 1),
                "main_image_url": f"https://placehold.co/400x400?text=Product+{product_id}",
                "image_urls": [f"https://placehold.co/400x400?text=Product+{product_id}_{j}" for j in range(1, 4)],
                "category": random.choice(categories),
                "crawled_at": datetime.now(timezone.utc).isoformat(),
            })

            yield item
            self.stats["products_saved"] += 1

        self.logger.info(f"Generated {self.stats['products_saved']} mock items")

    def errback_handler(self, failure):
        """Handle request failures."""
        request = failure.request
        self.logger.error(
            f"Request failed: {request.url}, "
            f"error: {failure.value}"
        )
        # Could implement retry logic here

    def closed(self, reason: str):
        """Called when spider closes."""
        self.logger.info(
            f"Spider closed. Stats: "
            f"pages_crawled={self.stats['pages_crawled']}, "
            f"products_found={self.stats['products_found']}, "
            f"products_saved={self.stats['products_saved']}"
        )


class AlibabaDetailSpider(scrapy.Spider):
    """Spider for crawling individual 1688 product detail pages.

    Usage:
        scrapy crawl alibaba_detail -a product_ids="1234567890,0987654321"
    """

    name = "alibaba_detail"
    allowed_domains = ["1688.com", "detail.1688.com"]

    DETAIL_URL = "https://detail.1688.com/offer/{product_id}.html"

    def __init__(self, product_ids: str = "", **kwargs):
        super().__init__(**kwargs)
        self.product_ids = [pid.strip() for pid in product_ids.split(",") if pid.strip()]

    def start_requests(self):
        if not self.product_ids:
            self.logger.error("No product IDs provided. Use -a product_ids='id1,id2'")
            return

        for product_id in self.product_ids:
            url = self.DETAIL_URL.format(product_id=product_id)
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta={"product_id": product_id},
            )

    def parse_detail(self, response):
        product_id = response.meta.get("product_id")
        detail_data = AlibabaParser.parse_product_detail(response.text, product_id)

        item = AlibabaProductItem()
        item.update(detail_data)
        return item
