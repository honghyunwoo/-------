import redis
import json
from loguru import logger

from app.config.config import config

_enable_redis = config.app.get("enable_redis", False)
_redis_host = config.app.get("redis_host", "localhost")
_redis_port = config.app.get("redis_port", 6379)
_redis_db = config.app.get("redis_db", 0)
_redis_password = config.app.get("redis_password", None)

redis_client = None
if _enable_redis:
    try:
        redis_client = redis.StrictRedis(
            host=_redis_host, port=_redis_port, db=_redis_db, password=_redis_password,
            decode_responses=True  # Automatically decode responses to strings
        )
        redis_client.ping()
        logger.info("Redis cache connected successfully.")
    except redis.exceptions.ConnectionError as e:
        logger.error(f"Could not connect to Redis: {e}")
        redis_client = None

def get_cache(key: str):
    if not redis_client:
        return None
    try:
        cached_value = redis_client.get(key)
        return json.loads(cached_value) if cached_value else None
    except (redis.exceptions.RedisError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to get cache for key '{key}': {e}")
        return None

def set_cache(key: str, value: any, ttl: int = 3600):
    if not redis_client:
        return
    try:
        redis_client.set(key, json.dumps(value), ex=ttl)
    except redis.exceptions.RedisError as e:
        logger.warning(f"Failed to set cache for key '{key}': {e}")