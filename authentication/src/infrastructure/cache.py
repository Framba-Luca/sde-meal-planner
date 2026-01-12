import redis.asyncio as redis
from src.core.config import settings

class RedisClient:
    """
    Handles the Redis async communication. 
    Used for:
    1. Token Blacklist (Logout / Revoke)
    2. Sessions or rate limiting
    """
    def __init__(self):
        # Initialize the connection using the config.py settings
        # decode_responses=True ci returns string instead of bytes
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,  # Using DB 0 for authentication
            decode_responses=True
        )

    async def add_to_blacklist(self, token: str, expiration_seconds: int):
        """
        Adds into the blacklist a token with TTL (Time To Live).
        When thr TTL expires, Redis automatically removes the keys.
        """
        await self.redis.setex(
            name=f"blacklist:{token}",
            time=expiration_seconds,
            value="revoked"
        )
        
    async def is_token_revoked(self, token: str) -> bool:
        """
        Checks if the token is present in the blacklist.
        Returns True if the token is revocated (therefore not valid).
        """
        val = await self.redis.get(f"blacklist:{token}")
        return val is not None

    async def close(self):
        """
        Closes the Redis connection pool."""
        await self.redis.close()

# Signleton instance of RedisClient
redis_client = RedisClient()