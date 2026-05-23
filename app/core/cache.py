import json
import logging
from typing import Optional, Any
import redis.asyncio as aioredis
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class CacheService:
    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None

    def get_client(self) -> aioredis.Redis:
        """Lazy initialization of the asynchronous Redis client instance."""
        if self._redis is None:
            self._redis = aioredis.Redis.from_url(
                settings.redis_url, 
                decode_responses=True
            )
        return self._redis

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve and deserialize structured data from the Redis cache cluster."""
        try:
            client = self.get_client()
            data = await client.get(key)
            if data:
                logger.info(f"Cache HIT for key: {key}")
                return json.loads(data)
            logger.info(f"Cache MISS for key: {key}")
            return None
        except Exception as e:
            logger.error(f"Redis backend GET exception for key {key}: {str(e)}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Serialize and commit data to Redis with a strict Time-To-Live (TTL)."""
        try:
            client = self.get_client()
            serialized_value = json.dumps(value)
            await client.set(key, serialized_value, ex=ttl)
            logger.info(f"Cache SET successful for key: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Redis backend SET exception for key {key}: {str(e)}")
            return False

    async def invalidate(self, key: str) -> bool:
        """Evict a specific keyspace record to preserve cache coherency."""
        try:
            client = self.get_client()
            await client.delete(key)
            logger.info(f"Cache INVALIDATE successful for key: {key}")
            return True
        except Exception as e:
            logger.error(f"Redis backend DELETE exception for key {key}: {str(e)}")
            return False

# Export a unified singleton instance for application-wide reuse
cache_service = CacheService()