from datetime import datetime
from fastapi import HTTPException
from app.core.redis import redis_client

# 🔥 limits
FREE_LIMIT = 25
PREMIUM_LIMIT = 500


def get_today_key(user_id: str):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    return f"quota:{user_id}:{today}"


async def check_and_increment_quota(user_id: str, plan: str):
    key = get_today_key(user_id)

    current = await redis_client.get(key)
    current = int(current) if current else 0

    # 🔥 choose limit
    limit = FREE_LIMIT if plan == "free" else PREMIUM_LIMIT

    if current >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Daily limit reached ({limit} requests)"
        )

    # increment
    await redis_client.incr(key)

    # set expiry (24h)
    await redis_client.expire(key, 86400)