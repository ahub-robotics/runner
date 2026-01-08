"""
REST API - Server Information Endpoints.

Provides server information endpoints:
    - GET /api/server-info: Get current server status and execution details
    - GET /api/logs: Get recent server logs
"""
import traceback
from pathlib import Path
from flask import Blueprint, jsonify, request
from api.auth import require_auth
from shared.state.redis_state import redis_state


# Create blueprint
rest_info_bp = Blueprint('rest_info', __name__)


def get_server():
    """Get server instance from api module."""
    from api import get_server
    return get_server()


@rest_info_bp.route('/api/server-info', methods=['GET'])
@require_auth
def get_server_info():
    """
    GET /api/server-info - Obtiene información actualizada del servidor.

    Returns:
        JSON con estado actual del servidor y detalles de ejecución

    Example Response:
        {
            "status": "running",
            "machine_id": "robot-1",
            "license_key": "abc123",
            "url": "https://orchestrator.com",
            "ip": "192.168.1.10",
            "port": "5055",
            "has_active_process": true,
            "current_execution": {
                "execution_id": "exec_123",
                "redis_status": "running",
                "started_at": "1234567890.123",
                "task_id": "celery-task-id",
                "pid": "12345",
                "exit_code": null
            }
        }
    """
    server = get_server()

    # IMPORTANTE: Obtener estado desde Redis para tener el estado real
    # (puede haber tareas de Celery en otros workers)
    try:
        redis_server_status = redis_state.get_server_status()
        if redis_server_status and server:
            # Sincronizar estado local con Redis
            if server.status != redis_server_status:
                print(f"[API] Sincronizando estado: {server.status} -> {redis_server_status}")
                server.status = redis_server_status
            actual_status = redis_server_status
        else:
            actual_status = server.status if server else 'unknown'
    except Exception as e:
        print(f"[API] Error obteniendo estado de Redis: {e}")
        actual_status = server.status if server else 'unknown'

    # Información básica del servidor
    if server:
        info = {
            'status': actual_status,
            'machine_id': server.machine_id,
            'license_key': server.license_key,
            'url': server.url,
            'ip': server.ip,
            'port': server.port,
            'has_active_process': server.run_robot_process is not None and server.run_robot_process.poll() is None
        }
    else:
        info = {
            'status': 'unknown',
            'machine_id': 'N/A',
            'license_key': 'N/A',
            'url': 'N/A',
            'ip': 'N/A',
            'port': 'N/A',
            'has_active_process': False
        }

    # Buscar ejecución activa en Redis (puede estar en otro worker de Celery)
    try:
        # Obtener todas las ejecuciones activas desde Redis
        import redis
        client = redis_state._get_redis_client()
        execution_keys = client.keys('execution:*')

        # Buscar la ejecución que está running o paused
        active_execution = None
        for key in execution_keys:
            key_str = key.decode('utf-8') if isinstance(key, bytes) else key

            # Saltar claves de control de pausa
            if ':pause_control' in key_str:
                continue

            try:
                state = client.hgetall(key)
                if state:
                    # Convertir bytes a str
                    state_dict = {}
                    for k, v in state.items():
                        k_str = k.decode('utf-8') if isinstance(k, bytes) else k
                        v_str = v.decode('utf-8') if isinstance(v, bytes) else v
                        state_dict[k_str] = v_str

                    status = state_dict.get('status', '')

                    # Si encontramos una ejecución activa, usarla
                    if status in ['running', 'paused', 'pending']:
                        active_execution = state_dict
                        break

            except Exception as e:
                print(f"[API] Error procesando clave {key_str}: {e}")
                continue

        # Si encontramos una ejecución activa, agregarla
        if active_execution:
            info['current_execution'] = {
                'execution_id': active_execution.get('execution_id'),
                'redis_status': active_execution.get('status'),
                'started_at': active_execution.get('started_at'),
                'task_id': active_execution.get('task_id'),
                'pid': active_execution.get('pid'),
                'exit_code': active_execution.get('exit_code')
            }

            # Si está pausada, agregar timestamp de pausa
            if active_execution.get('status') == 'paused' and active_execution.get('paused_at'):
                info['current_execution']['paused_at'] = active_execution.get('paused_at')

            # Actualizar execution_id local si no coincide
            if server and server.execution_id != active_execution.get('execution_id'):
                print(f"[API] Sincronizando execution_id: {server.execution_id} -> {active_execution.get('execution_id')}")
                server.execution_id = active_execution.get('execution_id')

    except Exception as e:
        print(f"[API] Error buscando ejecuciones activas: {e}")
        traceback.print_exc()

    return jsonify(info)


@rest_info_bp.route('/api/logs', methods=['GET'])
@require_auth
def get_logs():
    """
    GET /api/logs - Obtiene las últimas líneas del log del servidor.

    Query params:
        lines (int): Número de líneas a retornar (default: 100, max: 500)

    Returns:
        JSON con las últimas líneas del log

    Example Response:
        {
            "success": true,
            "logs": [
                {
                    "message": "[2024-01-01 10:00:00] Server started",
                    "type": "info"
                },
                {
                    "message": "[2024-01-01 10:01:00] ✅ Task completed",
                    "type": "success"
                },
                {
                    "message": "[2024-01-01 10:02:00] ❌ Error occurred",
                    "type": "error"
                }
            ],
            "total": 3
        }
    """
    try:
        # Obtener número de líneas solicitadas
        lines = request.args.get('lines', default=100, type=int)
        lines = min(lines, 500)  # Máximo 500 líneas

        log_file = Path.home() / 'Robot' / 'requests.log'

        if not log_file.exists():
            return jsonify({
                'success': True,
                'logs': [],
                'message': 'No log file found'
            })

        # Leer las últimas N líneas del archivo
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            # Leer todo el archivo y obtener las últimas líneas
            all_lines = f.readlines()
            last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        # Formatear logs
        formatted_logs = []
        for line in last_lines:
            line = line.strip()
            if line:
                # Detectar tipo de log basado en contenido
                log_type = 'info'
                if 'ERROR' in line or 'Error' in line or '❌' in line:
                    log_type = 'error'
                elif 'WARNING' in line or 'Warning' in line or '⚠' in line:
                    log_type = 'warning'
                elif 'SUCCESS' in line or '✓' in line or '✅' in line:
                    log_type = 'success'

                formatted_logs.append({
                    'message': line,
                    'type': log_type
                })

        return jsonify({
            'success': True,
            'logs': formatted_logs,
            'total': len(formatted_logs)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error reading logs: {str(e)}',
            'logs': []
        }), 500
