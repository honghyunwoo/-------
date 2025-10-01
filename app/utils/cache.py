
import redis
import json
from app.config import config

_enable_redis = config.app.get("enable_redis", False)
_redis_host = config.app.get("redis_host", "localhost")
_redis_port = config.app.get("redis_port", 6379)
_redis_db = config.app.get("redis_db", 0)
_redis_password = config.app.get("redis_password", None)

redis_client = None
if _enable_redis:
    try:
        redis_client = redis.Redis(
            host=_redis_host, 
            port=_redis_port, 
            db=_redis_db, 
            password=_redis_password,
            decode_responses=True # Decode responses to strings
        )
        redis_client.ping() # Check connection
        print("Successfully connected to Redis.")
    except redis.exceptions.ConnectionError as e:
        print(f"Could not connect to Redis: {e}")
        redis_client = None

def set_cache(key: str, value, ex: int = 3600): # default 1 hour expiration
    if redis_client:
        try:
            # Serialize complex data types to JSON string
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            redis_client.set(key, value, ex=ex)
        except Exception as e:
            print(f"Error setting cache for key {key}: {e}")

def get_cache(key: str):
    if redis_client:
        try:
            cached_value = redis_client.get(key)
            if cached_value:
                try:
                    # Try to deserialize if it's a JSON string
                    return json.loads(cached_value)
                except json.JSONDecodeError:
                    return cached_value # Return as plain string
        except Exception as e:
            print(f"Error getting cache for key {key}: {e}")
    return None

