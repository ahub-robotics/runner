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

def _verify_broker_available():
    """
    Verifica que el broker de Celery esté disponible.

    Detecta automáticamente si es Redis o RabbitMQ y hace el check apropiado.

    Returns:
        bool: True si el broker está disponible
    """
    import time
    from shared.celery_app.config import BROKER_URL, BACKEND_TYPE

    print(f"[GUNICORN] 🔍 Verificando broker ({BACKEND_TYPE})...")

    if 'redis' in BROKER_URL:
        # Redis broker
        max_attempts = 10
        for attempt in range(1, max_attempts + 1):
            try:
                import redis
                # Extract host and port from redis URL
                if '://' in BROKER_URL:
                    parts = BROKER_URL.split('://')[1].split(':')
                    host = parts[0]
                    port = int(parts[1].split('/')[0]) if len(parts) > 1 else 6379
                else:
                    host, port = 'localhost', 6379

                client = redis.Redis(host=host, port=port, socket_connect_timeout=2)
                client.ping()
                print(f"[GUNICORN] ✅ Redis disponible en {host}:{port}")
                return True
            except Exception as e:
                if attempt == max_attempts:
                    print(f"[GUNICORN] ❌ Redis no disponible después de {max_attempts} intentos: {e}")
                    return False
                print(f"[GUNICORN] ⏳ Redis no responde (intento {attempt}/{max_attempts}), reintentando...")
                time.sleep(1)

    elif 'amqp' in BROKER_URL:
        # RabbitMQ broker
        max_attempts = 10
        for attempt in range(1, max_attempts + 1):
            try:
                import socket
                # Extract host and port from amqp URL
                # amqp://guest:guest@localhost:5672//
                if '://' in BROKER_URL:
                    parts = BROKER_URL.split('://')[1].split('@')
                    if len(parts) > 1:
                        host_port = parts[1].split('/')[0]
                        if ':' in host_port:
                            host, port = host_port.split(':')
                            port = int(port)
                        else:
                            host, port = host_port, 5672
                    else:
                        host, port = 'localhost', 5672
                else:
                    host, port = 'localhost', 5672

                # Test TCP connection to RabbitMQ
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((host, port))
                sock.close()

                if result == 0:
                    print(f"[GUNICORN] ✅ RabbitMQ disponible en {host}:{port}")
                    return True
                else:
                    raise ConnectionError(f"No se pudo conectar a RabbitMQ en {host}:{port}")
            except Exception as e:
                if attempt == max_attempts:
                    print(f"[GUNICORN] ❌ RabbitMQ no disponible después de {max_attempts} intentos: {e}")
                    return False
                print(f"[GUNICORN] ⏳ RabbitMQ no responde (intento {attempt}/{max_attempts}), reintentando...")
                time.sleep(1)

    else:
        print(f"[GUNICORN] ⚠️  Broker desconocido: {BROKER_URL}")
        return True  # Asumir disponible para evitar bloquear startup


def post_worker_init(worker):
    """
    Hook ejecutado después de que un worker de Gunicorn se inicializa.

    Inicia un thread de Celery worker embebido en cada worker de Gunicorn.
    Esto permite procesar tareas de Celery sin necesidad de un proceso separado.

    Importante: Espera a que el broker esté disponible antes de iniciar Celery.

    Args:
        worker: Gunicorn worker instance
    """
    print(f"[GUNICORN] Worker {worker.pid} iniciado")

    # 1. Verificar que el broker esté disponible
    if not _verify_broker_available():
        print(f"[GUNICORN] ❌ Broker no disponible - no se inicia Celery worker")
        return

    # 2. Iniciar Celery worker thread
    try:
        from shared.celery_app.worker import start_celery_worker_thread
        print(f"[GUNICORN] 🚀 Arrancando Celery worker thread...")
        start_celery_worker_thread()
        print(f"[GUNICORN] ✅ Celery worker thread iniciado")
    except Exception as e:
        print(f"[GUNICORN] ⚠️  Error iniciando Celery worker thread: {e}")
        import traceback
        traceback.print_exc()

    # 3. Inicializar servidor proactivamente (no esperar a primera petición)
    try:
        print(f"[GUNICORN] 🔧 Inicializando servidor...")
        from shared.config.loader import get_config_data
        from executors.server import Server
        from api import set_server
        from shared.state.state import get_state_manager

        state_manager = get_state_manager()

        config = get_config_data()
        server = Server(config)
        set_server(server)

        # Configurar state manager con machine_id
        state_manager.set_machine_id(config['machine_id'])

        # Recuperar ejecuciones huérfanas
        state_manager.mark_orphaned_executions_as_failed()

        # Establecer estado inicial
        server.change_status("free", notify_remote=True)

        print(f"[GUNICORN] ✅ Servidor inicializado (machine_id: {config['machine_id']})")
    except Exception as e:
        print(f"[GUNICORN] ⚠️  Error inicializando servidor: {e}")
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
    """
    Hook ejecutado antes de que el master process se inicie.

    Verifica que el broker de Celery esté disponible antes de iniciar los workers.
    """
    from shared.celery_app.config import BACKEND_TYPE

    print("=" * 60)
    print("  ROBOT RUNNER - Starting Gunicorn Server")
    print("=" * 60)
    print(f"  Bind: {bind}")
    print(f"  Workers: {workers}")
    print(f"  Threads per worker: {threads}")
    print(f"  Worker class: {worker_class}")
    print(f"  Timeout: {timeout}s")
    print(f"  SSL: {'Enabled' if certfile else 'Disabled'}")
    print(f"  Celery Backend: {BACKEND_TYPE}")
    print("=" * 60)

    # Verificar broker antes de iniciar workers
    print(f"\n[GUNICORN] 🔍 Verificando broker de Celery ({BACKEND_TYPE})...")

    if not _verify_broker_available():
        print(f"\n[GUNICORN] ❌ ERROR CRÍTICO: Broker no disponible")
        print(f"[GUNICORN] Por favor, verifica que el broker esté corriendo")
        if BACKEND_TYPE == 'redis':
            print(f"[GUNICORN]   Redis: redis-server --port 6378")
        elif BACKEND_TYPE == 'rabbitmq+sqlite':
            print(f"[GUNICORN]   RabbitMQ: rabbitmq-server")
            print(f"[GUNICORN]   Ver: docs/architecture/windows-architecture.md")
        raise RuntimeError(f"Broker {BACKEND_TYPE} no disponible - no se puede iniciar servidor")

    print("[GUNICORN] ✅ Verificación de dependencias completada\n")


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
