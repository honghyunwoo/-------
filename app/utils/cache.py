"""Redis 캐싱 시스템

성능 최적화를 위한 Redis 기반 캐싱 유틸리티
"""

import json
from functools import wraps
from typing import Any, Callable, Optional

import redis
from loguru import logger

from app.config.config import config

_enable_redis = config.app.get("enable_redis", False)
_redis_host = config.app.get("redis_host", "localhost")
_redis_port = config.app.get("redis_port", 6379)
_redis_db = config.app.get("redis_db", 0)
_redis_password = config.app.get("redis_password", None)

redis_client = None
REDIS_AVAILABLE = False

if _enable_redis:
    try:
        redis_client = redis.StrictRedis(
            host=_redis_host,
            port=_redis_port,
            db=_redis_db,
            password=_redis_password,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
        )
        redis_client.ping()
        logger.info(
            f"Redis cache connected: {_redis_host}:{_redis_port}"
        )
        REDIS_AVAILABLE = True
    except redis.exceptions.ConnectionError as e:
        logger.warning(f"Redis not available: {e}. Caching disabled.")
        redis_client = None
        REDIS_AVAILABLE = False


def get_cache(key: str) -> Optional[Any]:
    """캐시에서 데이터 조회

    Args:
        key: 캐시 키

    Returns:
        캐시된 데이터 (없으면 None)
    """
    if not redis_client:
        return None
    try:
        cached_value = redis_client.get(key)
        if cached_value:
            logger.debug(f"Cache HIT: {key}")
            return json.loads(cached_value)
        logger.debug(f"Cache MISS: {key}")
        return None
    except (redis.exceptions.RedisError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to get cache for key '{key}': {e}")
        return None


def set_cache(key: str, value: Any, ttl: int = 3600) -> bool:
    """캐시에 데이터 저장

    Args:
        key: 캐시 키
        value: 저장할 데이터
        ttl: 만료 시간 (초, 기본 1시간)

    Returns:
        성공 여부
    """
    if not redis_client:
        return False
    try:
        redis_client.set(key, json.dumps(value, default=str), ex=ttl)
        logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
        return True
    except redis.exceptions.RedisError as e:
        logger.warning(f"Failed to set cache for key '{key}': {e}")
        return False


def delete_cache(key: str) -> bool:
    """캐시에서 데이터 삭제

    Args:
        key: 캐시 키

    Returns:
        성공 여부
    """
    if not redis_client:
        return False
    try:
        redis_client.delete(key)
        logger.debug(f"Cache DELETE: {key}")
        return True
    except redis.exceptions.RedisError as e:
        logger.warning(f"Failed to delete cache for key '{key}': {e}")
        return False


def delete_pattern(pattern: str) -> int:
    """패턴과 일치하는 모든 캐시 삭제

    Args:
        pattern: 키 패턴 (예: "user:*")

    Returns:
        삭제된 키 개수
    """
    if not redis_client:
        return 0
    try:
        keys = redis_client.keys(pattern)
        if keys:
            count = redis_client.delete(*keys)
            logger.debug(f"Cache DELETE pattern '{pattern}': {count} keys")
            return count
        return 0
    except redis.exceptions.RedisError as e:
        logger.warning(f"Failed to delete pattern '{pattern}': {e}")
        return 0


def invalidate_user_cache(user_id: int):
    """특정 사용자의 모든 캐시 무효화

    Args:
        user_id: 사용자 ID
    """
    patterns = [
        f"api:*:*user_id*:{user_id}*",
        f"videos:*:*{user_id}*",
        f"credits:*:*{user_id}*",
        f"user:{user_id}:*",
    ]

    total_deleted = 0
    for pattern in patterns:
        total_deleted += delete_pattern(pattern)

    if total_deleted > 0:
        logger.info(
            f"Invalidated {total_deleted} cache entries for user {user_id}"
        )


def get_cache_stats() -> dict:
    """Redis 캐시 통계 조회

    Returns:
        캐시 통계 딕셔너리
    """
    if not REDIS_AVAILABLE:
        return {"available": False}

    try:
        info = redis_client.info("stats")
        keyspace = redis_client.info("keyspace")

        # db0 키 개수 추출
        db0_keys = 0
        if "db0" in keyspace:
            db0_info = keyspace["db0"]
            db0_keys = db0_info.get("keys", 0)

        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses

        return {
            "available": True,
            "total_keys": db0_keys,
            "hits": hits,
            "misses": misses,
            "hit_rate": round(hits / total * 100, 2) if total > 0 else 0,
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {"available": False, "error": str(e)}