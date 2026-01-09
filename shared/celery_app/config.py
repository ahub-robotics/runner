"""
Celery Configuration for Robot Runner

Auto-configures Celery broker and backend based on operating system:
- Windows: RabbitMQ (broker) + SQLite (backend)
- Linux/macOS: Redis (broker + backend) with fallback to RabbitMQ+SQLite

Compatible with Windows, Linux y macOS.

Características:
    - Worker pool 'threads' para concurrencia real
    - Auto-detección de broker/backend basada en OS y disponibilidad
    - Task tracking y acks tardíos para no perder tareas
    - Concurrency de 2 workers para ejecución + streaming simultáneos
"""
from celery import Celery
import os
import platform
from pathlib import Path


def _get_broker_and_backend():
    """
    Auto-detect appropriate broker and backend for Celery.

    Returns:
        tuple: (broker_url, backend_url, backend_type)
    """
    # Force specific backend via environment variable
    force_backend = os.environ.get('CELERY_BACKEND_TYPE', '').lower()

    if force_backend == 'redis':
        return _get_redis_config()
    elif force_backend == 'rabbitmq':
        return _get_rabbitmq_config()

    # Auto-detect based on OS
    system = platform.system()

    if system == 'Windows':
        print(f"[CELERY-CONFIG] 🪟 Windows detectado → RabbitMQ + SQLite")
        return _get_rabbitmq_config()

    # Linux/macOS - try Redis first
    print(f"[CELERY-CONFIG] 🐧 {system} detectado → Intentando Redis...")

    try:
        import redis
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6378/0')
        client = redis.from_url(redis_url, socket_connect_timeout=2)
        client.ping()
        print(f"[CELERY-CONFIG] ✅ Redis disponible")
        return _get_redis_config()
    except Exception as e:
        print(f"[CELERY-CONFIG] ⚠️  Redis no disponible ({e}) → RabbitMQ + SQLite")
        return _get_rabbitmq_config()


def _get_redis_config():
    """Get Redis configuration."""
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6378/0')
    return redis_url, redis_url, 'redis'


def _get_rabbitmq_config():
    """Get RabbitMQ + SQLite configuration."""
    # RabbitMQ broker
    rabbitmq_url = os.environ.get(
        'RABBITMQ_URL',
        'amqp://guest:guest@localhost:5672//'
    )

    # SQLite backend for results
    robot_dir = Path.home() / 'Robot'
    robot_dir.mkdir(parents=True, exist_ok=True)
    sqlite_path = robot_dir / 'celery_results.db'

    # Celery SQLAlchemy backend URL
    backend_url = os.environ.get(
        'CELERY_RESULT_BACKEND',
        f'db+sqlite:///{sqlite_path}'
    )

    return rabbitmq_url, backend_url, 'rabbitmq+sqlite'


# Get configuration
BROKER_URL, BACKEND_URL, BACKEND_TYPE = _get_broker_and_backend()

print(f"[CELERY-CONFIG] 📡 Broker: {BROKER_URL.split('@')[0] + '@...' if '@' in BROKER_URL else BROKER_URL}")
print(f"[CELERY-CONFIG] 💾 Backend: {BACKEND_URL.split('///')[0] + '///' + '...' if ':///' in BACKEND_URL else BACKEND_URL[:50]}")
print(f"[CELERY-CONFIG] 🏷️  Type: {BACKEND_TYPE}")

# Crear aplicación de Celery
celery_app = Celery(
    'robotrunner',
    broker=BROKER_URL,
    backend=BACKEND_URL
)

# Configuración base de Celery
base_config = {
    # Worker configuration
    'worker_pool': 'threads',  # CRÍTICO: Threading pool para concurrencia real
    'worker_concurrency': 2,  # 2 tareas concurrentes: ejecución + streaming

    # Task configuration
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'UTC',
    'enable_utc': True,

    # Task execution
    'task_acks_late': True,  # Acknowledge después de ejecutar, no antes
    'task_reject_on_worker_lost': True,  # Rechazar tarea si worker muere
    'task_track_started': True,  # Trackear cuando la tarea inicia

    # Result backend
    'result_expires': 86400,  # 24 horas

    # Broker configuration
    'broker_connection_retry_on_startup': True,
    'broker_connection_retry': True,
    'broker_connection_max_retries': 10,

    # Tasks to include
    'include': ['executors.tasks', 'streaming.tasks'],

    # Logging
    'worker_log_format': '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    'worker_task_log_format': '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
}

# Backend-specific configuration
if BACKEND_TYPE == 'redis':
    # Redis-specific settings
    base_config['result_backend_transport_options'] = {
        'master_name': 'mymaster',
        'visibility_timeout': 3600,
    }
elif BACKEND_TYPE == 'rabbitmq+sqlite':
    # SQLite backend settings
    base_config['database_table_names'] = {
        'task': 'celery_taskmeta',
        'group': 'celery_groupmeta',
    }

# Apply configuration
celery_app.conf.update(base_config)

# Auto-discover tasks from executors and streaming
celery_app.autodiscover_tasks(['executors', 'streaming'])

if __name__ == '__main__':
    celery_app.start()
