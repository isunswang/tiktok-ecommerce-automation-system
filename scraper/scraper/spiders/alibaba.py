"""1688 product search spider."""

import re

import scrapy

from scraper.items import AlibabaProductItem


class AlibabaSpider(scrapy.Spider):
    """Spider for crawling 1688.com product listings and details."""

    name = "alibaba"
    allowed_domains = ["1688.com", "s.1688.com"]

    # Base URLs
    SEARCH_URL = "https://s.1688.com/selloffer/offer_search.htm"
    DETAIL_URL = "https://detail.1688.com/offer/{product_id}.html"

    def __init__(self, keyword: str = "", max_pages: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.keyword = keyword
        self.max_pages = int(max_pages)

    def start_requests(self):
        """Start by searching for the keyword."""
        if not self.keyword:
            self.logger.error("No search keyword provided. Use -a keyword='your keyword'")
            return

        for page in range(1, self.max_pages + 1):
            yield scrapy.Request(
                url=self.SEARCH_URL,
                callback=self.parse_search,
                cb_kwargs={"page": page},
                dont_filter=True,
                meta={
                    "search_params": {
                        "keywords": self.keyword,
                        "pageSize": 60,
                        "beginPage": page,
                    },
                },
            )

    def parse_search(self, response, page):
        """Parse search results page and extract product listings."""
        # In MOCK mode, use mock data
        mock_mode = self.settings.getbool("ALIBABA_1688_MOCK_MODE", True)

        if mock_mode:
            yield from self._parse_mock_search(page)
            return

        # TODO: Implement actual 1688 search page parsing
        # This will parse the HTML response from 1688.com
        self.logger.info(f"Parsing search page {page} for keyword: {self.keyword}")

        # Extract product cards from search results
        product_cards = response.css("div.sm-offer-item, div.offer-item, div.sw-item")
        self.logger.info(f"Found {len(product_cards)} product cards on page {page}")

        for card in product_cards:
            item = self._parse_product_card(card)
            if item:
                yield item
                # Optionally follow to detail page
                # if item.get("product_id"):
                #     yield response.follow(
                #         self.DETAIL_URL.format(product_id=item["product_id"]),
                #         callback=self.parse_detail,
                #         cb_kwargs={"item": item},
                #     )

    def parse_detail(self, response, item):
        """Parse product detail page for additional information."""
        # TODO: Implement actual 1688 detail page parsing
        adapter = item

        # Extract SKU specs
        sku_data = response.css("div.obj-content, div.sku-attr-list ::text").getall()
        adapter["sku_specs"] = sku_data

        # Extract detail HTML for later processing
        adapter["detail_html"] = response.css("div.detail-content").get()

        yield adapter

    def _parse_product_card(self, card) -> AlibabaProductItem | None:
        """Parse a single product card from search results."""
        try:
            title = card.css("a.title, div.title a ::text").get("")
            if not title:
                return None

            price_text = card.css("div.price, span.price ::text").get("")
            price_range = self._clean_price(price_text)
            prices = price_text.split("-") if price_text else ["0", "0"]

            return AlibabaProductItem({
                "source_url": card.css("a.title::attr(href), div.title a::attr(href)").get(""),
                "product_id": self._extract_product_id(
                    card.css("a.title::attr(href), div.title a::attr(href)").get("")
                ),
                "title": title.strip(),
                "price_range": price_range,
                "min_price": float(prices[0].replace(",", "")) if prices[0] else 0,
                "max_price": float(prices[1].replace(",", "")) if len(prices) > 1 else float(prices[0] or 0),
                "sales_count": self._parse_sales(card.css("div.sale, span.sale ::text").get("")),
                "supplier_name": card.css("div.company-name, span.company-name ::text").get("").strip(),
                "supplier_location": card.css("div.location, span.location ::text").get("").strip(),
                "main_image_url": card.css("img.pic, img.image ::attr(src)").get(""),
            })
        except Exception as e:
            self.logger.error(f"Error parsing product card: {e}")
            return None

    def _parse_mock_search(self, page):
        """Generate mock product items for development/testing."""
        import random
        from faker import Faker

        fake = Faker("zh_CN")
        categories = ["电子产品", "家居用品", "服装鞋帽", "美妆个护", "运动户外", "食品饮料", "母婴用品", "办公用品"]
        locations = ["广州", "深圳", "义乌", "杭州", "温州", "东莞", "佛山", "宁波"]

        for i in range(10):
            product_id = fake.random_int(min=100000000, max=999999999)
            min_p = round(random.uniform(5, 200), 2)
            max_p = round(min_p * random.uniform(1.2, 3.0), 2)

            yield AlibabaProductItem({
                "source_url": f"https://detail.1688.com/offer/{product_id}.html",
                "product_id": str(product_id),
                "title": f"{self.keyword} {fake.sentence(nb_words=8)} 批发",
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
                "image_urls": [f"https://placehold.co/400x400?text=Product+{product_id}_{j}" for j in range(1, 6)],
                "category": random.choice(categories),
            })

        self.logger.info(f"Generated {10} mock items for page {page}")

    @staticmethod
    def _clean_price(price_text: str) -> str:
        """Clean price text."""
        if not price_text:
            return "0-0"
        cleaned = re.sub(r"[^\d.\-]", "", price_text.strip())
        return cleaned if cleaned else "0-0"

    @staticmethod
    def _extract_product_id(url: str) -> str:
        """Extract product ID from URL."""
        if not url:
            return ""
        match = re.search(r"offer/(\d+)\.html", url)
        return match.group(1) if match else ""

    @staticmethod
    def _parse_sales(text: str) -> int:
        """Parse sales count text (e.g. '1000+件' -> 1000)."""
        if not text:
            return 0
        match = re.search(r"(\d+)", text.replace(",", ""))
        return int(match.group(1)) if match else 0
