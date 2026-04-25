import redis.asyncio as redis
from arq import create_pool
from arq.connections import RedisSettings

from app.core.config import settings

redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True
)

arq_redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)

class ArqManager:
    pool = None

async def init_arq():
    ArqManager.pool = await create_pool(arq_redis_settings)