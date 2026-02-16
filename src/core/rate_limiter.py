import random
from time import time
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis, RedisError

from src.core.cache import get_redis
from src.core.logging_conf import logger


class RateLimiter:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def is_limited(
        self, ip_address: str, endpoint: str, max_requests: int, window_seconds: int
    ) -> bool:
        try:
            key = f"rate_limiter:{endpoint}:{ip_address}"

            current_ms = time() * 1000
            window_start_ms = current_ms - window_seconds * 1000

            current_request = f"{current_ms}-{random.randint(0, 100_000)}"

            async with self._redis.pipeline() as pipe:
                await pipe.zremrangebyscore(key, 0, window_start_ms)
                await pipe.zadd(key, {current_request: current_ms})
                await pipe.zcard(key)
                await pipe.expire(key, window_seconds)
                res = await pipe.execute()
            _, _, current_count, _ = res

            if current_count > max_requests:
                await self._redis.zrem(key, current_request)
                return True
            return False
        except RedisError as e:
            logger.error(f"Rate limiter Redis error: {e}")
            return False


def get_rate_limiter() -> RateLimiter:
    return RateLimiter(get_redis())


def rate_limiter_factory(
    max_requests: int,
    window_seconds: int,
):
    async def dependency(
        request: Request,
        rate_limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
    ):
        ip_address = request.client.host if request.client else "unknown"
        endpoint = request.url.path
        limited = await rate_limiter.is_limited(
            ip_address, endpoint, max_requests, window_seconds
        )
        if limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="You exceed max requests, try later again",
            )

    return dependency


rate_limiter_auth = rate_limiter_factory(3, 10)
rate_limiter_posts = rate_limiter_factory(5, 5)
rate_limiter_comments = rate_limiter_factory(10, 5)
