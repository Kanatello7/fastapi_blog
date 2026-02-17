import hashlib
import json
import random
import zlib
from functools import wraps
from typing import Any, Callable

from fastapi.encoders import jsonable_encoder
from redis.asyncio import ConnectionPool, Redis, RedisError

from src.conf import settings
from src.core.logging_conf import logger


class RedisManager:
    def __init__(self):
        self._pool: ConnectionPool | None = None
        self._client: Redis | None = None

    async def initialize(self):
        if self._pool is None:
            self._pool = ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                max_connections=50,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30,
                decode_responses=False,
            )
            self._client = Redis(connection_pool=self._pool)

    async def close(self):
        if self._pool:
            await self._pool.disconnect()
            self._pool = None
            self._client = None

    def get_client(self) -> Redis:
        if not self._client:
            raise RuntimeError("Redis  not initialized")
        return self._client


redis_manager = RedisManager()


def get_redis() -> Redis:
    return redis_manager.get_client()


PREFIX = "cache"


def _build_stable_key(
    func: Callable,
    kwargs: dict,
    key_params: list[str] | None,
    namespace: str,
) -> str:
    if key_params is not None:
        parts = {}
        for k in key_params:
            if k in kwargs:
                v = kwargs[k]
                parts[k] = str(v.id) if hasattr(v, "id") else v
    else:
        parts = {}
        for k, v in kwargs.items():
            if hasattr(v, "id"):
                parts[k] = str(v.id)
            elif isinstance(v, (str, int, float, bool, type(None))):
                parts[k] = v

    raw = json.dumps(parts, default=str, sort_keys=True)
    key_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]

    return f"{PREFIX}:{namespace}:{func.__module__}.{func.__name__}:{key_hash}"


def cache(
    exp=60,
    namespace: str = "default",
    key_params: list[str] | None = None,
    response_model=None,
):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            redis: Redis = get_redis()
            key = _build_stable_key(func, kwargs, key_params, namespace)

            try:
                cached = await redis.get(key)
                if cached is not None:
                    logger.debug("Cache HIT: %s", key)
                    await redis.incr(f"metrics:cache:hit:{namespace}")
                    decompressed = zlib.decompress(cached).decode()
                    return json.loads(decompressed)
            except RedisError:
                logger.warning("Redis read error for key %s, falling throgh", key)

            # Only one request computes; others wait
            lock_key = f"lock:{key}"
            lock = redis.lock(lock_key, timeout=10, blocking_timeout=5)

            if await lock.acquire(blocking=True):
                try:
                    # Double check
                    cached = await redis.get(key)
                    if cached is not None:
                        logger.debug("Cache HIT: %s", key)
                        await redis.incr(f"metrics:cache:hit:{namespace}")
                        decompressed = zlib.decompress(cached).decode()
                        return json.loads(decompressed)

                    logger.debug("Cache MISS: %s", key)
                    await redis.incr(f"metrics:cache:miss:{namespace}")
                    response = await func(*args, **kwargs)

                    serializable = _serialize(response, response_model)
                    encoded = json.dumps(serializable)
                    compressed = zlib.compress(encoded.encode())
                    jittered_exp = exp + random.randint(0, exp // 10)
                    await redis.set(key, compressed, ex=jittered_exp)

                    return response
                except Exception:
                    logger.warning("Cache write failed for key %s", key, exc_info=True)
                    return await func(*args, **kwargs)
                finally:
                    await lock.release()
            else:
                cached = await redis.get(key)
                if cached is not None:
                    logger.debug("Cache HIT: %s", key)
                    await redis.incr(f"metrics:cache:hit:{namespace}")
                    decompressed = zlib.decompress(cached).decode()
                    return json.loads(decompressed)
                await redis.incr(f"metrics:cache:miss:{namespace}")
                return await func(*args, **kwargs)

        wrapper._cache_namespace = namespace
        wrapper._cache_key_params = key_params
        wrapper._cache_func = func
        return wrapper

    return decorator


def _serialize(obj: Any, response_model=None) -> Any:
    from pydantic import BaseModel

    if isinstance(obj, list):
        return [_serialize(item, response_model) for item in obj]
    if response_model:
        return response_model.model_validate(obj).model_dump(mode="json")
    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    return jsonable_encoder(obj)


async def invalidate_namespace(namespace: str, cache=True) -> int:
    redis: Redis = get_redis()
    pattern = f"{PREFIX}:{namespace}:*" if cache else f"{namespace}:*"
    deleted = 0

    try:
        async for key in redis.scan_iter(pattern):
            await redis.delete(key)
            deleted += 1
        logger.info("Invalidated %d keys in namespace '%s'", deleted, namespace)
    except RedisError:
        logger.warning("Failed to invalidate namespace '%s'", namespace)

    return deleted


async def invalidate_for(*cached_funcs, **kwargs) -> int:
    redis = get_redis()
    deleted = 0

    for fn in cached_funcs:
        namespace = getattr(fn, "_cache_namespace", "default")
        key_params = getattr(fn, "_cache_key_params", None)
        original_func = getattr(fn, "_cache_func", fn)

        key = _build_stable_key(original_func, kwargs, key_params, namespace)
        try:
            result = await redis.delete(key)
            if result:
                deleted += result
                logger.info("Invalidated key: %s", key)
        except RedisError:
            logger.warning("Failed to invalidate key %s", key)
    return deleted
