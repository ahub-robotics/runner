"""
Celery Configuration for Robot Runner

Este módulo configura Celery para ejecutar robots de manera asíncrona usando Redis
como broker y backend. Compatible con Windows, Linux y macOS.

Características:
    - Worker pool 'solo' para compatibilidad con Windows y threading de Gunicorn
    - Redis como broker y backend de resultados
    - Task tracking y acks tardíos para no perder tareas
    - Concurrency de 1 worker por proceso de Gunicorn
"""
from celery import Celery
import os

# Redis URL (local por defecto)
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6378/0')

# Crear aplicación de Celery
celery_app = Celery(
    'robotrunner',
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Configuración de Celery
celery_app.conf.update(
    # Worker configuration
    worker_pool='threads',  # CRÍTICO: Threading pool para concurrencia real
    worker_concurrency=2,  # 2 tareas concurrentes: ejecución + streaming

    # Task configuration
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Task execution
    task_acks_late=True,  # Acknowledge después de ejecutar, no antes
    task_reject_on_worker_lost=True,  # Rechazar tarea si worker muere
    task_track_started=True,  # Trackear cuando la tarea inicia

    # Result backend
    result_expires=864000,  # 24 horas
    result_backend_transport_options={
        'master_name': 'mymaster',
        'visibility_timeout': 3600,
    },

    # Broker configuration
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,

    # Tasks to include
    include=['executors.tasks', 'streaming.tasks'],

    # Logging
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)

# Auto-discover tasks from executors and streaming
celery_app.autodiscover_tasks(['executors', 'streaming'])

if __name__ == '__main__':
    celery_app.start()
