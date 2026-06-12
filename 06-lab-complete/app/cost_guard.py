"""Monthly budget protection for LLM calls."""
import time
from collections import defaultdict

from fastapi import HTTPException

from app.config import settings

try:
    import redis
except ModuleNotFoundError:
    redis = None


_local_monthly_cost: dict[str, float] = defaultdict(float)
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


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    input_cost = (input_tokens / 1000) * 0.00015
    output_cost = (output_tokens / 1000) * 0.0006
    return input_cost + output_cost


def check_and_record_cost(bucket: str, input_tokens: int, output_tokens: int) -> float:
    cost = estimate_cost(input_tokens, output_tokens)
    month = time.strftime("%Y-%m")
    limit = settings.monthly_budget_usd
    client = _get_redis()

    if client:
        key = f"budget:{bucket}:{month}"
        current = float(client.get(key) or 0.0)
        if current + cost > limit:
            raise HTTPException(
                status_code=402,
                detail=f"Monthly budget exceeded. Current: ${current:.4f}",
            )
        total = client.incrbyfloat(key, cost)
        client.expire(key, 32 * 24 * 3600)
        return float(total)

    key = f"{bucket}:{month}"
    current = _local_monthly_cost[key]
    if current + cost > limit:
        raise HTTPException(
            status_code=402,
            detail=f"Monthly budget exceeded. Current: ${current:.4f}",
        )
    _local_monthly_cost[key] += cost
    return _local_monthly_cost[key]


def get_monthly_cost(bucket: str) -> float:
    month = time.strftime("%Y-%m")
    client = _get_redis()
    if client:
        return float(client.get(f"budget:{bucket}:{month}") or 0.0)
    return _local_monthly_cost[f"{bucket}:{month}"]
