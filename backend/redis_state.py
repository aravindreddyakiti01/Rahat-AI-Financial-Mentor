import os
import json
import logging
from typing import Any, Optional

logger = logging.getLogger("rahat.redis")

class RedisStateManager:
    """
    Redis Temporary / Fast Working State Manager.
    Supports real Redis when REDIS_URL is configured, with automatic
    fakeredis / in-memory fallback for zero-downtime resilience.
    """
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.client = None
        self._memory_fallback = {}
        self._init_connection()

    def _init_connection(self):
        try:
            import redis
            client = redis.from_url(self.redis_url, decode_responses=True, socket_connect_timeout=1)
            client.ping()
            self.client = client
            logger.info("Connected to Redis server.")
        except Exception as e:
            logger.warning(f"Could not connect to Redis server ({e}). Falling back to fakeredis/in-memory cache.")
            try:
                import fakeredis
                self.client = fakeredis.FakeStrictRedis(decode_responses=True)
            except Exception:
                self.client = None

    def get(self, key: str) -> Optional[str]:
        try:
            if self.client:
                return self.client.get(key)
            return self._memory_fallback.get(key)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return self._memory_fallback.get(key)

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        try:
            if self.client:
                if ex:
                    self.client.setex(key, ex, value)
                else:
                    self.client.set(key, value)
                return True
            self._memory_fallback[key] = value
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            self._memory_fallback[key] = value
            return True

    def delete(self, key: str) -> bool:
        try:
            if self.client:
                self.client.delete(key)
            self._memory_fallback.pop(key, None)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            self._memory_fallback.pop(key, None)
            return True

    def set_json(self, key: str, data: Any, ex: Optional[int] = None) -> bool:
        return self.set(key, json.dumps(data), ex=ex)

    def get_json(self, key: str) -> Optional[Any]:
        val = self.get(key)
        if val:
            try:
                return json.loads(val)
            except Exception:
                return None
        return None

# Singleton instance
redis_state = RedisStateManager()
