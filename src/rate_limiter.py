import random
from time import time
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import ConnectionPool, Redis, RedisError

from src.conf import settings
from src.logging_conf import logger

_pool: ConnectionPool | None = None


class RedisManager:
    def __init__(self):
        self._pool: ConnectionPool | None = None

    async def initialize(self):
        if self._pool is None:
            self._pool = ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                max_connections=50,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30,
                decode_responses=True,
            )

    async def close(self):
        if self._pool:
            await self._pool.disconnect()
            self._pool = None

    def get_client(self) -> Redis:
        if not self._pool:
            raise RuntimeError("Redis pool not initialized")
        return Redis(connection_pool=self._pool)


redis_manager = RedisManager()


def get_redis() -> Redis:
    return redis_manager.get_client()


class RateLimiter:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def is_limited(
        self, ip_address: str, endpoint: str, max_requests: int, window_seconds
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
        ip_address = request.client.host
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
