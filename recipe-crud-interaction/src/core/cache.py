import redis
import json
from typing import Any, Optional
from src.core.config import settings

class CacheClient:
    def __init__(self):
        self._redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2
        )
        self.DEFAULT_TTL = 3600

    def get(self, key: str) -> Optional[Any]:
        """Safely retrieves and deserializes a value from Redis."""
        try:
            data = self._redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            print(f"⚠️ Redis Get Error ({key}): {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = None):
        """Serializes and saves a value to Redis with TTL."""
        try:
            payload = json.dumps(value)
            self._redis.setex(key, ttl or self.DEFAULT_TTL, payload)
        except Exception as e:
            print(f"⚠️ Redis Set Error ({key}): {e}")

    def delete(self, *keys):
        """Deletes one or more keys."""
        try:
            if keys:
                self._redis.delete(*keys)
        except Exception as e:
            print(f"⚠️ Redis Delete Error: {e}")

# Singleton instance
cache_client = CacheClient()