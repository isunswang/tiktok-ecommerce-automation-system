"""Tool wrappers for calling backend API from agents."""

import httpx

from app.config import agent_settings


class BackendClient:
    """HTTP client for calling the backend API."""

    def __init__(self):
        self.base_url = agent_settings.backend_api_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get(self, path: str, params: dict | None = None) -> dict:
        """Send GET request to backend."""
        resp = await self.client.get(f"{self.base_url}{path}", params=params)
        resp.raise_for_status()
        return resp.json()

    async def post(self, path: str, json: dict | None = None) -> dict:
        """Send POST request to backend."""
        resp = await self.client.post(f"{self.base_url}{path}", json=json)
        resp.raise_for_status()
        return resp.json()

    async def put(self, path: str, json: dict | None = None) -> dict:
        """Send PUT request to backend."""
        resp = await self.client.put(f"{self.base_url}{path}", json=json)
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self.client.aclose()


# Singleton client instance
backend_client = BackendClient()


async def get_products(keyword: str = "", page: int = 1, page_size: int = 20) -> dict:
    """Fetch products from backend."""
    return await backend_client.get("/v1/products", params={
        "keyword": keyword, "page": page, "page_size": page_size,
    })


async def get_orders(status: str | None = None, page: int = 1) -> dict:
    """Fetch orders from backend."""
    params = {"page": page}
    if status:
        params["status"] = status
    return await backend_client.get("/v1/orders", params=params)


async def calculate_pricing(cost_price_cny: float, target_market: str, **kwargs) -> dict:
    """Calculate pricing through backend."""
    payload = {"cost_price_cny": cost_price_cny, "target_market": target_market}
    payload.update(kwargs)
    return await backend_client.post("/v1/pricing/calculate", json=payload)


async def get_finance_summary(period: str = "month") -> dict:
    """Get financial summary."""
    return await backend_client.get("/v1/finance/summary", params={"period": period})
