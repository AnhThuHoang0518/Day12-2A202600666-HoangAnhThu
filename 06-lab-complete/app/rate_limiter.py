"""Sliding-window rate limiting with Redis storage and local fallback."""
import time
from collections import defaultdict, deque

from fastapi import HTTPException

from app.config import settings

try:
    import redis
except ModuleNotFoundError:
    redis = None


_local_windows: dict[str, deque] = defaultdict(deque)
_redis_client = None
_redis_available: bool | None = None


def _get_redis():
    global _redis_client, _redis_available
    if not redis or not settings.redis_url:
        return None
    if _redis_available is False:
        return None
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    try:
        _redis_client.ping()
        _redis_available = True
        return _redis_client
    except redis.RedisError:
        _redis_available = False
        return None


def check_rate_limit(bucket: str) -> None:
    now = time.time()
    limit = settings.rate_limit_per_minute
    client = _get_redis()

    if client:
        key = f"rate:{bucket}"
        pipe = client.pipeline()
        pipe.zremrangebyscore(key, 0, now - 60)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, 60)
        _, current, _, _ = pipe.execute()
        if int(current) >= limit:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {limit} req/min",
                headers={"Retry-After": "60"},
            )
        return

    window = _local_windows[bucket]
    while window and window[0] < now - 60:
        window.popleft()
    if len(window) >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {limit} req/min",
            headers={"Retry-After": "60"},
        )
    window.append(now)
