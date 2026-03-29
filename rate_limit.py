import time
import redis
from fastapi import HTTPException
from app import config

# Create a Redis client with short timeouts so requests don't hang forever.
# NOTE: We intentionally "fail open" in dev if Redis is unavailable to avoid 500s.
_redis = redis.Redis.from_url(
    config.REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=1,
    socket_timeout=1,
)

def enforce_rate_limit(api_key: str, requests_per_minute: int = None) -> None:
    """
    Enforce a simple per-minute request limit using Redis INCR.

    Behavior:
      - If Redis is available: enforce limit (429 if exceeded).
      - If Redis is down/unreachable: fail-open (do NOT block requests).
        This prevents the API from 500'ing in local dev.
    """
    limit = int(requests_per_minute or config.RL_REQUESTS_PER_MINUTE)
    now = int(time.time())
    bucket = now // 60
    key = f"rl:req:{api_key}:{bucket}"

    try:
        n = _redis.incr(key)
        if n == 1:
            # Keep key alive for 2 minutes to handle clock drift and late requests.
            _redis.expire(key, 120)

        if n > limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
        # Fail-open: don't take the whole API down if Redis isn't reachable.
        return
    except redis.exceptions.RedisError:
        # Any other Redis-layer error: also fail-open for safety.
        return
