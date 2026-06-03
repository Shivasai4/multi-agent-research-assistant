import redis
import json
from src.config import settings
from loguru import logger

redis_client = None

def init_redis():
    global redis_client
    try:
        redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        redis_client.ping()
        logger.info(f"Redis connected to {settings.redis_url}")
    except Exception as e:
        logger.warning(f"Redis not available: {e}. Caching disabled.")
        redis_client = None

def get_cache_key(query: str, max_revisions: int) -> str:
    """Generate unique cache key for query + revision setting."""
    return f"research:{max_revisions}:{query.lower().strip()}"

def get_cached_result(query: str, max_revisions: int):
    """Retrieve cached result if exists."""
    if not redis_client:
        return None
    key = get_cache_key(query, max_revisions)
    cached = redis_client.get(key)
    if cached:
        logger.info(f"Cache hit for: {query[:50]}...")
        return json.loads(cached)
    return None

def set_cached_result(query: str, max_revisions: int, result_data: dict):
    """Store result in cache with TTL."""
    if not redis_client:
        return
    key = get_cache_key(query, max_revisions)
    redis_client.setex(key, settings.cache_ttl, json.dumps(result_data))
    logger.info(f"Cached result for: {query[:50]}...")