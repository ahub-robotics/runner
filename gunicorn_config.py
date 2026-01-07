"""
Gunicorn Configuration for Robot Runner.

This configuration file sets up Gunicorn to run the Flask application
with embedded Celery workers in each Gunicorn worker process.

Usage:
    gunicorn api.wsgi:app --config gunicorn_config.py
    
    Or programmatically:
    python -c "from api.gunicorn_server import start_gunicorn_server; start_gunicorn_server()"
"""
import os
import sys
from pathlib import Path


# ============================================================================
# BASIC CONFIGURATION
# ============================================================================

# Server socket
bind = "0.0.0.0:5001"  # Default port, can be overridden

# Worker processes
workers = 1  # 1 worker para evitar fork issues con CoreFoundation en macOS
threads = 4  # Más threads para compensar menos workers
worker_class = "gthread"  # Thread-based workers

# Timeouts
timeout = 120  # Request timeout en segundos
graceful_timeout = 30  # Tiempo para terminar requests al shutdown
keepalive = 5  # Keep-alive timeout

# Logging
loglevel = "error"  # Solo mostrar errores, no warnings
accesslog = None  # No access log (usamos nuestro propio logging)
errorlog = "-"  # Error log to stderr

# Application preloading
preload_app = True  # Precargar la app antes del fork para evitar issues


# ============================================================================
# SSL/TLS CONFIGURATION
# ============================================================================

# SSL certificates (si existen)
PROJECT_ROOT = Path(__file__).parent
certfile = str(PROJECT_ROOT / "ssl" / "cert.pem")
keyfile = str(PROJECT_ROOT / "ssl" / "key.pem")

# Verificar que los certificados existen
if not Path(certfile).exists() or not Path(keyfile).exists():
    print(f"[WARNING] SSL certificates not found:")
    print(f"  - certfile: {certfile}")
    print(f"  - keyfile: {keyfile}")
    print(f"[WARNING] Running without SSL. Generate certificates first.")
    certfile = None
    keyfile = None


# ============================================================================
# CELERY WORKER HOOKS
# ============================================================================

def post_worker_init(worker):
    """
    Hook ejecutado después de que un worker de Gunicorn se inicializa.
    
    Inicia un thread de Celery worker embebido en cada worker de Gunicorn.
    Esto permite procesar tareas de Celery sin necesidad de un proceso separado.
    
    Args:
        worker: Gunicorn worker instance
    """
    try:
        from shared.celery_app.worker import start_celery_worker_thread
        print(f"[GUNICORN] Worker {worker.pid} iniciado, arrancando Celery worker thread")
        start_celery_worker_thread()
    except Exception as e:
        print(f"[GUNICORN] ⚠️  Error iniciando Celery worker thread: {e}")
        import traceback
        traceback.print_exc()


def worker_exit(server, worker):
    """
    Hook ejecutado cuando un worker de Gunicorn termina.
    
    Detiene el thread de Celery worker embebido de forma grácil.
    
    Args:
        server: Gunicorn server instance
        worker: Gunicorn worker instance
    """
    try:
        from shared.celery_app.worker import stop_celery_worker_thread
        print(f"[GUNICORN] Worker {worker.pid} terminando, deteniendo Celery worker thread")
        stop_celery_worker_thread()
    except Exception as e:
        print(f"[GUNICORN] ⚠️  Error deteniendo Celery worker thread: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# ADDITIONAL HOOKS
# ============================================================================

def on_starting(server):
    """Hook ejecutado antes de que el master process se inicie."""
    print("=" * 60)
    print("  ROBOT RUNNER - Starting Gunicorn Server")
    print("=" * 60)
    print(f"  Bind: {bind}")
    print(f"  Workers: {workers}")
    print(f"  Threads per worker: {threads}")
    print(f"  Worker class: {worker_class}")
    print(f"  Timeout: {timeout}s")
    print(f"  SSL: {'Enabled' if certfile else 'Disabled'}")
    print("=" * 60)


def on_exit(server):
    """Hook ejecutado cuando el servidor se detiene."""
    print("\n[GUNICORN] 🛑 Servidor Gunicorn detenido")


def when_ready(server):
    """Hook ejecutado cuando el servidor está listo para aceptar conexiones."""
    print(f"\n[GUNICORN] ✅ Servidor listo en https://{bind}")
    print(f"[GUNICORN] PID del master process: {os.getpid()}")


# ============================================================================
# PROCESS NAMING
# ============================================================================

proc_name = "robot_runner"  # Nombre del proceso para ps/top


# ============================================================================
# DEVELOPMENT vs PRODUCTION
# ============================================================================

# En desarrollo, puedes habilitar reload para auto-restart
# reload = True  # Solo para desarrollo
# reload_extra_files = [...]  # Archivos adicionales para watch
