# Windows Architecture - RabbitMQ + SQLite

## Problema

Redis no es nativo en Windows, lo que causa problemas de compatibilidad para deployment en máquinas Windows.

## Solución: Arquitectura Híbrida

### Componentes por Sistema Operativo

| Componente | Linux/macOS | Windows |
|------------|-------------|---------|
| **Celery Broker** | Redis | RabbitMQ |
| **Celery Backend** | Redis | SQLite |
| **Estado Compartido** | Redis | SQLite |
| **Streaming State** | Redis | SQLite |

### Auto-detección

El sistema detecta automáticamente el SO y usa el backend apropiado:

```python
import platform

if platform.system() == 'Windows':
    # RabbitMQ + SQLite
    BROKER_URL = 'amqp://guest:guest@localhost:5672//'
    BACKEND_URL = 'db+sqlite:///~/Robot/celery_results.db'
    state_backend = SQLiteStateBackend()
else:
    # Redis (más rápido)
    BROKER_URL = 'redis://localhost:6378/0'
    BACKEND_URL = 'redis://localhost:6378/0'
    state_backend = RedisStateBackend()
```

## Implementación

### 1. Estado Compartido (State Backend Abstraction)

Crear capa de abstracción con dos implementaciones:

#### `shared/state/backends/base.py`
```python
class StateBackend(ABC):
    @abstractmethod
    def hset(self, key: str, mapping: dict): pass

    @abstractmethod
    def hgetall(self, key: str) -> dict: pass

    @abstractmethod
    def set(self, key: str, value: str): pass

    @abstractmethod
    def get(self, key: str) -> str: pass

    @abstractmethod
    def delete(self, key: str): pass
```

#### `shared/state/backends/redis_backend.py`
```python
class RedisStateBackend(StateBackend):
    def __init__(self, url='redis://localhost:6378/0'):
        self.client = redis.from_url(url)

    def hset(self, key, mapping):
        return self.client.hset(key, mapping=mapping)

    # ... otros métodos
```

#### `shared/state/backends/sqlite_backend.py`
```python
import sqlite3
import json

class SQLiteStateBackend(StateBackend):
    def __init__(self, db_path='~/Robot/state.db'):
        self.db_path = os.path.expanduser(db_path)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS kv_store (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS hash_store (
                key TEXT,
                field TEXT,
                value TEXT,
                PRIMARY KEY (key, field)
            )
        ''')
        conn.commit()
        conn.close()

    def hset(self, key, mapping):
        conn = sqlite3.connect(self.db_path)
        for field, value in mapping.items():
            conn.execute(
                'INSERT OR REPLACE INTO hash_store (key, field, value) VALUES (?, ?, ?)',
                (key, field, str(value))
            )
        conn.commit()
        conn.close()

    def hgetall(self, key):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            'SELECT field, value FROM hash_store WHERE key = ?',
            (key,)
        )
        result = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return result

    def set(self, key, value):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            'INSERT OR REPLACE INTO kv_store (key, value) VALUES (?, ?)',
            (key, str(value))
        )
        conn.commit()
        conn.close()

    def get(self, key):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('SELECT value FROM kv_store WHERE key = ?', (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def delete(self, key):
        conn = sqlite3.connect(self.db_path)
        conn.execute('DELETE FROM kv_store WHERE key = ?', (key,))
        conn.execute('DELETE FROM hash_store WHERE key = ?', (key,))
        conn.commit()
        conn.close()
```

### 2. Celery Configuration

#### `shared/celery_app/config.py`
```python
import os
import platform

# Auto-detect backend based on OS
IS_WINDOWS = platform.system() == 'Windows'

if IS_WINDOWS:
    # Windows: RabbitMQ + SQLite
    BROKER_URL = os.environ.get('CELERY_BROKER', 'amqp://guest:guest@localhost:5672//')
    BACKEND_URL = os.environ.get('CELERY_BACKEND', 'db+sqlite:///~/Robot/celery_results.db')
else:
    # Linux/macOS: Redis (más rápido)
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6378/0')
    BROKER_URL = REDIS_URL
    BACKEND_URL = REDIS_URL

celery_app = Celery(
    'robotrunner',
    broker=BROKER_URL,
    backend=BACKEND_URL
)
```

### 3. Gestión de Dependencias

#### Linux/macOS (Redis)
```bash
# Instalar Redis
brew install redis  # macOS
sudo apt install redis-server  # Ubuntu

# Iniciar Redis
redis-server --port 6378
```

#### Windows (RabbitMQ)
```powershell
# Descargar e instalar Erlang (prerequisito)
# https://www.erlang.org/downloads

# Descargar e instalar RabbitMQ
# https://www.rabbitmq.com/install-windows.html

# Iniciar RabbitMQ
rabbitmq-server
```

### 4. Ventajas de esta Arquitectura

✅ **Multiplataforma**: Funciona en Windows, Linux y macOS sin cambios
✅ **Sin instalación en Windows**: SQLite incluido en Python
✅ **Robusto**: RabbitMQ es excelente para colas de mensajes
✅ **Transparente**: La aplicación no necesita saber qué backend usa
✅ **Testeable**: Fácil mockear backends en tests

### 5. Desventajas

⚠️ **Rendimiento**: SQLite más lento que Redis (pero suficiente para tu caso)
⚠️ **RabbitMQ requiere instalación**: Pero tiene instalador oficial y es simple
⚠️ **Mantenimiento**: Dos backends en lugar de uno

## Testing

### Unit Tests
```python
# tests/unit/test_state_backends.py
def test_redis_backend():
    backend = RedisStateBackend()
    backend.set('test', 'value')
    assert backend.get('test') == 'value'

def test_sqlite_backend():
    backend = SQLiteStateBackend(':memory:')
    backend.set('test', 'value')
    assert backend.get('test') == 'value'
```

### Integration Tests
```python
# tests/integration/test_state_cross_platform.py
def test_state_operations_work_on_any_backend():
    from shared.state import get_state_backend
    backend = get_state_backend()  # Auto-detected

    # Same interface, different implementation
    backend.hset('exec:123', {'status': 'running'})
    assert backend.hgetall('exec:123')['status'] == 'running'
```

## Migration Steps

1. ✅ Crear backends abstractos
2. ✅ Implementar SQLiteStateBackend
3. ✅ Implementar RedisStateBackend (wrapper actual)
4. ✅ Actualizar redis_state.py para usar backends
5. ✅ Actualizar Celery config para auto-detect
6. ✅ Testing en ambos sistemas
7. ✅ Actualizar documentación

## Rollback Plan

Si algo falla, mantener Redis-only mode:
```python
# shared/celery_app/config.py
FORCE_REDIS = os.environ.get('FORCE_REDIS', 'false').lower() == 'true'

if FORCE_REDIS:
    BROKER_URL = 'redis://localhost:6378/0'
    BACKEND_URL = 'redis://localhost:6378/0'
```

## Referencias

- [Celery SQLAlchemy Backend](https://docs.celeryproject.org/en/stable/userguide/configuration.html#sqlalchemy-result-backend)
- [RabbitMQ Windows Install](https://www.rabbitmq.com/install-windows.html)
- [SQLite Python](https://docs.python.org/3/library/sqlite3.html)
