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
        from shared.state.state import get_state_manager
        state_manager = get_state_manager()

        # Verificar si ya hay streaming activo
        state = state_manager.hgetall('streaming:state')

        # Normalizar bytes a strings
        state_dict = {}
        for k, v in state.items():
            k_str = k.decode('utf-8') if isinstance(k, bytes) else k
            v_str = v.decode('utf-8') if isinstance(v, bytes) else v
            state_dict[k_str] = v_str

        if state_dict and state_dict.get('active') == 'true':
            print(f"[STREAMING-TASK] ⚠️  Ya hay streaming activo")
            return {
                'status': 'already_running',
                'message': 'Streaming already active'
            }

        # Marcar como activo en el state backend
        state_manager.hset('streaming:state', {
            'active': 'true',
            'task_id': self.request.id,
            'host': host,
            'port': str(port),
            'fps': str(fps),
            'quality': str(quality),
            'started_at': str(time.time())
        })

        print(f"[STREAMING-TASK] ✅ Streaming marcado como activo en backend")

        # Mantener la tarea viva mientras el streaming esté activo
        # Verificar cada segundo si se solicitó detener o si no hay clientes
        task_start_time = time.time()
        grace_period = 120  # 2 minutos de gracia para que se conecte el primer cliente
        inactivity_timeout = 60  # 60 segundos sin clientes después de actividad → auto-stop
        had_clients = False  # Flag para saber si alguna vez tuvo clientes

        print(f"[STREAMING-TASK] Período de gracia: {grace_period}s para primer cliente")
        print(f"[STREAMING-TASK] Timeout de inactividad: {inactivity_timeout}s después de actividad")

        while True:
            time.sleep(1)

            # Verificar si se solicitó detener
            stop_requested = state_manager.get('streaming:stop_requested')
            if stop_requested:
                stop_str = stop_requested.decode('utf-8') if isinstance(stop_requested, bytes) else stop_requested
                if stop_str == 'true':
                    print(f"[STREAMING-TASK] 🛑 Detención solicitada desde backend")
                    break

            # Verificar que el estado siga activo (por si se limpió externamente)
            state = state_manager.hgetall('streaming:state')
            state_dict = {}
            for k, v in state.items():
                k_str = k.decode('utf-8') if isinstance(k, bytes) else k
                v_str = v.decode('utf-8') if isinstance(v, bytes) else v
                state_dict[k_str] = v_str

            if not state_dict or state_dict.get('active') != 'true':
                print(f"[STREAMING-TASK] ⚠️  Estado de streaming ya no está activo")
                break

            # Verificar si hay clientes conectados (via timestamp)
            last_activity_str = state_manager.get('streaming:last_client_activity')

            if last_activity_str:
                # Hay actividad registrada - marcar que tuvo clientes
                had_clients = True

                # Verificar si es reciente
                try:
                    last_activity_decoded = last_activity_str.decode('utf-8') if isinstance(last_activity_str, bytes) else last_activity_str
                    last_activity = float(last_activity_decoded)
                    inactive_time = time.time() - last_activity

                    # Solo aplicar timeout si ya pasó el período de gracia
                    time_since_start = time.time() - task_start_time
                    if time_since_start > grace_period and inactive_time > inactivity_timeout:
                        print(f"[STREAMING-TASK] ⏱️  Sin clientes por {int(inactive_time)}s → auto-stop")
                        break
                except Exception as e:
                    print(f"[STREAMING-TASK] Error verificando actividad: {e}")
            else:
                # No hay actividad registrada
                time_since_start = time.time() - task_start_time

                # Si ya tuvo clientes antes y ahora no hay actividad, aplicar timeout
                if had_clients:
                    if time_since_start > grace_period:
                        print(f"[STREAMING-TASK] ⏱️  Clientes desconectados, sin actividad → auto-stop")
                        break
                else:
                    # Nunca tuvo clientes - verificar período de gracia
                    if time_since_start > grace_period:
                        print(f"[STREAMING-TASK] ⏱️  Sin clientes durante {grace_period}s desde inicio → auto-stop")
                        break

        # Limpiar estado en el backend
        state_manager.delete('streaming:state', 'streaming:stop_requested')

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
            from shared.state.state import get_state_manager
            state_manager = get_state_manager()
            state_manager.delete('streaming:state', 'streaming:stop_requested')
        except:
            pass

        return {
            'status': 'error',
            'message': str(e)
        }


@celery_app.task(name='streaming.tasks.stop_streaming_task')
def stop_streaming_task():
    """
    Detiene el streaming de video enviando señal de detención via state backend.

    Returns:
        dict: Estado de la operación
    """
    print(f"[STREAMING-TASK] Solicitando detención del streaming")

    try:
        from shared.state.state import get_state_manager
        state_manager = get_state_manager()

        # Verificar si hay streaming activo
        state = state_manager.hgetall('streaming:state')

        # Normalizar bytes a strings
        state_dict = {}
        for k, v in state.items():
            k_str = k.decode('utf-8') if isinstance(k, bytes) else k
            v_str = v.decode('utf-8') if isinstance(v, bytes) else v
            state_dict[k_str] = v_str

        if not state_dict or state_dict.get('active') != 'true':
            print(f"[STREAMING-TASK] ⚠️  No hay streaming activo")
            return {
                'status': 'not_running',
                'message': 'No active streaming to stop'
            }

        # Solicitar detención (sin TTL por ahora - se limpiará cuando la tarea pare)
        state_manager.set('streaming:stop_requested', 'true')

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
    Obtiene el estado actual del streaming desde el state backend.

    Returns:
        dict: Estado del streaming
    """
    try:
        from shared.state.state import get_state_manager
        state_manager = get_state_manager()

        # Obtener estado desde el backend
        state = state_manager.hgetall('streaming:state')

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
