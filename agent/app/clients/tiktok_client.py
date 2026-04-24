"""TikTok Shop API client - supports mock and real API modes."""

import hashlib
import hmac
import json
import logging
import time
from typing import Any, Optional

import httpx

from app.config import agent_settings

logger = logging.getLogger(__name__)


class TikTokShopClient:
    """Client for TikTok Shop Open Platform API.

    Supports:
    - Product management (create, update, get)
    - Order management (list, get, update)
    - Category management (list, match)
    - Mock mode for development
    """

    # API endpoints
    SANDBOX_BASE_URL = "https://open-api.tiktokglobal.com/sandbox"
    PRODUCTION_BASE_URL = "https://open-api.tiktokglobal.com"

    def __init__(
        self,
        app_key: str = "",
        app_secret: str = "",
        sandbox: bool = True,
        mock_mode: bool = True,
    ):
        self.app_key = app_key or agent_settings.tiktok_app_key if hasattr(agent_settings, 'tiktok_app_key') else ""
        self.app_secret = app_secret or agent_settings.tiktok_app_secret if hasattr(agent_settings, 'tiktok_app_secret') else ""
        self.sandbox = sandbox
        self.mock_mode = mock_mode or agent_settings.tiktok_shop_mock_mode

        self.base_url = self.SANDBOX_BASE_URL if sandbox else self.PRODUCTION_BASE_URL
        self.client = httpx.AsyncClient(timeout=30.0)

        if self.mock_mode:
            logger.info("TikTokShopClient running in MOCK mode")
        else:
            logger.info(f"TikTokShopClient initialized for {'sandbox' if sandbox else 'production'}")

    # ==================== Product APIs ====================

    async def create_product(self, product_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new product on TikTok Shop.

        Args:
            product_data: Product information including:
                - title: Product title
                - description: Product description
                - category_id: TikTok category ID
                - images: List of image URLs
                - skus: List of SKU info
                - price: Base price

        Returns:
            API response with product_id
        """
        if self.mock_mode:
            return self._mock_create_product(product_data)

        params = {
            "product": product_data,
        }
        return await self._call_api("product.create", params)

    async def update_product(
        self,
        product_id: str,
        update_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Update an existing product."""
        if self.mock_mode:
            return self._mock_update_product(product_id, update_data)

        params = {
            "product_id": product_id,
            "update": update_data,
        }
        return await self._call_api("product.update", params)

    async def get_product(self, product_id: str) -> dict[str, Any]:
        """Get product details."""
        if self.mock_mode:
            return self._mock_get_product(product_id)

        params = {"product_id": product_id}
        return await self._call_api("product.get", params)

    async def list_products(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> dict[str, Any]:
        """List products with pagination."""
        if self.mock_mode:
            return self._mock_list_products(page, page_size, status)

        params = {
            "page_number": page,
            "page_size": page_size,
        }
        if status:
            params["product_status"] = status
        return await self._call_api("product.list", params)

    # ==================== Category APIs ====================

    async def get_categories(
        self,
        parent_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Get product categories."""
        if self.mock_mode:
            return self._mock_get_categories(parent_id)

        params = {}
        if parent_id:
            params["parent_id"] = parent_id
        result = await self._call_api("category.list", params)
        return result.get("categories", [])

    async def match_category(
        self,
        product_name: str,
        description: str = "",
    ) -> list[dict[str, Any]]:
        """Match product to TikTok categories using AI/category rules.

        Args:
            product_name: Product name
            description: Product description

        Returns:
            List of matched categories with confidence scores
        """
        if self.mock_mode:
            return self._mock_match_category(product_name)

        params = {
            "product_name": product_name,
            "description": description,
        }
        result = await self._call_api("category.match", params)
        return result.get("matches", [])

    # ==================== Order APIs ====================

    async def get_orders(
        self,
        status: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """Get orders from TikTok Shop.

        Args:
            status: Order status filter
            start_time: Start time (ISO format)
            end_time: End time (ISO format)
            page: Page number
            page_size: Page size

        Returns:
            Orders list with pagination info
        """
        if self.mock_mode:
            return self._mock_get_orders(status, page, page_size)

        params = {
            "page_number": page,
            "page_size": page_size,
        }
        if status:
            params["order_status"] = status
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        return await self._call_api("order.list", params)

    async def get_order(self, order_id: str) -> dict[str, Any]:
        """Get order details."""
        if self.mock_mode:
            return self._mock_get_order(order_id)

        params = {"order_id": order_id}
        return await self._call_api("order.get", params)

    async def update_order_status(
        self,
        order_id: str,
        status: str,
        tracking_number: Optional[str] = None,
        carrier: Optional[str] = None,
    ) -> dict[str, Any]:
        """Update order status (e.g., mark as shipped)."""
        if self.mock_mode:
            return self._mock_update_order_status(order_id, status)

        params = {
            "order_id": order_id,
            "status": status,
        }
        if tracking_number:
            params["tracking_number"] = tracking_number
        if carrier:
            params["carrier"] = carrier

        return await self._call_api("order.update", params)

    # ==================== API Call Infrastructure ====================

    async def _call_api(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """Make authenticated API call to TikTok Shop.

        Args:
            method: API method name
            params: API parameters

        Returns:
            API response
        """
        timestamp = int(time.time())

        # Build request
        request_body = {
            "app_key": self.app_key,
            "method": method,
            "timestamp": timestamp,
            "version": "202309",
            **params,
        }

        # Generate signature
        sign = self._generate_signature(request_body)
        request_body["sign"] = sign

        try:
            response = await self.client.post(
                f"{self.base_url}/api",
                json=request_body,
            )
            response.raise_for_status()

            result = response.json()
            if result.get("code") != 0:
                raise TikTokAPIError(
                    code=result.get("code"),
                    message=result.get("message", "Unknown error"),
                )
            return result.get("data", {})

        except httpx.HTTPError as e:
            logger.error(f"TikTok API HTTP error: {e}")
            raise

    def _generate_signature(self, params: dict[str, Any]) -> str:
        """Generate API signature.

        TikTok Shop uses HMAC-SHA256 for signature.
        """
        # Sort params and concatenate
        sorted_params = sorted(params.items())
        sign_string = self.app_secret
        for key, value in sorted_params:
            if key != "sign":
                sign_string += f"{key}{value}"
        sign_string += self.app_secret

        # HMAC-SHA256
        signature = hmac.new(
            self.app_secret.encode(),
            sign_string.encode(),
            hashlib.sha256,
        ).hexdigest()

        return signature

    # ==================== Mock Implementations ====================

    def _mock_create_product(self, data: dict) -> dict:
        import random
        product_id = f"TK_PROD_{random.randint(100000000, 999999999)}"
        return {
            "product_id": product_id,
            "status": "pending_review",
            "message": "Product created successfully (mock)",
        }

    def _mock_update_product(self, product_id: str, data: dict) -> dict:
        return {
            "product_id": product_id,
            "status": "updated",
            "message": "Product updated (mock)",
        }

    def _mock_get_product(self, product_id: str) -> dict:
        return {
            "product_id": product_id,
            "title": f"Mock Product {product_id}",
            "status": "active",
            "price": "29.99",
        }

    def _mock_list_products(self, page: int, page_size: int, status: str | None) -> dict:
        import random
        return {
            "products": [
                {
                    "product_id": f"TK_PROD_{i}",
                    "title": f"Mock Product {i}",
                    "status": status or "active",
                    "price": f"{random.uniform(10, 100):.2f}",
                }
                for i in range((page - 1) * page_size, page * page_size)
            ],
            "total": 100,
            "page": page,
            "page_size": page_size,
        }

    def _mock_get_categories(self, parent_id: str | None) -> list:
        categories = [
            {"id": "cat_001", "name": "Electronics", "level": 1},
            {"id": "cat_002", "name": "Clothing", "level": 1},
            {"id": "cat_003", "name": "Home & Garden", "level": 1},
            {"id": "cat_004", "name": "Beauty", "level": 1},
            {"id": "cat_005", "name": "Sports", "level": 1},
        ]
        if parent_id:
            # Return subcategories
            return [
                {"id": f"{parent_id}_sub_{i}", "name": f"Subcategory {i}", "level": 2}
                for i in range(1, 6)
            ]
        return categories

    def _mock_match_category(self, product_name: str) -> list:
        import random
        # Simple keyword matching
        name_lower = product_name.lower()
        if any(kw in name_lower for kw in ["phone", "case", "charger", "电子"]):
            cat = {"id": "cat_001", "name": "Electronics", "confidence": 0.85}
        elif any(kw in name_lower for kw in ["dress", "shirt", "鞋", "服装"]):
            cat = {"id": "cat_002", "name": "Clothing", "confidence": 0.80}
        elif any(kw in name_lower for kw in ["home", "kitchen", "家居"]):
            cat = {"id": "cat_003", "name": "Home & Garden", "confidence": 0.75}
        else:
            cat = {"id": "cat_001", "name": "Electronics", "confidence": 0.50}

        return [
            cat,
            {"id": "cat_004", "name": "Beauty", "confidence": random.uniform(0.3, 0.5)},
            {"id": "cat_005", "name": "Sports", "confidence": random.uniform(0.2, 0.4)},
        ]

    def _mock_get_orders(self, status: str | None, page: int, page_size: int) -> dict:
        import random
        from datetime import datetime, timezone

        orders = []
        for i in range(page_size):
            orders.append({
                "order_id": f"TK_ORD_{random.randint(100000, 999999)}",
                "status": status or random.choice(["pending", "paid", "shipped", "delivered"]),
                "total_amount": f"{random.uniform(10, 200):.2f}",
                "currency": "USD",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "items": [
                    {
                        "product_id": f"TK_PROD_{random.randint(1, 100)}",
                        "quantity": random.randint(1, 3),
                        "price": f"{random.uniform(5, 50):.2f}",
                    }
                ],
            })
        return {
            "orders": orders,
            "total": 100,
            "page": page,
            "page_size": page_size,
        }

    def _mock_get_order(self, order_id: str) -> dict:
        import random
        from datetime import datetime, timezone

        return {
            "order_id": order_id,
            "status": random.choice(["pending", "paid", "shipped", "delivered"]),
            "total_amount": f"{random.uniform(10, 200):.2f}",
            "currency": "USD",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "shipping_address": {
                "name": "Mock Customer",
                "address": "123 Mock Street",
                "city": "Mock City",
                "country": "US",
            },
        }

    def _mock_update_order_status(self, order_id: str, status: str) -> dict:
        return {
            "order_id": order_id,
            "status": status,
            "message": f"Order status updated to {status} (mock)",
        }

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


class TikTokAPIError(Exception):
    """TikTok API error."""
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"TikTok API Error [{code}]: {message}")


# Singleton client
_tiktok_client = None


def get_tiktok_client() -> TikTokShopClient:
    """Get TikTok Shop client singleton."""
    global _tiktok_client
    if _tiktok_client is None:
        _tiktok_client = TikTokShopClient()
    return _tiktok_client
