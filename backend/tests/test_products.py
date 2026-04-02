"""Product CRUD unit tests."""

import pytest
from httpx import AsyncClient


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict:
    """Get auth headers for authenticated requests."""
    reg = await client.post("/api/v1/auth/register", json={
        "username": "product@example.com",
        "password": "securepass123",
        "nickname": "Product User",
    })
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_product(client: AsyncClient, auth_headers: dict):
    """Test creating a product."""
    response = await client.post(
        "/api/v1/products",
        json={
            "name": "Test Product",
            "cost_price": "25.50",
            "description": "A test product",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Product"
    assert data["status"] == "draft"
    assert data["cost_price"] == "25.50"


@pytest.mark.asyncio
async def test_list_products(client: AsyncClient, auth_headers: dict):
    """Test listing products."""
    # Create a product first
    await client.post("/api/v1/products", json={
        "name": "List Test Product",
        "cost_price": "10.00",
    }, headers=auth_headers)

    response = await client.get("/api/v1/products", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_product(client: AsyncClient, auth_headers: dict):
    """Test getting a single product."""
    # Create
    create_resp = await client.post("/api/v1/products", json={
        "name": "Get Test Product",
        "cost_price": "15.00",
    }, headers=auth_headers)
    product_id = create_resp.json()["id"]

    # Get
    response = await client.get(
        f"/api/v1/products/{product_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Get Test Product"


@pytest.mark.asyncio
async def test_get_product_not_found(client: AsyncClient, auth_headers: dict):
    """Test getting a non-existent product."""
    response = await client.get(
        "/api/v1/products/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_product(client: AsyncClient, auth_headers: dict):
    """Test updating a product."""
    # Create
    create_resp = await client.post("/api/v1/products", json={
        "name": "Update Test Product",
        "cost_price": "20.00",
    }, headers=auth_headers)
    product_id = create_resp.json()["id"]

    # Update
    response = await client.put(
        f"/api/v1/products/{product_id}",
        json={"name": "Updated Name", "sale_price": "39.99"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_search_products(client: AsyncClient, auth_headers: dict):
    """Test searching products by keyword."""
    await client.post("/api/v1/products", json={
        "name": "Wireless Bluetooth Headphones",
        "cost_price": "50.00",
    }, headers=auth_headers)

    response = await client.get(
        "/api/v1/products?keyword=Bluetooth",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
