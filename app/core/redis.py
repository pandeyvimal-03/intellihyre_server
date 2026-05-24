from redis.asyncio import Redis
from typing import Optional
from app.core.config import settings

class RedisClient:
    redis: Optional[Redis] = None

redis_client = RedisClient()

async def connect_to_redis():
    redis_client.redis = Redis.from_url(
        settings.REDIS_URL, encoding="utf-8", decode_responses=True
    )

async def close_redis_connection():
    if redis_client.redis:
        await redis_client.redis.aclose()

def get_redis():
    return redis_client.redis