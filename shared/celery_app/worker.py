"""
Celery Worker Thread Integration for Gunicorn

Este módulo permite ejecutar workers de Celery como threads dentro de los workers
de Gunicorn, evitando la necesidad de procesos separados.

Cada worker de Gunicorn tiene su propio thread de Celery worker.
"""
import threading
import sys

from .config import celery_app

# IMPORTANTE: Importar tasks para registrarlos con Celery
try:
    from executors import tasks  # noqa: F401
    from streaming import tasks as streaming_tasks  # noqa: F401
except ImportError:
    # During migration, these may not be available yet
    pass

# Variable global para almacenar el thread del worker
_celery_worker_thread = None


class CeleryWorkerThread(threading.Thread):
    """Thread que ejecuta un worker de Celery."""

    def __init__(self):
        """Inicializa el thread del worker."""
        super().__init__(daemon=True, name='CeleryWorker')
        self._stop_event = threading.Event()

    def run(self):
        """
        Ejecuta el worker de Celery en este thread.

        El worker se ejecuta hasta que se llame a stop().
        """
        print(f"[CELERY-WORKER] 🚀 Iniciando worker de Celery en thread: {threading.current_thread().name}")

        try:
            # Argumentos para el worker de Celery
            worker_args = [
                'worker',
                '--loglevel=info',
                '--pool=solo',  # CRÍTICO: pool 'solo' para compatibilidad
                '--concurrency=2',  # 2 tareas concurrentes: ejecución + streaming
                '--without-heartbeat',  # Sin heartbeat para evitar problemas con threads
                '--without-gossip',  # Sin gossip para simplificar
                '--without-mingle',  # Sin mingle para evitar delays
            ]

            # Iniciar worker de Celery
            # Nota: worker_main() es bloqueante hasta que el worker se detenga
            celery_app.worker_main(argv=worker_args)

        except Exception as e:
            print(f"[CELERY-WORKER] ❌ Error en worker de Celery: {e}")
            import traceback
            traceback.print_exc()

        print(f"[CELERY-WORKER] ⛔ Worker de Celery detenido")

    def stop(self):
        """
        Detiene el worker de Celery.

        Envía señal de parada al worker.
        """
        print(f"[CELERY-WORKER] 🛑 Deteniendo worker de Celery...")
        self._stop_event.set()

        try:
            # Intentar detener el worker grácilmente
            celery_app.control.shutdown()
        except Exception as e:
            print(f"[CELERY-WORKER] ⚠️  Error al detener worker: {e}")


def start_celery_worker_thread():
    """
    Inicia el thread del worker de Celery.

    Esta función debe llamarse desde el hook post_worker_init de Gunicorn.
    Cada worker de Gunicorn tendrá su propio thread de Celery worker.

    Returns:
        CeleryWorkerThread: El thread iniciado
    """
    global _celery_worker_thread

    # Verificar que no haya un worker ya corriendo
    if _celery_worker_thread is not None and _celery_worker_thread.is_alive():
        print(f"[CELERY-WORKER] ⚠️  Ya hay un worker de Celery corriendo")
        return _celery_worker_thread

    print(f"[CELERY-WORKER] 📡 Iniciando worker de Celery en worker de Gunicorn (PID: {threading.get_ident()})")

    try:
        # Crear y iniciar thread del worker
        _celery_worker_thread = CeleryWorkerThread()
        _celery_worker_thread.start()

        print(f"[CELERY-WORKER] ✅ Worker de Celery iniciado")

        return _celery_worker_thread

    except Exception as e:
        print(f"[CELERY-WORKER] ❌ Error al iniciar worker de Celery: {e}")
        import traceback
        traceback.print_exc()
        raise


def stop_celery_worker_thread():
    """
    Detiene el thread del worker de Celery.

    Esta función debe llamarse desde el hook worker_exit de Gunicorn.

    Returns:
        bool: True si se detuvo exitosamente, False si no había worker corriendo
    """
    global _celery_worker_thread

    if _celery_worker_thread is None or not _celery_worker_thread.is_alive():
        print(f"[CELERY-WORKER] ⚠️  No hay worker de Celery corriendo")
        return False

    print(f"[CELERY-WORKER] 🛑 Deteniendo worker de Celery...")

    try:
        # Detener el worker
        _celery_worker_thread.stop()

        # Esperar a que termine (timeout de 5 segundos)
        _celery_worker_thread.join(timeout=5)

        if _celery_worker_thread.is_alive():
            print(f"[CELERY-WORKER] ⚠️  Worker no terminó en el timeout, forzando salida")
        else:
            print(f"[CELERY-WORKER] ✅ Worker de Celery detenido exitosamente")

        # Limpiar referencia
        _celery_worker_thread = None

        return True

    except Exception as e:
        print(f"[CELERY-WORKER] ❌ Error al detener worker de Celery: {e}")
        import traceback
        traceback.print_exc()
        return False


def is_worker_running():
    """
    Verifica si el worker de Celery está corriendo.

    Returns:
        bool: True si el worker está corriendo, False en caso contrario
    """
    global _celery_worker_thread
    return _celery_worker_thread is not None and _celery_worker_thread.is_alive()
