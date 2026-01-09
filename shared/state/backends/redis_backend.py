"""
Redis State Backend for Linux/macOS

Redis-based implementation of StateBackend for Linux/macOS systems.
Faster than SQLite but requires Redis server installation.
"""
import redis
from typing import Dict, Optional
from .base import StateBackend


class RedisStateBackend(StateBackend):
    """
    Redis implementation of StateBackend.

    Wrapper around redis-py client that implements the StateBackend interface.
    """

    def __init__(self, url: str = 'redis://localhost:6378/0'):
        """
        Initialize Redis backend.

        Args:
            url: Redis connection URL
        """
        self.url = url
        try:
            self.client = redis.from_url(
                url,
                decode_responses=True,  # Auto-decode bytes to str
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.client.ping()
            print(f"[REDIS-BACKEND] ✅ Conectado a Redis: {url}")
        except redis.ConnectionError as e:
            print(f"[REDIS-BACKEND] ❌ Error conectando a Redis: {e}")
            raise ConnectionError(f"No se pudo conectar a Redis en {url}: {e}")

    def hset(self, key: str, mapping: dict) -> int:
        """Set multiple fields in a hash."""
        return self.client.hset(key, mapping=mapping)

    def hgetall(self, key: str) -> dict:
        """Get all fields and values from a hash."""
        return self.client.hgetall(key)

    def hget(self, key: str, field: str) -> Optional[str]:
        """Get a single field value from a hash."""
        return self.client.hget(key, field)

    def set(self, key: str, value: str) -> bool:
        """Set a key-value pair."""
        return self.client.set(key, value)

    def get(self, key: str) -> Optional[str]:
        """Get a value by key."""
        return self.client.get(key)

    def delete(self, key: str) -> int:
        """Delete a key and all its data."""
        return self.client.delete(key)

    def exists(self, key: str) -> bool:
        """Check if a key exists."""
        return self.client.exists(key) > 0

    def keys(self, pattern: str = '*') -> list:
        """Get all keys matching a pattern."""
        # Redis returns bytes, convert to strings
        return [k.decode('utf-8') if isinstance(k, bytes) else k
                for k in self.client.keys(pattern)]

    def ping(self) -> bool:
        """Test connectivity to the backend."""
        try:
            return self.client.ping()
        except Exception as e:
            print(f"[REDIS-BACKEND] ❌ Ping failed: {e}")
            return False

    def close(self):
        """Close connections and cleanup resources."""
        try:
            self.client.close()
            print(f"[REDIS-BACKEND] 🔌 Connection closed")
        except Exception as e:
            print(f"[REDIS-BACKEND] ⚠️  Error closing connection: {e}")

    def get_stats(self) -> dict:
        """Get statistics about Redis."""
        try:
            info = self.client.info()
            return {
                'keys': self.client.dbsize(),
                'used_memory_mb': info.get('used_memory', 0) / (1024 * 1024),
                'connected_clients': info.get('connected_clients', 0),
                'uptime_seconds': info.get('uptime_in_seconds', 0),
            }
        except Exception as e:
            print(f"[REDIS-BACKEND] ⚠️  Error getting stats: {e}")
            return {}
