"""
AegisAI Core — Centralized Redis Client.

Provides a lazily-initialized, process-wide synchronous Redis client.
Falls back gracefully to None if Redis is unavailable, so callers can
degrade to in-memory behavior rather than crashing.

Usage (sync context):
    from app.core.cache.redis_client import get_redis

    r = get_redis()
    if r:
        r.set("key", "value", ex=300)
        val = r.get("key")
    else:
        # fall back to in-memory / skip caching

The client is configured with:
  - socket_connect_timeout = 2s   (fast-fail on unavailable Redis)
  - socket_timeout          = 2s  (fast-fail on slow responses)
  - decode_responses         = True (return str instead of bytes)
"""

import threading
from typing import Any

import structlog

logger = structlog.get_logger("aegis_ai.core.cache.redis")

_lock = threading.Lock()
_client: Any = None  # redis.Redis | None
_initialized: bool = False


def get_redis() -> Any:  # returns redis.Redis | None
    """
    Return a lazily-initialized, process-wide Redis client.

    Thread-safe initialization via a module-level lock.
    Returns None if the Redis package is not installed or the server
    is unreachable — callers must handle the None case.
    """
    global _client, _initialized

    if _initialized:
        return _client

    with _lock:
        if _initialized:
            return _client

        try:
            import redis  # noqa: PLC0415

            from app.core.config.settings import settings  # noqa: PLC0415

            client = redis.from_url(
                settings.REDIS_URL,
                socket_connect_timeout=2,
                socket_timeout=2,
                decode_responses=True,
            )
            # Validate connectivity eagerly — fail fast at startup
            client.ping()
            _client = client
            logger.info("redis_client_connected", url=settings.REDIS_URL.split("@")[-1])
        except ImportError:
            logger.warning("redis_package_not_installed_caching_degraded")
            _client = None
        except Exception as exc:
            logger.warning("redis_connection_failed_caching_degraded", error=str(exc))
            _client = None

        _initialized = True
        return _client


def reset_redis_client() -> None:
    """Force re-initialization on next get_redis() call. Used in tests."""
    global _client, _initialized
    with _lock:
        _client = None
        _initialized = False
