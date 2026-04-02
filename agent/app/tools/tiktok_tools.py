"""TikTok Shop API tools (Mock mode)."""

import random
from datetime import datetime, timezone
from typing import Any

from app.config import agent_settings


async def search_tiktok_products(keyword: str, page: int = 1) -> dict[str, Any]:
    """Search TikTok Shop for similar products (mock)."""
    if agent_settings.tiktok_shop_mock_mode:
        return _mock_search(keyword, page)

    # TODO: Implement actual TikTok Shop API call
    raise NotImplementedError("TikTok Shop API not yet implemented")


async def get_tiktok_product(product_id: str) -> dict[str, Any]:
    """Get TikTok product details (mock)."""
    if agent_settings.tiktok_shop_mock_mode:
        return {
            "product_id": product_id,
            "title": f"Mock TikTok Product {product_id}",
            "price": round(random.uniform(9.99, 99.99), 2),
            "currency": "USD",
            "sales": random.randint(100, 10000),
        }
    raise NotImplementedError("TikTok Shop API not yet implemented")


async def list_product_on_tiktok(product_data: dict) -> dict[str, Any]:
    """List product on TikTok Shop (mock)."""
    if agent_settings.tiktok_shop_mock_mode:
        mock_id = f"TK{random.randint(1000000000, 9999999999)}"
        return {
            "tiktok_product_id": mock_id,
            "status": "active",
            "message": "Product listed successfully (mock)",
        }
    raise NotImplementedError("TikTok Shop API not yet implemented")


async def get_tiktok_orders(status: str | None = None) -> dict[str, Any]:
    """Get TikTok Shop orders (mock)."""
    if agent_settings.tiktok_shop_mock_mode:
        return {
            "orders": [
                {
                    "tiktok_order_id": f"ORD{random.randint(100000, 999999)}",
                    "status": status or "pending",
                    "total_amount": round(random.uniform(10, 200), 2),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                for _ in range(5)
            ]
        }
    raise NotImplementedError("TikTok Shop API not yet implemented")


def _mock_search(keyword: str, page: int) -> dict[str, Any]:
    """Generate mock search results."""
    return {
        "keyword": keyword,
        "page": page,
        "total": 100,
        "items": [
            {
                "product_id": f"TK_PROD_{i + (page - 1) * 20}",
                "title": f"{keyword} related product {i}",
                "price": round(random.uniform(5, 50), 2),
                "sales": random.randint(50, 5000),
                "rating": round(random.uniform(3.5, 5.0), 1),
            }
            for i in range(20)
        ],
    }
