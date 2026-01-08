"""
Singleton Redis Client for Robot Runner

Este módulo proporciona un cliente Redis singleton para ser usado
por toda la aplicación. Facilita lazy loading y configuración centralizada.
"""
import redis
from typing import Optional


class RedisClient:
    """Cliente Redis singleton con lazy initialization."""

    _instance: Optional['RedisClient'] = None
    _client: Optional[redis.Redis] = None
    _redis_url: str = 'redis://localhost:6378/0'

    def __new__(cls):
        """Implementa patrón Singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def configure(cls, redis_url: str = 'redis://localhost:6378/0'):
        """
        Configura la URL de conexión a Redis.

        Args:
            redis_url: URL de conexión (ej: redis://localhost:6378/0)
        """
        cls._redis_url = redis_url
        # Reiniciar cliente si ya existía
        if cls._client is not None:
            try:
                cls._client.close()
            except:
                pass
            cls._client = None

    @classmethod
    def get_client(cls, decode_responses: bool = False) -> redis.Redis:
        """
        Obtiene el cliente Redis (lazy initialization).

        Args:
            decode_responses: Si True, decodifica automáticamente bytes a str

        Returns:
            redis.Redis: Cliente de Redis conectado

        Raises:
            ConnectionError: Si no se puede conectar a Redis
        """
        if cls._client is None:
            try:
                cls._client = redis.from_url(
                    cls._redis_url,
                    decode_responses=decode_responses,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Verificar conexión
                cls._client.ping()
                print(f"[REDIS-CLIENT] ✅ Conectado a Redis: {cls._redis_url}")
            except redis.ConnectionError as e:
                print(f"[REDIS-CLIENT] ❌ Error al conectar a Redis: {e}")
                raise ConnectionError(f"No se pudo conectar a Redis en {cls._redis_url}: {e}")

        return cls._client

    @classmethod
    def is_connected(cls) -> bool:
        """
        Verifica si hay una conexión activa a Redis.

        Returns:
            bool: True si está conectado y responde a ping
        """
        if cls._client is None:
            return False

        try:
            cls._client.ping()
            return True
        except:
            return False

    @classmethod
    def close(cls):
        """Cierra la conexión a Redis."""
        if cls._client is not None:
            try:
                cls._client.close()
                print(f"[REDIS-CLIENT] 🔌 Conexión a Redis cerrada")
            except Exception as e:
                print(f"[REDIS-CLIENT] ⚠️  Error al cerrar conexión: {e}")
            finally:
                cls._client = None

    @classmethod
    def reset(cls):
        """Resetea el singleton (útil para testing)."""
        cls.close()
        cls._instance = None
        cls._redis_url = 'redis://localhost:6378/0'


# Función helper para obtener cliente fácilmente
def get_redis_client(decode_responses: bool = False) -> redis.Redis:
    """
    Función helper para obtener el cliente Redis.

    Args:
        decode_responses: Si True, decodifica automáticamente bytes a str

    Returns:
        redis.Redis: Cliente de Redis conectado

    Example:
        from shared.state.redis_client import get_redis_client

        client = get_redis_client()
        client.set('key', 'value')
    """
    return RedisClient.get_client(decode_responses=decode_responses)
