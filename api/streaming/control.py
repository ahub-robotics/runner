"""
Streaming Control Endpoints.

Provides streaming control endpoints:
    - POST /stream/start: Start screen streaming via Celery task
    - POST /stream/stop: Stop screen streaming
    - GET /stream/status: Get streaming status from state backend
"""
import time
import traceback
from flask import Blueprint, jsonify
from api.auth import require_auth
from shared.state.state import get_state_manager
from shared.celery_app.config import celery_app


# Create blueprint
streaming_control_bp = Blueprint('streaming_control', __name__, url_prefix='/stream')


@streaming_control_bp.route('/start', methods=['POST'])
@require_auth
def start_streaming():
    """
    POST /stream/start - Inicia el streaming de pantalla via Celery task.

    Returns:
        JSON: Estado de la operación

    Example Response:
        {
            "success": true,
            "message": "Streaming iniciado correctamente",
            "task_id": "celery-task-id"
        }
    """
    print("[STREAM-API] POST /stream/start recibido")

    try:
        # Verificar si ya está activo consultando el state backend
        state_manager = get_state_manager()
        state = state_manager.hgetall('streaming:state')

        # Normalizar bytes a strings
        state_dict = {}
        for k, v in state.items():
            k_str = k.decode('utf-8') if isinstance(k, bytes) else k
            v_str = v.decode('utf-8') if isinstance(v, bytes) else v
            state_dict[k_str] = v_str

        print(f"[STREAM-API] Estado actual en backend: {state_dict}")

        if state_dict and state_dict.get('active') == 'true':
            # Verificar si la tarea realmente existe en Celery
            task_id = state_dict.get('task_id', '')
            print(f"[STREAM-API] Verificando tarea existente: {task_id}")

            try:
                from celery.result import AsyncResult
                task_result = AsyncResult(task_id, app=celery_app)
                task_state = task_result.state

                print(f"[STREAM-API] Estado de la tarea en Celery: {task_state}")

                # Estados válidos de tareas corriendo: STARTED, RETRY
                # Estados de tareas no corriendo: PENDING, FAILURE, SUCCESS, REVOKED
                if task_state in ['STARTED', 'RETRY']:
                    print("[STREAM-API] Streaming ya está activo y tarea está corriendo")
                    return jsonify({
                        'success': False,
                        'message': 'El streaming ya está activo'
                    }), 400
                elif task_state == 'PENDING':
                    # Dar tiempo de gracia MUCHO MÁS LARGO a tareas PENDING
                    # En Windows, Celery puede tardar más en procesar tareas
                    started_at_str = state_dict.get('started_at')
                    if started_at_str:
                        started_at = float(started_at_str)
                        time_elapsed = time.time() - started_at
                        grace_period = 300  # 5 minutos de gracia

                        if time_elapsed < grace_period:
                            print(f"[STREAM-API] Tarea PENDING reciente ({time_elapsed:.1f}s), dando tiempo de gracia...")
                            return jsonify({
                                'success': False,
                                'message': 'El streaming se está iniciando, espera unos segundos'
                            }), 400

                    print(f"[STREAM-API] ⚠️  Estado huérfano detectado (tarea PENDING > 5min)")
                    print(f"[STREAM-API] ⚠️  Esto indica que el worker de Celery NO está funcionando")
                    print(f"[STREAM-API] ⚠️  Reinicia el servidor para que el worker se inicie correctamente")
                    state_manager.delete('streaming:state', 'streaming:stop_requested')
                    print("[STREAM-API] Estado huérfano limpiado, continuando con inicio")
                else:
                    print(f"[STREAM-API] ⚠️  Estado huérfano detectado (tarea {task_state}), limpiando...")
                    state_manager.delete('streaming:state', 'streaming:stop_requested')
                    print("[STREAM-API] Estado huérfano limpiado, continuando con inicio")
            except Exception as e:
                print(f"[STREAM-API] Error verificando tarea, asumiendo huérfano: {e}")
                state_manager.delete('streaming:state', 'streaming:stop_requested')

        # Iniciar tarea de Celery en segundo plano
        print("[STREAM-API] Iniciando tarea de Celery...")
        from streaming.tasks import start_streaming_task
        task = start_streaming_task.delay(
            host='0.0.0.0',
            port=8765,
            fps=15,
            quality=75,
            use_ssl=True
        )

        print(f"[STREAM-API] ✅ Tarea de streaming iniciada: {task.id}")

        # Esperar un momento para que se registre en el backend
        time.sleep(0.5)

        # Verificar que se registró
        state = state_manager.hgetall('streaming:state')
        print(f"[STREAM-API] Estado después de iniciar: {state}")

        return jsonify({
            'success': True,
            'message': 'Streaming iniciado correctamente',
            'task_id': task.id
        }), 200

    except Exception as e:
        print(f"[STREAM-API] ❌ Error al iniciar streaming: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error al iniciar streaming: {str(e)}'
        }), 500


