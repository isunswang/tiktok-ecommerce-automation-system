"""Authentication flow unit tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """Test successful user registration."""
    response = await client.post("/api/v1/auth/register", json={
        "username": "testuser@example.com",
        "password": "securepass123",
        "nickname": "Test User",
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    """Test duplicate registration."""
    payload = {"username": "dup@example.com", "password": "securepass123", "nickname": "Dup"}
    await client.post("/api/v1/auth/register", json=payload)

    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test successful login."""
    # Register first
    await client.post("/api/v1/auth/register", json={
        "username": "login@example.com",
        "password": "securepass123",
        "nickname": "Login User",
    })

    # Login
    response = await client.post("/api/v1/auth/login", json={
        "username": "login@example.com",
        "password": "securepass123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    """Test login with wrong password."""
    await client.post("/api/v1/auth/register", json={
        "username": "wrong@example.com",
        "password": "securepass123",
        "nickname": "Wrong Pass",
    })

    response = await client.post("/api/v1/auth/login", json={
        "username": "wrong@example.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient):
    """Test getting current user info with valid token."""
    # Register
    reg = await client.post("/api/v1/auth/register", json={
        "username": "me@example.com",
        "password": "securepass123",
        "nickname": "Me User",
    })
    token = reg.json()["access_token"]

    # Get me
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "me@example.com"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    """Test getting current user without token returns 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token(client: AsyncClient):
    """Test getting current user with invalid token returns 401."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401
