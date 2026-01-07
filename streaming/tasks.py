"""
Tareas de Celery para gestionar el streaming de video.

Este módulo maneja el estado del streaming de video de manera simple:
- Las tareas solo gestionan el estado en Redis
- La captura y transmisión de frames se hace en /stream/feed via SSE
"""
import time
from shared.celery_app.config import celery_app


@celery_app.task(bind=True, name='streaming.tasks.start_streaming_task')
def start_streaming_task(self, host='0.0.0.0', port=8765, fps=15, quality=50, use_ssl=True):
    """
    Inicia el streaming de video marcando el estado como activo en Redis.

    Esta tarea solo gestiona el estado - la captura y transmisión real
    se hace en /stream/feed via SSE.

    Args:
        host (str): Host (no usado, pero mantenido para compatibilidad)
        port (int): Puerto (no usado, pero mantenido para compatibilidad)
        fps (int): Frames por segundo
        quality (int): Calidad JPEG (1-100)
        use_ssl (bool): Si usar SSL/TLS (no usado aquí)

    Returns:
        dict: Estado del streaming
    """
    print(f"[STREAMING-TASK] Iniciando streaming")
    print(f"[STREAMING-TASK] - Task ID: {self.request.id}")
    print(f"[STREAMING-TASK] - Config: {fps}fps, quality={quality}")

    try:
        from shared.state.redis_state import redis_state
        redis_client = redis_state._get_redis_client()

        # Verificar si ya hay streaming activo
        state = redis_client.hgetall('streaming:state')
        if state and state.get(b'active') == b'true':
            print(f"[STREAMING-TASK] ⚠️  Ya hay streaming activo")
            return {
                'status': 'already_running',
                'message': 'Streaming already active'
            }

        # Marcar como activo en Redis
        redis_client.hset('streaming:state', mapping={
            'active': 'true',
            'task_id': self.request.id,
            'host': host,
            'port': str(port),
            'fps': str(fps),
            'quality': str(quality),
            'started_at': str(time.time())
        })

        print(f"[STREAMING-TASK] ✅ Streaming marcado como activo en Redis")

        # Mantener la tarea viva mientras el streaming esté activo
        # Verificar cada segundo si se solicitó detener o si no hay clientes
        task_start_time = time.time()
        inactivity_timeout = 30  # 30 segundos sin clientes → auto-stop

        while True:
            time.sleep(1)

            # Verificar si se solicitó detener
            stop_requested = redis_client.get('streaming:stop_requested')
            if stop_requested and stop_requested.decode('utf-8') == 'true':
                print(f"[STREAMING-TASK] 🛑 Detención solicitada desde Redis")
                break

            # Verificar que el estado siga activo (por si se limpió externamente)
            state = redis_client.hgetall('streaming:state')
            if not state or state.get(b'active') != b'true':
                print(f"[STREAMING-TASK] ⚠️  Estado de streaming ya no está activo")
                break

            # Verificar si hay clientes conectados (via timestamp)
            last_activity_str = redis_client.get('streaming:last_client_activity')

            if last_activity_str:
                # Hay actividad registrada - verificar si es reciente
                try:
                    last_activity = float(last_activity_str.decode('utf-8'))
                    inactive_time = time.time() - last_activity

                    if inactive_time > inactivity_timeout:
                        print(f"[STREAMING-TASK] ⏱️  Sin clientes por {int(inactive_time)}s → auto-stop")
                        break
                except Exception as e:
                    print(f"[STREAMING-TASK] Error verificando actividad: {e}")
            else:
                # No hay actividad registrada - verificar tiempo desde inicio
                time_since_start = time.time() - task_start_time
                if time_since_start > inactivity_timeout:
                    print(f"[STREAMING-TASK] ⏱️  Sin clientes desde inicio ({int(time_since_start)}s) → auto-stop")
                    break

        # Limpiar estado en Redis
        redis_client.delete('streaming:state')
        redis_client.delete('streaming:stop_requested')

        print(f"[STREAMING-TASK] ✅ Streaming detenido correctamente")

        return {
            'status': 'stopped',
            'message': 'Streaming stopped successfully'
        }

    except Exception as e:
        print(f"[STREAMING-TASK] ❌ Error: {e}")
        import traceback
        traceback.print_exc()

        # Limpiar en caso de error
        try:
            from shared.state.redis_state import redis_state
            redis_client = redis_state._get_redis_client()
            redis_client.delete('streaming:state')
            redis_client.delete('streaming:stop_requested')
        except:
            pass

        return {
            'status': 'error',
            'message': str(e)
        }


@celery_app.task(name='streaming.tasks.stop_streaming_task')
def stop_streaming_task():
    """
    Detiene el streaming de video enviando señal de detención via Redis.

    Returns:
        dict: Estado de la operación
    """
    print(f"[STREAMING-TASK] Solicitando detención del streaming")

    try:
        from shared.state.redis_state import redis_state
        redis_client = redis_state._get_redis_client()

        # Verificar si hay streaming activo
        state = redis_client.hgetall('streaming:state')
        if not state or state.get(b'active') != b'true':
            print(f"[STREAMING-TASK] ⚠️  No hay streaming activo")
            return {
                'status': 'not_running',
                'message': 'No active streaming to stop'
            }

        # Solicitar detención
        redis_client.set('streaming:stop_requested', 'true', ex=60)  # TTL 60s

        print(f"[STREAMING-TASK] ✅ Señal de detención enviada")

        return {
            'status': 'stopping',
            'message': 'Stop signal sent to streaming task'
        }

    except Exception as e:
        print(f"[STREAMING-TASK] ❌ Error: {e}")
        import traceback
        traceback.print_exc()

        return {
            'status': 'error',
            'message': str(e)
        }


@celery_app.task(name='streaming.tasks.get_streaming_status')
def get_streaming_status():
    """
    Obtiene el estado actual del streaming desde Redis.

    Returns:
        dict: Estado del streaming
    """
    try:
        from shared.state.redis_state import redis_state
        redis_client = redis_state._get_redis_client()

        # Obtener estado desde Redis
        state = redis_client.hgetall('streaming:state')

        if not state:
            return {
                'active': False,
                'clients': 0
            }

        # Convertir bytes a str
        state_dict = {}
        for k, v in state.items():
            k_str = k.decode('utf-8') if isinstance(k, bytes) else k
            v_str = v.decode('utf-8') if isinstance(v, bytes) else v
            state_dict[k_str] = v_str

        return {
            'active': state_dict.get('active') == 'true',
            'task_id': state_dict.get('task_id'),
            'host': state_dict.get('host'),
            'port': int(state_dict.get('port', 0)),
            'fps': int(state_dict.get('fps', 0)),
            'quality': int(state_dict.get('quality', 0)),
            'started_at': float(state_dict.get('started_at', 0)),
            'clients': 0  # No se trackean en modo SSE
        }

    except Exception as e:
        print(f"[STREAMING-TASK] ❌ Error obteniendo estado: {e}")
        return {
            'active': False,
            'clients': 0,
            'error': str(e)
        }
