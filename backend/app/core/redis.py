"""Redis connection management."""

import redis.asyncio as redis

from app.config import get_settings

settings = get_settings()

redis_client: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    """Get Redis client instance (singleton)."""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global redis_client
    if redis_client is not None:
        await redis_client.close()
        redis_client = None