@streaming_control_bp.route('/stop', methods=['POST'])
@require_auth
def stop_streaming():
    """
    POST /stream/stop - Detiene el streaming de pantalla via Celery task.

    Returns:
        JSON: Estado de la operación

    Example Response:
        {
            "success": true,
            "message": "Streaming detenido correctamente",
            "task_id": "celery-task-id"
        }
    """
    print("[STREAM-API] POST /stream/stop recibido")

    try:
        # Verificar si hay streaming activo en el state backend
        state_manager = get_state_manager()
        state = state_manager.hgetall('streaming:state')

        # Normalizar bytes a strings
        state_dict = {}
        for k, v in state.items():
            k_str = k.decode('utf-8') if isinstance(k, bytes) else k
            v_str = v.decode('utf-8') if isinstance(v, bytes) else v
            state_dict[k_str] = v_str

        print(f"[STREAM-API] Estado actual en backend: {state_dict}")

        if not state_dict or state_dict.get('active') != 'true':
            print("[STREAM-API] No hay streaming activo para detener")
            return jsonify({
                'success': False,
                'message': 'No hay streaming activo'
            }), 400

        # Llamar a la tarea de detención
        print("[STREAM-API] Enviando señal de detención...")
        from streaming.tasks import stop_streaming_task
        result = stop_streaming_task.delay()

        print(f"[STREAM-API] ✅ Señal de detención enviada: {result.id}")

        # Esperar un momento para verificar
        time.sleep(0.5)

        state = state_manager.hgetall('streaming:state')
        print(f"[STREAM-API] Estado después de detener: {state}")

        return jsonify({
            'success': True,
            'message': 'Streaming detenido correctamente',
            'task_id': result.id
        }), 200

    except Exception as e:
        print(f"[STREAM-API] ❌ Error al detener streaming: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error al detener streaming: {str(e)}'
        }), 500


@streaming_control_bp.route('/status', methods=['GET'])
@require_auth
def streaming_status():
    """
    GET /stream/status - Obtiene el estado del streaming desde el state backend.

    Verifica que la tarea de Celery realmente esté corriendo y limpia estados huérfanos.

    Returns:
        JSON: Estado del streaming (active/inactive) y detalles

    Example Response:
        {
            "success": true,
            "active": true,
            "port": 8765,
            "clients": 0,
            "task_id": "celery-task-id",
            "fps": 15,
            "quality": 75
        }
    """
    try:
        # Consultar estado desde el state backend
        state_manager = get_state_manager()
        state = state_manager.hgetall('streaming:state')

        if not state:
            return jsonify({
                'success': True,
                'active': False,
                'port': None,
                'clients': 0
            }), 200

        # Decodificar datos
        state_dict = {}
        for k, v in state.items():
            k_str = k.decode('utf-8') if isinstance(k, bytes) else k
            v_str = v.decode('utf-8') if isinstance(v, bytes) else v
            state_dict[k_str] = v_str

        is_active = state_dict.get('active') == 'true'

        # Si dice que está activo, verificar que la tarea realmente exista
        if is_active:
            task_id = state_dict.get('task_id')
            if task_id:
                try:
                    from celery.result import AsyncResult
                    task_result = AsyncResult(task_id, app=celery_app)
                    task_state = task_result.state

                    # Estados válidos: STARTED, RETRY
                    # IMPORTANTE: NO limpiar estados SUCCESS o PENDING inmediatamente
                    # porque puede ser normal durante operación
                    if task_state in ['FAILURE', 'REVOKED']:
                        # Solo limpiar si la tarea realmente falló o fue revocada
                        print(f"[STREAM-STATUS] ⚠️  Tarea falló o fue revocada ({task_state}), limpiando...")
                        state_manager.delete('streaming:state', 'streaming:stop_requested')

                        # Retornar como inactivo
                        return jsonify({
                            'success': True,
                            'active': False,
                            'port': None,
                            'clients': 0
                        }), 200
                    elif task_state == 'PENDING':
                        # Tarea PENDING: dar tiempo de gracia
                        started_at_str = state_dict.get('started_at')
                        if started_at_str:
                            started_at = float(started_at_str)
                            time_elapsed = time.time() - started_at
                            # Solo limpiar si lleva más de 5 minutos en PENDING
                            if time_elapsed > 300:
                                print(f"[STREAM-STATUS] ⚠️  Tarea PENDING > 5min, limpiando...")
                                state_manager.delete('streaming:state', 'streaming:stop_requested')
                                return jsonify({
                                    'success': True,
                                    'active': False,
                                    'port': None,
                                    'clients': 0
                                }), 200
                    elif task_state == 'SUCCESS':
                        # Tarea completada: podría ser normal si se detuvo, verificar timestamp
                        # Solo limpiar si el estado dice activo pero la tarea finalizó hace más de 10s
                        # Esto da tiempo para que la UI refresque
                        pass  # No limpiar inmediatamente
                except Exception as e:
                    print(f"[STREAM-STATUS] Error verificando tarea: {e}")
                    # En caso de error, NO limpiar automáticamente
                    # Dejar que la tarea misma se limpie si es necesario
                    pass

        port = int(state_dict.get('port', 8765)) if is_active else None
        clients_count = 0  # WebSocket clients - not tracked in SSE mode

        return jsonify({
            'success': True,
            'active': is_active,
            'port': port,
            'clients': clients_count,
            'task_id': state_dict.get('task_id'),
            'fps': int(state_dict.get('fps', 15)),
            'quality': int(state_dict.get('quality', 75))
        }), 200

    except Exception as e:
        print(f"[STREAM-STATUS] ❌ Error obteniendo estado: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
