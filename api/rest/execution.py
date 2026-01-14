"""
REST API - Robot Execution Control Endpoints.

Provides execution control endpoints:
    - POST /run: Execute a robot task
    - GET /stop: Stop running execution
    - GET /pause: Pause running execution
    - GET /resume: Resume paused execution
    - GET /block: Block robot manually
"""
import json
import time
import uuid
import traceback
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from api import get_server
from api.auth import require_token
from api.middleware import REQUEST_LOG_FILE
from shared.state.state import get_state_manager
from shared.celery_app.config import celery_app


# Create blueprint
rest_execution_bp = Blueprint('rest_execution', __name__)


def log_to_file(message):
    """Helper to log messages to the shared request log file."""
    try:
        with open(REQUEST_LOG_FILE, 'a') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass


@rest_execution_bp.route('/run', methods=['POST'])
@require_token
def run_robot():
    """
    POST /run - Ejecuta una tarea en el robot.

    Request Body (JSON):
        {
            "robot_file": "script.robot",  # Archivo robot a ejecutar
            "params": {...},  # Parámetros adicionales
            "execution_id": "exec_123"  # ID de la ejecución (opcional)
        }

    Returns:
        JSON: Resultado de la operación
            - {"message": "running", "execution_id": "..."}: Tarea iniciada correctamente
            - {"message": "<error>"}: Error al iniciar la tarea

    Status Codes:
        200: Tarea iniciada
        400: Error al iniciar tarea

    Comportamiento:
        - Ejecuta la tarea de forma asíncrona usando Celery
        - No bloquea el servidor mientras la tarea corre
        - Actualiza el estado del servidor a "running"

    Note:
        Solo se puede ejecutar una tarea a la vez. Verificar el estado
        antes con GET /status.

    Example:
        POST /run
        Content-Type: application/json

        {
            "robot_file": "mi_robot.robot",
            "params": {"env": "production"},
            "execution_id": "exec_123456"
        }

        Response: {"message": "running", "execution_id": "exec_123456"}
    """
    server = get_server()

    # Log al archivo
    log_msg = f"[ENDPOINT /run] Recibida petición POST"
    print("=" * 70)
    print(log_msg)
    print("=" * 70)
    log_to_file(log_msg)

    # Validar y parsear JSON
    try:
        data = request.json

        # Validar que sea un diccionario
        if data is None:
            log_msg = f"[ENDPOINT /run] ERROR: No JSON data provided"
            print(log_msg)
            log_to_file(log_msg)
            return current_app.response_class(
                response=json.dumps({'message': 'No JSON data provided'}),
                status=400,
                mimetype='application/json'
            )

        if not isinstance(data, dict):
            log_msg = f"[ENDPOINT /run] ERROR: Invalid JSON format - expected dict, got {type(data).__name__}: {data}"
            print(log_msg)
            log_to_file(log_msg)
            return current_app.response_class(
                response=json.dumps({'message': f'Invalid JSON format: expected dict, got {type(data).__name__}'}),
                status=400,
                mimetype='application/json'
            )

        log_msg = f"[ENDPOINT /run] Datos recibidos: {data}"
        print(log_msg)
        log_to_file(log_msg)

    except Exception as e:
        log_msg = f"[ENDPOINT /run] ERROR: Exception parsing JSON: {e}"
        print(log_msg)
        log_to_file(log_msg)
        try:
            with open(REQUEST_LOG_FILE, 'a') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] Traceback:\n")
                traceback.print_exc(file=f)
        except:
            pass
        return current_app.response_class(
            response=json.dumps({'message': f'Error parsing JSON: {str(e)}'}),
            status=400,
            mimetype='application/json'
        )

    try:
        # Generar o extraer execution_id
        # Extract execution_id from various possible formats
        execution_id = data.get('execution_id')
        if not execution_id:
            execution_value = data.get('execution')
            if isinstance(execution_value, dict):
                # execution is a dict with execution_id field
                execution_id = execution_value.get('execution_id')
            elif isinstance(execution_value, str):
                # execution is already the execution_id string
                execution_id = execution_value

        # Generate UUID if no execution_id found
        if not execution_id:
            execution_id = str(uuid.uuid4())

        # Asegurar que execution_id esté en data para la tarea de Celery
        data['execution_id'] = execution_id

        log_msg = f"[ENDPOINT /run] Execution ID: {execution_id}"
        print(log_msg)
        log_to_file(log_msg)

        # Cambiar estado a running con el execution_id
        log_msg = f"[ENDPOINT /run] Cambiando estado a 'running'"
        print(log_msg)
        log_to_file(log_msg)

        # IMPORTANTE: Establecer estado a running Y notificar al remoto
        # Esto debe hacerse ANTES de enviar la tarea a Celery
        if server:
            server.change_status("running", notify_remote=True, execution_id=execution_id)

            # Verificar que se guardó correctamente
            log_msg = f"[ENDPOINT /run] Execution ID guardado: {server.execution_id}"
            print(log_msg)
            log_to_file(log_msg)

        # Ejecutar tarea de forma asíncrona con Celery
        log_msg = f"[ENDPOINT /run] Enviando tarea a Celery"
        print(log_msg)
        log_to_file(log_msg)

        # Enviar tarea a Celery
        from executors.tasks import run_robot_task
        task = run_robot_task.delay(data)

        # Guardar estado inicial en Redis (con estado 'running', NO 'pending')
        # IMPORTANTE: No sobrescribir el estado del servidor aquí
        get_state_manager().save_execution_state(execution_id, {
            'execution_id': execution_id,
            'status': 'running',  # ← CAMBIAR de 'pending' a 'running'
            'task_id': task.id,
            'started_at': time.time()
        })

        log_msg = f"[ENDPOINT /run] Tarea enviada a Celery: task_id={task.id}"
        print(log_msg)
        log_to_file(log_msg)

        log_msg = f"[ENDPOINT /run] ✅ Retornando respuesta exitosa"
        print(log_msg)
        log_to_file(log_msg)

        return current_app.response_class(
            response=json.dumps({
                'message': "running",
                'execution_id': execution_id,
                'task_id': task.id
            }),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:
        error_msg = f"[ENDPOINT /run] ❌ Error: {e}"
        print(error_msg)
        log_to_file(error_msg)

        tb_str = traceback.format_exc()
        print(tb_str)

        # Escribir traceback al log
        try:
            with open(REQUEST_LOG_FILE, 'a') as f:
                for line in tb_str.split('\n'):
                    if line:
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        f.write(f"[{timestamp}] {line}\n")
        except:
            pass

        # Log del error
        if server:
            try:
                server.send_log(str(e))
            except Exception as log_error:
                print(f"[ENDPOINT /run] Error al enviar log: {log_error}")

            try:
                server.change_status("free", notify_remote=False)
            except Exception as status_error:
                print(f"[ENDPOINT /run] Error al cambiar estado: {status_error}")

        return current_app.response_class(
            response=json.dumps({'message': str(e)}),
            status=400,
            mimetype='application/json'
        )


@rest_execution_bp.route('/stop', methods=['GET'])
@require_token
def stop_robot():
    """
    GET /stop - Detiene la ejecución actual del robot.

    Query Parameters:
        execution_id (str): ID de la ejecución a detener

    Returns:
        JSON: Resultado de la operación
            - {"message": "OK"}: Robot detenido correctamente
            - {"message": "execution_id_mismatch"}: El execution_id no coincide
            - {"message": "<error>"}: Error al detener

    Status Codes:
        200: Operación exitosa
        400: execution_id no coincide o no proporcionado

    Comportamiento:
        - Valida que el execution_id recibido coincida con el que está corriendo
        - Si no coincide, no hace nada y retorna error
        - Si coincide, detiene el proceso del robot de forma segura
        - Si falla, establece el estado como "fail"

    Example:
        GET /stop?execution_id=abc123

        Response: {"message": "OK"}
    """
    server = get_server()

    # Obtener execution_id del query parameter
    received_execution_id = request.args.get('execution_id')

    if not received_execution_id:
        print(f"[STOP] ❌ No se proporcionó execution_id")
        return current_app.response_class(
            response=json.dumps({'message': "execution_id required"}),
            status=400,
            mimetype='application/json'
        )

    # Validar contra Redis (reemplaza JSON file)
    state = get_state_manager().get_execution_state(received_execution_id)

    if not state:
        print(f"[STOP] ❌ Ejecución no encontrada en Redis")
        return current_app.response_class(
            response=json.dumps({'message': "execution_id_mismatch"}),
            status=400,
            mimetype='application/json'
        )

    print(f"[STOP] ✅ Ejecución encontrada. Deteniendo...")
    print(f"[STOP] - Estado: {state.get('status')}")
    print(f"[STOP] - Task ID: {state.get('task_id')}")

    try:
        # Revocar tarea de Celery si existe
        task_id = state.get('task_id')
        if task_id:
            print(f"[STOP] Revocando tarea de Celery: {task_id}")
            celery_app.control.revoke(task_id, terminate=True, signal='SIGTERM')

        # Configurar execution_id en server para que stop() funcione
        if server:
            server.execution_id = received_execution_id

            # Detener subprocess (si existe en este worker)
            server.stop()

        # Actualizar estado en Redis
        get_state_manager().save_execution_state(received_execution_id, {
            'status': 'failed',
            'exit_code': -1,
            'error': 'Stopped by user',
            'finished_at': time.time()
        })

        print(f"[STOP] ✅ Ejecución detenida correctamente")
        return current_app.response_class(
            response=json.dumps({'message': "OK"}),
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        print(f"[STOP] ❌ Error al detener: {e}")
        traceback.print_exc()
        return current_app.response_class(
            response=json.dumps({'message': str(e)}),
            status=200,
            mimetype='application/json'
        )


@rest_execution_bp.route('/pause', methods=['GET'])
@require_token
def pause_robot():
    """
    GET /pause - Pausa la ejecución actual del robot.

    Query Parameters:
        execution_id (str): ID de la ejecución a pausar

    Returns:
        JSON: Resultado de la operación
            - {"message": "OK"}: Robot pausado correctamente
            - {"message": "execution_id_mismatch"}: El execution_id no coincide
            - {"message": "<error>"}: Error al pausar

    Status Codes:
        200: Operación exitosa
        400: execution_id no coincide o no proporcionado

    Comportamiento:
        - Valida que el execution_id recibido coincida con el que está corriendo
        - Si no coincide, no hace nada y retorna error
        - Si coincide, pausa el proceso del robot
        - Si falla, establece el estado como "fail"

    Note:
        La funcionalidad de pausa depende de la implementación del
        robot. No todos los robots soportan pausa.

    Example:
        GET /pause?execution_id=abc123

        Response: {"message": "OK"}
    """
    server = get_server()

    # Obtener execution_id del query parameter
    received_execution_id = request.args.get('execution_id')

    if not received_execution_id:
        print(f"[PAUSE] ❌ No se proporcionó execution_id")
        return current_app.response_class(
            response=json.dumps({'message': "execution_id required"}),
            status=400,
            mimetype='application/json'
        )

    # Validar contra Redis (reemplaza JSON file)
    state = get_state_manager().get_execution_state(received_execution_id)

    if not state or state.get('status') not in ['running', 'pending']:
        print(f"[PAUSE] ❌ Ejecución no válida para pausar")
        return current_app.response_class(
            response=json.dumps({'message': "execution_id_mismatch"}),
            status=400,
            mimetype='application/json'
        )

    print(f"[PAUSE] ✅ Ejecución válida. Pausando...")
    print(f"[PAUSE] - Estado: {state.get('status')}")

    try:
        # Configurar execution_id en server
        if server:
            server.execution_id = received_execution_id

            # Pausar (internamente usa Redis para comunicar al worker)
            server.pause()

        print(f"[PAUSE] ✅ Ejecución pausada correctamente")
        return current_app.response_class(
            response=json.dumps({'message': "OK"}),
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        print(f"[PAUSE] ❌ Error al pausar: {e}")
        traceback.print_exc()
        return current_app.response_class(
            response=json.dumps({'message': str(e)}),
            status=200,
            mimetype='application/json'
        )


@rest_execution_bp.route('/resume', methods=['GET'])
@require_token
def resume_robot():
    """
    GET /resume - Reanuda la ejecución pausada del robot.

    Query Parameters:
        execution_id (str): ID de la ejecución a reanudar

    Returns:
        JSON: Resultado de la operación
            - {"message": "OK"}: Robot reanudado correctamente
            - {"message": "execution_id_mismatch"}: El execution_id no coincide
            - {"message": "<error>"}: Error al reanudar

    Status Codes:
        200: Operación exitosa
        400: execution_id no coincide o no proporcionado

    Comportamiento:
        - Valida que el execution_id recibido coincida con el que está corriendo
        - Si no coincide, no hace nada y retorna error
        - Si coincide, reanuda el proceso del robot pausado
        - Si falla, retorna error

    Example:
        GET /resume?execution_id=abc123

        Response: {"message": "OK"}
    """
    server = get_server()

    # Obtener execution_id del query parameter
    received_execution_id = request.args.get('execution_id')

    if not received_execution_id:
        print(f"[RESUME] ❌ No se proporcionó execution_id")
        return current_app.response_class(
            response=json.dumps({'message': "execution_id required"}),
            status=400,
            mimetype='application/json'
        )

    # Validar contra Redis (reemplaza JSON file)
    state = get_state_manager().get_execution_state(received_execution_id)

    if not state or state.get('status') != 'paused':
        print(f"[RESUME] ❌ Ejecución no válida para reanudar")
        return current_app.response_class(
            response=json.dumps({'message': "execution_id_mismatch"}),
            status=400,
            mimetype='application/json'
        )

    print(f"[RESUME] ✅ Ejecución válida. Reanudando...")
    print(f"[RESUME] - Estado: {state.get('status')}")

    try:
        # Configurar execution_id en server
        if server:
            server.execution_id = received_execution_id

            # Reanudar (internamente usa Redis para comunicar al worker)
            server.resume()

        print(f"[RESUME] ✅ Ejecución reanudada correctamente")
        return current_app.response_class(
            response=json.dumps({'message': "OK"}),
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        print(f"[RESUME] ❌ Error al reanudar: {e}")
        traceback.print_exc()
        return current_app.response_class(
            response=json.dumps({'message': str(e)}),
            status=200,
            mimetype='application/json'
        )


@rest_execution_bp.route('/block', methods=['GET'])
@require_token
def set_robot_status():
    """
    GET /block - Bloquea el robot manualmente.

    Returns:
        JSON: {"message": "blocked"}

    Status Codes:
        300: Success (código personalizado)

    Use Case:
        Permite bloquear el robot para mantenimiento o por política
        del orquestador.
    """
    server = get_server()

    if server:
        server.status = "blocked"

    return current_app.response_class(
        response=json.dumps({'message': "blocked"}),
        status=300,
        mimetype='application/json'
    )
