"""1688 HTML parsers for extracting product data."""

import json
import re
from decimal import Decimal
from typing import Optional

import parsel


class AlibabaParser:
    """Parser for 1688.com product pages.

    Supports parsing:
    - Search results page (product listings)
    - Product detail page (full product info)
    """

    # CSS selectors for search results (may change, keep updated)
    SEARCH_SELECTORS = {
        # Modern 1688 search page selectors
        "product_card": [
            "div.sm-offer-item",
            "div.offer-item",
            "div.list-item",
            "div.item-offer",
            "div.sw-offer-item",
        ],
        "title": [
            "a.title",
            "div.title a",
            "a.subject-link",
            "h4.title a",
            "div.offer-title a",
        ],
        "price": [
            "div.price",
            "span.price",
            "div.price-original",
            "span.price-value",
            "div.offer-price",
        ],
        "sales": [
            "div.sale",
            "span.sale",
            "div.offer-sale",
            "span.trade-count",
        ],
        "company": [
            "div.company-name",
            "span.company-name",
            "div.shop-name",
            "a.company-link",
        ],
        "location": [
            "div.location",
            "span.location",
            "div.area",
            "span.send-address",
        ],
        "image": [
            "img.pic",
            "img.image",
            "img.offer-img",
            "img.main-img",
        ],
        "link": [
            "a.title",
            "a.subject-link",
            "a.offer-link",
        ],
    }

    # CSS selectors for product detail page
    DETAIL_SELECTORS = {
        "title": [
            "h1.title",
            "div.detail-title",
            "h1.offer-title",
            "div.mod-detail-title h1",
        ],
        "price": [
            "div.price-value",
            "span.price-value",
            "div.offer-price",
            "div.mod-detail-price .value",
        ],
        "sku_container": [
            "div.sku-wrapper",
            "div.sku-list",
            "div.obj-sku",
            "div.mod-detail-sku",
        ],
        "images": [
            "div.detail-gallery img",
            "div.vertical-imgs img",
            "div.mod-detail-gallery img",
            "ul.detail-pic-list img",
        ],
        "description": [
            "div.detail-content",
            "div.offer-detail",
            "div.mod-detail-description",
            "div.desc-content",
        ],
        "company": [
            "div.shop-name",
            "div.supplier-name",
            "a.company-name",
        ],
        "attributes": [
            "div.attributes-list",
            "div.obj-attributes",
            "div.mod-detail-attributes",
        ],
    }

    @classmethod
    def parse_search_results(cls, html: str, keyword: str) -> list[dict]:
        """Parse 1688 search results page.

        Args:
            html: Raw HTML content
            keyword: Search keyword used

        Returns:
            List of product data dictionaries
        """
        selector = parsel.Selector(text=html)
        products = []

        # Try multiple product card selectors
        product_cards = []
        for card_selector in cls.SEARCH_SELECTORS["product_card"]:
            cards = selector.css(card_selector)
            if cards:
                product_cards = cards
                break

        if not product_cards:
            # Fallback: try to extract JSON data from page source
            json_products = cls._extract_json_products(html)
            if json_products:
                return json_products
            return []

        for card in product_cards:
            try:
                product = cls._parse_product_card(card)
                if product and product.get("product_id"):
                    products.append(product)
            except Exception as e:
                # Log error but continue processing other cards
                continue

        return products

    @classmethod
    def _parse_product_card(cls, card: parsel.Selector) -> Optional[dict]:
        """Parse a single product card from search results.

        Args:
            card: Parsel selector for product card

        Returns:
            Product data dictionary or None
        """
        title = cls._get_first_match(card, cls.SEARCH_SELECTORS["title"])
        if not title:
            return None

        # Extract URL and product ID
        link = cls._get_first_match_attr(card, cls.SEARCH_SELECTORS["link"], "href")
        product_id = cls._extract_product_id(link) if link else None

        # Parse price
        price_text = cls._get_first_match(card, cls.SEARCH_SELECTORS["price"])
        price_range, min_price, max_price = cls._parse_price(price_text)

        # Parse other fields
        sales = cls._parse_sales(cls._get_first_match(card, cls.SEARCH_SELECTORS["sales"]))
        company = cls._get_first_match(card, cls.SEARCH_SELECTORS["company"])
        location = cls._get_first_match(card, cls.SEARCH_SELECTORS["location"])
        image = cls._get_first_match_attr(card, cls.SEARCH_SELECTORS["image"], "src")

        return {
            "source_url": f"https:{link}" if link and link.startswith("//") else link or "",
            "product_id": product_id or "",
            "title": title.strip(),
            "price_range": price_range,
            "min_price": min_price,
            "max_price": max_price,
            "sales_count": sales,
            "supplier_name": company.strip() if company else "",
            "supplier_location": location.strip() if location else "",
            "main_image_url": cls._normalize_image_url(image) if image else "",
        }

    @classmethod
    def parse_product_detail(cls, html: str, product_id: str) -> dict:
        """Parse 1688 product detail page.

        Args:
            html: Raw HTML content
            product_id: 1688 product ID

        Returns:
            Product detail data dictionary
        """
        selector = parsel.Selector(text=html)

        # Try to extract JSON-LD data first
        json_data = cls._extract_json_ld_data(html)
        if json_data:
            return json_data

        title = cls._get_first_match(selector, cls.DETAIL_SELECTORS["title"])
        price_text = cls._get_first_match(selector, cls.DETAIL_SELECTORS["price"])

        # Extract images
        images = []
        for img_selector in cls.DETAIL_SELECTORS["images"]:
            img_elements = selector.css(img_selector)
            for img in img_elements:
                src = img.css("::attr(src)").get() or img.css("::attr(data-src)").get()
                if src:
                    images.append(cls._normalize_image_url(src))
            if images:
                break

        # Extract SKU info
        sku_data = cls._extract_sku_data(selector, html)

        # Extract description
        description = selector.css("div.detail-content").get() or ""

        # Extract company info
        company = cls._get_first_match(selector, cls.DETAIL_SELECTORS["company"])

        return {
            "product_id": product_id,
            "title": title.strip() if title else "",
            "price_range": price_text or "",
            "min_price": Decimal("0"),
            "max_price": Decimal("0"),
            "image_urls": images,
            "main_image_url": images[0] if images else "",
            "sku_specs": sku_data,
            "detail_html": description,
            "supplier_name": company.strip() if company else "",
        }

    @classmethod
    def _extract_json_products(cls, html: str) -> list[dict]:
        """Extract product data from embedded JSON in page source.

        1688 often embeds product data in JavaScript variables.
        """
        products = []

        # Pattern 1: window.__INITIAL_DATA__ = {...}
        patterns = [
            r'window\.__INITIAL_DATA__\s*=\s*({.*?});',
            r'window\.pageData\s*=\s*({.*?});',
            r'var\s+offerListData\s*=\s*({.*?});',
            r'"offerList"\s*:\s*(\[.*?\])',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    # Navigate to product list
                    product_list = (
                        data.get("offerList", [])
                        or data.get("data", {}).get("offerList", [])
                        or data.get("globalData", {}).get("offerList", [])
                    )
                    if isinstance(product_list, list):
                        for item in product_list:
                            product = cls._normalize_json_product(item)
                            if product:
                                products.append(product)
                        if products:
                            return products
                except (json.JSONDecodeError, AttributeError):
                    continue

        return products

    @classmethod
    def _normalize_json_product(cls, item: dict) -> Optional[dict]:
        """Normalize JSON product data to standard format."""
        try:
            product_id = item.get("id") or item.get("offerId") or item.get("product_id")
            if not product_id:
                return None

            title = item.get("subject") or item.get("title") or ""

            # Price handling
            price_info = item.get("price", {})
            if isinstance(price_info, dict):
                min_price = Decimal(str(price_info.get("minPrice", 0) or 0))
                max_price = Decimal(str(price_info.get("maxPrice", min_price) or min_price))
            else:
                price_str = str(price_info) if price_info else "0"
                _, min_price, max_price = cls._parse_price(price_str)

            return {
                "product_id": str(product_id),
                "title": title,
                "source_url": f"https://detail.1688.com/offer/{product_id}.html",
                "min_price": min_price,
                "max_price": max_price,
                "price_range": f"{min_price}-{max_price}",
                "sales_count": item.get("tradeCount", 0) or 0,
                "supplier_name": item.get("companyName", "") or "",
                "supplier_id": str(item.get("companyId", "") or ""),
                "image_urls": item.get("imageUrls", []) if isinstance(item.get("imageUrls"), list) else [],
                "main_image_url": item.get("picUrl", "") or "",
            }
        except Exception:
            return None

    @classmethod
    def _extract_json_ld_data(cls, html: str) -> Optional[dict]:
        """Extract JSON-LD structured data if available."""
        pattern = r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                # Normalize to our format
                return {
                    "title": data.get("name", ""),
                    "price_range": str(data.get("offers", {}).get("price", "")),
                }
            except json.JSONDecodeError:
                pass
        return None

    @classmethod
    def _extract_sku_data(cls, selector: parsel.Selector, html: str) -> list[dict]:
        """Extract SKU specification data."""
        skus = []

        # Try to find SKU data in JavaScript
        patterns = [
            r'skuData\s*=\s*({.*?});',
            r'var\s+skuInfo\s*=\s*({.*?});',
            r'"skuMap"\s*:\s*({.*?})',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    if isinstance(data, dict):
                        for sku_id, sku_info in data.items():
                            skus.append({
                                "sku_id": sku_id,
                                "attributes": sku_info.get("attributes", {}),
                                "price": sku_info.get("price", "0"),
                                "stock": sku_info.get("stock", 0),
                            })
                        if skus:
                            return skus
                except json.JSONDecodeError:
                    continue

        # Fallback: parse from HTML
        sku_attrs = selector.css("div.sku-attr-list, div.obj-attr-item")
        for idx, attr in enumerate(sku_attrs):
            name = attr.css("span.attr-name::text").get() or ""
            values = attr.css("span.attr-value::text").getall()
            if name and values:
                skus.append({
                    "sku_id": f"attr-{idx}",
                    "attributes": {name.strip(): [v.strip() for v in values]},
                    "price": "0",
                    "stock": 0,
                })

        return skus

    @staticmethod
    def _get_first_match(selector: parsel.Selector, css_selectors: list[str]) -> str:
        """Get first matching text from list of selectors."""
        for css in css_selectors:
            text = selector.css(f"{css}::text").get()
            if text:
                return text
            # Try deeper extraction
            text = selector.css(f"{css} *::text").get()
            if text:
                return text
        return ""

    @staticmethod
    def _get_first_match_attr(selector: parsel.Selector, css_selectors: list[str], attr: str) -> str:
        """Get first matching attribute from list of selectors."""
        for css in css_selectors:
            value = selector.css(f"{css}::attr({attr})").get()
            if value:
                return value
        return ""

    @staticmethod
    def _parse_price(price_text: str) -> tuple[str, Decimal, Decimal]:
        """Parse price text to standardized format.

        Examples:
            "￥12.00-25.00" -> ("12.00-25.00", 12.00, 25.00)
            "12.00" -> ("12.00-12.00", 12.00, 12.00)
            "¥128.00 起" -> ("128.00-128.00", 128.00, 128.00)
        """
        if not price_text:
            return "0-0", Decimal("0"), Decimal("0")

        # Clean price text
        price_text = re.sub(r"[￥¥]", "", price_text)
        price_text = re.sub(r"[起元]", "", price_text)
        price_text = price_text.strip()

        # Find all numbers
        numbers = re.findall(r"[\d,.]+", price_text)
        if not numbers:
            return "0-0", Decimal("0"), Decimal("0")

        # Parse min and max
        min_price = Decimal(numbers[0].replace(",", ""))
        max_price = min_price

        if len(numbers) >= 2:
            max_price = Decimal(numbers[-1].replace(",", ""))

        price_range = f"{min_price}-{max_price}"
        return price_range, min_price, max_price

    @staticmethod
    def _parse_sales(sales_text: str) -> int:
        """Parse sales count text.

        Examples:
            "1000+件成交" -> 1000
            "月销500" -> 500
            "1万+" -> 10000
        """
        if not sales_text:
            return 0

        sales_text = sales_text.strip()

        # Handle Chinese number units
        if "万" in sales_text:
            match = re.search(r"([\d.]+)万", sales_text)
            if match:
                return int(float(match.group(1)) * 10000)

        # Extract number
        match = re.search(r"(\d+)", sales_text.replace(",", ""))
        return int(match.group(1)) if match else 0

    @staticmethod
    def _extract_product_id(url: str) -> str:
        """Extract product ID from URL.

        Examples:
            "https://detail.1688.com/offer/1234567890.html" -> "1234567890"
            "//detail.1688.com/offer/1234567890.html" -> "1234567890"
        """
        match = re.search(r"offer/(\d+)", url)
        return match.group(1) if match else ""

    @staticmethod
    def _normalize_image_url(url: str) -> str:
        """Normalize image URL to full https format."""
        if not url:
            return ""
        if url.startswith("//"):
            return f"https:{url}"
        if not url.startswith("http"):
            return f"https://{url}" if url else ""
        return url
