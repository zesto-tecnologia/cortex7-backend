"""Redis cache client for token operations and caching.

This module provides async Redis operations for:
- Token deny-list (revocation)
- Token family tracking
- Token metadata caching
- General application caching
"""

from __future__ import annotations

from typing import Any, Optional
import json
from redis.asyncio import Redis, ConnectionPool
import structlog

from services.auth.config import settings

logger = structlog.get_logger(__name__)


class RedisClient:
    """Async Redis client wrapper for token operations."""

    def __init__(self):
        """Initialize Redis connection pool."""
        self.pool: Optional[ConnectionPool] = None
        self.redis: Optional[Redis] = None

    async def connect(self) -> None:
        """Connect to Redis with connection pooling."""
        try:
            self.pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=settings.REDIS_POOL_SIZE,
                decode_responses=settings.REDIS_DECODE_RESPONSES,
            )
            self.redis = Redis(connection_pool=self.pool)
            # Test connection
            await self.redis.ping()
        except Exception as e:
            logger.error(f"redis_connect_failed - {str(e)}")
            raise

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.aclose()

    async def ping(self) -> bool:
        """Ping Redis to check connection health."""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        return await self.redis.ping()

    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        return await self.redis.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> None:
        """Set key-value pair with optional expiration."""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        await self.redis.set(key, value, ex=ex)

    async def setex(self, key: str, seconds: int, value: str) -> None:
        """Set key-value with expiration in seconds."""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        await self.redis.setex(key, seconds, value)

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys."""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        return await self.redis.delete(*keys)

    async def exists(self, *keys: str) -> int:
        """Check if keys exist."""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        return await self.redis.exists(*keys)

    async def ttl(self, key: str) -> int:
        """Get TTL for key."""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        return await self.redis.ttl(key)

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key."""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        return await self.redis.expire(key, seconds)

    # Set operations for token families
    async def sadd(self, key: str, *values: str) -> int:
        """Add members to a set."""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        return await self.redis.sadd(key, *values)

    async def smembers(self, key: str) -> set[str]:
        """Get all members of a set."""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        return await self.redis.smembers(key)

    async def srem(self, key: str, *values: str) -> int:
        """Remove members from a set."""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        return await self.redis.srem(key, *values)

    # JSON helpers
    async def get_json(self, key: str) -> Optional[dict[str, Any]]:
        """Get JSON value by key."""
        value = await self.get(key)
        if value:
            return json.loads(value)
        return None

    async def set_json(self, key: str, value: dict[str, Any], ex: Optional[int] = None) -> None:
        """Set JSON value with optional expiration."""
        await self.set(key, json.dumps(value), ex=ex)


# Global Redis client instance
redis_client = RedisClient()
