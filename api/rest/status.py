"""
REST API - Robot Status Endpoints.

Provides status checking endpoints:
    - GET /status: Get current robot status (free, running, blocked, closed)
    - GET /execution: Get specific execution status
"""
from flask import Blueprint, jsonify, request
from api import get_server
from api.auth import require_token
from shared.state.state import get_state_manager


# Create blueprint
rest_status_bp = Blueprint('rest_status', __name__)


@rest_status_bp.route('/status', methods=['GET'])
@require_token
def get_robot_status():
    """
    GET /status - Obtiene el estado actual del robot.

    Query Parameters:
        machine_id (str): ID de la máquina (autenticación)
        license_key (str): License key (autenticación)

    Returns:
        JSON: Estado del robot
            - "free": Disponible para tareas
            - "running": Ejecutando una tarea
            - "blocked": Bloqueado manualmente
            - "closed": Credenciales inválidas o desconectado

    Status Codes:
        200: Success

    Lógica:
        1. Verifica credenciales (machine_id, license_key)
        2. Si inválidas: retorna "closed"
        3. Verifica si hay proceso corriendo:
           - Proceso activo: "running"
           - Proceso terminado: "free"
        4. Sin proceso: "free"

    Example:
        GET /status?machine_id=ABC123&license_key=XYZ789

        Response: "free"
    """
    server = get_server()
    
    # Autenticación
    machine_id = request.args.get('machine_id')
    license_key = request.args.get('license_key')

    if not server or machine_id != server.machine_id or license_key != server.license_key:
        return jsonify("closed")

    # Verificar estado del proceso
    if server.run_robot_process:
        if server.run_robot_process.poll() is not None:
            # Proceso terminado
            if server.status != "closed":
                server.status = "free"
        else:
            # Proceso corriendo
            server.status = "running"
    else:
        # Sin proceso
        if server.status != "closed":
            server.status = "free"

    return jsonify(server.status)


@rest_status_bp.route('/execution', methods=['GET'])
@require_token
def get_execution_status():
    """
    GET /execution - Obtiene el estado de una ejecución específica.

    Query Parameters:
        id (str): ID de la ejecución a consultar

    Returns:
        JSON: Estado de la ejecución
            - {"status": "working"}: Ejecución en progreso
            - {"status": "paused"}: Ejecución pausada
            - {"status": "stopped"}: Ejecución terminó exitosamente
            - {"status": "fail"}: Ejecución terminó con error o no se encontró

    Status Codes:
        200: Success

    Use Case:
        Permite al orquestador verificar si una tarea específica
        sigue ejecutándose o ha terminado.

    Example:
        GET /execution?id=exec_123456

        Response: {"status": "working"}
    """
    execution_id = request.args.get('id')

    print(f"[EXECUTION] Verificando estado de ejecución: {execution_id}")

    if not execution_id:
        print(f"[EXECUTION] ❌ No se proporcionó ID → fail")
        return jsonify({"status": "fail"})

    # Consultar estado desde Redis (reemplaza JSON file)
    state = get_state_manager().load_execution_state(execution_id)

    if not state:
        print(f"[EXECUTION] ❌ Ejecución no encontrada en Redis → fail")
        return jsonify({"status": "fail"})

    print(f"[EXECUTION] Estado en Redis: {state}")

    # Mapear estados internos de Celery/Redis a estados de la API
    status_map = {
        'pending': 'working',   # Tarea en cola, aún no iniciada
        'running': 'working',   # Tarea ejecutándose
        'paused': 'paused',     # Tarea pausada
        'completed': 'stopped', # Tarea terminó exitosamente
        'failed': 'fail'        # Tarea terminó con error
    }

    internal_status = state.get('status', 'failed')
    api_status = status_map.get(internal_status, 'fail')

    print(f"[EXECUTION] Estado API: {api_status}")

    return jsonify({"status": api_status})
