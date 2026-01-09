"""
State Backend Factory

Auto-detects the appropriate state backend based on:
1. Environment variable (FORCE_REDIS, FORCE_SQLITE)
2. Operating system (Windows → SQLite, Linux/macOS → Redis)
3. Availability (try Redis, fallback to SQLite)
"""
import os
import platform
from typing import Optional
from .base import StateBackend
from .sqlite_backend import SQLiteStateBackend


# Singleton instance
_backend_instance: Optional[StateBackend] = None


def get_state_backend(force_backend: Optional[str] = None) -> StateBackend:
    """
    Get the appropriate state backend for the current system.

    The backend is selected in this priority order:
    1. force_backend parameter (if provided)
    2. ROBOT_STATE_BACKEND environment variable
    3. Auto-detection based on OS and availability

    Args:
        force_backend: Force a specific backend ('redis' or 'sqlite').
                      Overrides auto-detection.

    Returns:
        StateBackend: Configured backend instance

    Example:
        # Auto-detect
        backend = get_state_backend()

        # Force Redis
        backend = get_state_backend(force_backend='redis')

        # Force SQLite
        backend = get_state_backend(force_backend='sqlite')
    """
    global _backend_instance

    # Return singleton if already created (unless forcing different backend)
    if _backend_instance is not None and force_backend is None:
        return _backend_instance

    # Determine which backend to use
    backend_type = (
        force_backend or
        os.environ.get('ROBOT_STATE_BACKEND', '').lower() or
        _auto_detect_backend()
    )

    print(f"[STATE-FACTORY] 🏭 Seleccionando backend: {backend_type}")

    # Create backend instance
    if backend_type == 'redis':
        _backend_instance = _create_redis_backend()
    elif backend_type == 'sqlite':
        _backend_instance = _create_sqlite_backend()
    else:
        raise ValueError(f"Unknown backend type: {backend_type}")

    return _backend_instance


def _auto_detect_backend() -> str:
    """
    Auto-detect the best backend for the current system.

    Logic:
    - Windows → SQLite (Redis not native)
    - Linux/macOS → Try Redis, fallback to SQLite
    """
    system = platform.system()

    if system == 'Windows':
        print(f"[STATE-FACTORY] 🪟 Windows detectado → SQLite")
        return 'sqlite'

    # Linux/macOS - try Redis first
    print(f"[STATE-FACTORY] 🐧 {system} detectado → Intentando Redis...")

    try:
        # Try to import redis and test connection
        from .redis_backend import RedisStateBackend
        test_backend = RedisStateBackend()
        if test_backend.ping():
            print(f"[STATE-FACTORY] ✅ Redis disponible")
            return 'redis'
        else:
            print(f"[STATE-FACTORY] ⚠️  Redis no responde → Fallback a SQLite")
            return 'sqlite'
    except Exception as e:
        print(f"[STATE-FACTORY] ⚠️  Redis no disponible ({e}) → Fallback a SQLite")
        return 'sqlite'


def _create_redis_backend() -> StateBackend:
    """Create and configure Redis backend."""
    from .redis_backend import RedisStateBackend

    # Get Redis URL from environment or use default
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6378/0')

    try:
        backend = RedisStateBackend(redis_url)
        print(f"[STATE-FACTORY] ✅ Redis backend creado")
        return backend
    except Exception as e:
        print(f"[STATE-FACTORY] ❌ Error creando Redis backend: {e}")
        print(f"[STATE-FACTORY] 🔄 Fallback a SQLite...")
        return _create_sqlite_backend()


def _create_sqlite_backend() -> StateBackend:
    """Create and configure SQLite backend."""
    # Get DB path from environment or use default
    db_path = os.environ.get('SQLITE_DB_PATH', None)  # None uses default

    backend = SQLiteStateBackend(db_path)
    print(f"[STATE-FACTORY] ✅ SQLite backend creado")
    return backend


def reset_backend():
    """
    Reset the singleton backend instance.

    Useful for testing or forcing a backend reload.
    """
    global _backend_instance

    if _backend_instance is not None:
        try:
            _backend_instance.close()
        except:
            pass
        _backend_instance = None
        print(f"[STATE-FACTORY] 🔄 Backend reset")


def get_backend_info() -> dict:
    """
    Get information about the current backend.

    Returns:
        dict: Backend information including type, connection status, etc.
    """
    global _backend_instance

    if _backend_instance is None:
        return {'status': 'not_initialized'}

    backend_type = type(_backend_instance).__name__

    info = {
        'type': backend_type,
        'connected': _backend_instance.ping(),
    }

    # Add backend-specific stats if available
    if hasattr(_backend_instance, 'get_stats'):
        try:
            info['stats'] = _backend_instance.get_stats()
        except:
            pass

    return info
