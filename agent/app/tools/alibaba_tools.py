"""1688 API tools (Mock mode)."""

import random
from typing import Any

from app.config import agent_settings


async def search_1688_products(keyword: str, page: int = 1, page_size: int = 20) -> dict[str, Any]:
    """Search 1688 for products (mock)."""
    if agent_settings.alibaba_1688_mock_mode:
        return _mock_search(keyword, page, page_size)

    # TODO: Implement actual 1688 API call
    raise NotImplementedError("1688 API not yet implemented")


async def get_1688_product_detail(product_id: str) -> dict[str, Any]:
    """Get 1688 product detail (mock)."""
    if agent_settings.alibaba_1688_mock_mode:
        return {
            "product_id": product_id,
            "title": f"Mock 1688 Product {product_id}",
            "price_range": f"{random.uniform(5, 15):.2f}-{random.uniform(15, 50):.2f}",
            "min_order_qty": random.choice([1, 2, 5, 10]),
            "supplier": {
                "name": f"Mock Supplier {random.randint(1000, 9999)}",
                "location": random.choice(["广州", "深圳", "义乌", "杭州"]),
                "rating": round(random.uniform(4.0, 5.0), 1),
            },
            "skus": [
                {"specs": f"Color:{c}, Size:{s}", "price": round(random.uniform(5, 30), 2)}
                for c in ["Black", "White", "Red"]
                for s in ["S", "M", "L"]
            ],
        }
    raise NotImplementedError("1688 API not yet implemented")


async def create_1688_purchase_order(items: list[dict]) -> dict[str, Any]:
    """Create purchase order on 1688 (mock)."""
    if agent_settings.alibaba_1688_mock_mode:
        order_id = f"1688_ORD_{random.randint(100000000, 999999999)}"
        return {
            "alibaba_order_id": order_id,
            "status": "ordered",
            "total_amount": round(sum(i.get("price", 0) * i.get("quantity", 1) for i in items), 2),
            "message": "Purchase order created (mock)",
        }
    raise NotImplementedError("1688 API not yet implemented")


def _mock_search(keyword: str, page: int, page_size: int) -> dict[str, Any]:
    """Generate mock 1688 search results."""
    return {
        "keyword": keyword,
        "page": page,
        "page_size": page_size,
        "total": 500,
        "items": [
            {
                "product_id": f"1688_{i + (page - 1) * page_size}",
                "title": f"{keyword} 批发 供货 厂家直销 商品{i}",
                "price_range": f"{random.uniform(3, 15):.2f}-{random.uniform(15, 60):.2f}",
                "sales": random.randint(100, 100000),
                "supplier": f"Supplier_{random.randint(1000, 9999)}",
                "location": random.choice(["广州", "深圳", "义乌", "杭州", "温州"]),
                "min_order_qty": random.choice([1, 2, 5, 10, 50]),
            }
            for i in range(page_size)
        ],
    }
