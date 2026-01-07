#!/usr/bin/env python3
"""
================================================================================
Robot Runner - Servidor Web con GUI Integrada
================================================================================

Descripción:
    Aplicación servidor-cliente que permite ejecutar robots (scripts de
    automatización) de forma remota a través de una API REST con interfaz
    gráfica integrada usando webview.

Características principales:
    - API REST para control remoto del robot
    - Interfaz gráfica integrada con webview
    - Servidor HTTPS con certificados SSL (CA propia)
    - Autenticación basada en machine_id y license_key
    - Gestión de estado del robot (free, running, blocked, closed)
    - Ejecución asíncrona de tareas usando ThreadPoolExecutor

Arquitectura:
    - Flask: Framework web para la API
    - Gunicorn: Servidor WSGI de producción con soporte SSL
    - Webview: GUI nativa que muestra la interfaz Flask
    - Subprocess: Separación de servidor (Gunicorn) y GUI (webview)

Modos de ejecución:
    1. Modo completo (GUI + Servidor):
       $ python app.py

    2. Modo solo servidor (sin GUI):
       $ python app.py --server-only

Author: Robot Runner Team
Version: 2.0
License: Proprietary
================================================================================
"""

# ============================================================================
# IMPORTS - Bibliotecas estándar
# ============================================================================
import argparse
import json
import os
import secrets
import sys
import subprocess
import time
import warnings
import logging
import signal
import atexit
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import shared_memory
from datetime import datetime
from pathlib import Path

# ============================================================================
# IMPORTS - Bibliotecas de terceros
# ============================================================================
import flask
from flask import jsonify, request, render_template, redirect, url_for, session, flash
import gunicorn.app.base
import requests
from urllib3.exceptions import InsecureRequestWarning

# ============================================================================
# IMPORTS - Módulos locales
# ============================================================================
from .config import get_config_data, write_to_config, get_args
from .server import Server
from .emisor import ScreenStreamer
from .celery_config import celery_app
from .redis_state import redis_state
from .tasks import run_robot_task
from .streaming_tasks import start_streaming_task, stop_streaming_task, get_streaming_status
from .redis_manager import redis_manager

# ============================================================================
# CONFIGURACIÓN GLOBAL
# ============================================================================

# Suprimir warnings de SSL para peticiones internas
warnings.filterwarnings('ignore', category=InsecureRequestWarning)

# Directorio raíz del proyecto (un nivel arriba de src/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Crear aplicación Flask con rutas correctas para templates y static
app = flask.Flask(
    __name__,
    template_folder=os.path.join(PROJECT_ROOT, 'templates'),
    static_folder=os.path.join(PROJECT_ROOT, 'static')
)

# Configuración de Flask
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Límite: 16 MB
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_SECURE'] = True  # Solo HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # No accesible desde JavaScript
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Protección CSRF

# Configuración de sesiones permanentes (30 días)
from datetime import timedelta
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# ============================================================================
# CLEANUP HANDLERS - Registrar al nivel de módulo
# ============================================================================
# Estos handlers se registran al importar el módulo, asegurando que funcionen
# independientemente de cómo se inicie el servidor (Gunicorn, Flask dev, etc.)

def _cleanup_on_exit_signal(signum, frame):
    """Handler para señales de terminación."""
    # Importar aquí para evitar referencia circular
    # La función está definida más abajo en el archivo
    try:
        cleanup_celery_workers()
    except NameError:
        # Si la función aún no está definida (durante importación inicial), ignorar
        pass
    sys.exit(0)

# Registrar handlers de señales
signal.signal(signal.SIGTERM, _cleanup_on_exit_signal)
signal.signal(signal.SIGINT, _cleanup_on_exit_signal)

# Registrar con atexit para cleanup en salida normal
def _cleanup_on_exit():
    """Handler para salida normal del programa."""
    try:
        cleanup_celery_workers()
    except NameError:
        # Si la función aún no está definida (durante importación inicial), ignorar
        pass

atexit.register(_cleanup_on_exit)

print("[INIT] ✅ Cleanup handlers registrados globalmente (SIGTERM, SIGINT, atexit)")

# NOTA: ThreadPoolExecutor reemplazado por Celery + Redis
# La ejecución asíncrona de robots ahora se maneja con Celery workers
# executor = ThreadPoolExecutor(max_workers=4)  # <- OBSOLETO

# Variable global para el servidor (se inicializa al importar o en main)
server = None

# NOTA: screen_streamer ya no es necesario - ahora se gestiona via Celery tasks
# La gestión de streaming se hace a través de Redis state y tareas de Celery

# Archivo de socket temporal (para verificar instancia única)
SOCKET_FILE = "/tmp/myapp_socket"

# Función para inicializar el servidor si no está inicializado
def init_server_if_needed():
    """
    Inicializa el servidor si aún no ha sido inicializado.
    Esta función se llama antes de cada petición para asegurar que
    el servidor esté disponible incluso cuando Flask se ejecuta como WSGI.

    También configura Redis, recupera ejecuciones huérfanas y establece estado a "free".
    """
    global server
    if server is None:
        from .config import get_config_data
        config = get_config_data()
        server = Server(config)

        # Configurar Redis state manager con machine_id
        redis_state.set_machine_id(config['machine_id'])

        # Recuperar ejecuciones huérfanas (running/paused) y marcarlas como fallidas
        # Esto es importante para recuperarse de crashes o reinicios del servidor
        redis_state.mark_orphaned_executions_as_failed()

        # Establecer estado inicial a "free" y notificar al orquestador
        print("[INIT] Estableciendo estado inicial a 'free'")
        server.change_status("free", notify_remote=True)

# Archivo de log para peticiones HTTP (compartido entre servidor y GUI)
REQUEST_LOG_FILE = Path.home() / 'Robot' / 'requests.log'

# ============================================================================
# LOGGING DE PETICIONES HTTP
# ============================================================================

def log_request_to_file(method, path, remote_addr, status_code):
    """
    Registra una petición HTTP en el archivo de log compartido.

    Args:
        method (str): Método HTTP (GET, POST, etc.)
        path (str): Ruta de la petición
        remote_addr (str): IP del cliente
        status_code (int): Código de estado HTTP de la respuesta
    """
    try:
        # Crear directorio si no existe
        REQUEST_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Formatear el log
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {method} {path} - {remote_addr} - Status: {status_code}\n"

        # Escribir al archivo (append mode)
        with open(REQUEST_LOG_FILE, 'a') as f:
            f.write(log_entry)
    except Exception as e:
        # Si falla el logging, no queremos interrumpir el servidor
        print(f"Error al escribir log de petición: {e}")


@app.before_request
def before_request_logging():
    """
    Middleware que se ejecuta antes de cada petición.
    Inicializa el servidor si no está inicializado, guarda el tiempo de inicio
    y verifica si hay un token en los query parameters para autenticación automática.
    """
    # Inicializar el servidor si aún no ha sido inicializado
    init_server_if_needed()

    # Guardar tiempo de inicio
    request.start_time = time.time()

    # AUTENTICACIÓN AUTOMÁTICA: Verificar si viene token en query parameter
    # Esto permite autenticar desde cualquier URL: /?token=xxx, /connected?token=xxx, etc.
    if 'authenticated' not in session or not session.get('authenticated'):
        token_from_url = request.args.get('token')
        if token_from_url:
            # Validar token
            if token_from_url == server.token:
                # Token válido - crear sesión permanente (30 días)
                session['authenticated'] = True
                session['login_time'] = time.time()
                session.permanent = True  # Hacer sesión permanente por 30 días
                print(f"[AUTH] ✅ Autenticación automática desde URL: {request.path}")
                # No redirigir, continuar con la petición normalmente


@app.after_request
def after_request_logging(response):
    """
    Middleware que se ejecuta después de cada petición.
    Registra la petición en el archivo de log compartido.
    """
    try:
        # Registrar la petición
        log_request_to_file(
            method=request.method,
            path=request.path,
            remote_addr=request.remote_addr or 'unknown',
            status_code=response.status_code
        )
    except Exception as e:
        # Si falla el logging, no queremos interrumpir el servidor
        print(f"Error en after_request_logging: {e}")

    return response


# ============================================================================
# UTILIDADES - Funciones auxiliares
# ============================================================================

def get_resource_path(relative_path):
    """
    Obtiene la ruta absoluta de un recurso, compatible con PyInstaller.

    PyInstaller empaqueta los recursos en un directorio temporal (_MEIPASS)
    cuando la aplicación se ejecuta como ejecutable. Esta función maneja
    ambos casos: desarrollo y ejecutable empaquetado.

    Args:
        relative_path (str): Ruta relativa del recurso (ej: 'cert.pem')

    Returns:
        str: Ruta absoluta del recurso

    Ejemplo:
        >>> get_resource_path('cert.pem')
        '/path/to/app/cert.pem'  # En desarrollo
        '/tmp/_MEIxxx/cert.pem'  # En ejecutable
    """
    if hasattr(sys, '_MEIPASS'):
        # Ejecutable empaquetado con PyInstaller
        return os.path.join(sys._MEIPASS, relative_path)
    # Modo desarrollo
    return os.path.join(os.path.abspath("."), relative_path)


def check_already_running():
    """
    Verifica si ya hay una instancia de la aplicación ejecutándose.

    Utiliza memoria compartida (shared_memory) para detectar instancias
    duplicadas. Si ya existe una instancia, termina la nueva.

    Returns:
        SharedMemory: Objeto de memoria compartida que sirve como lock

    Raises:
        SystemExit: Si ya existe una instancia corriendo

    Note:
        En producción, considere usar un sistema de locks más robusto
        como flock o un archivo PID.
    """
    try:
        shm = shared_memory.SharedMemory(name='my_app_lock', create=True, size=1)
        return shm
    except FileExistsError:
        print("⚠️  La aplicación ya está en ejecución.")
        print("   Si esto es un error, elimina el lock manualmente:")
        print("   $ python -c \"from multiprocessing import shared_memory; "
              "shared_memory.SharedMemory(name='my_app_lock').unlink()\"")
        sys.exit(0)


def wait_for_server(url, timeout=30):
    """
    Espera a que el servidor esté listo para aceptar conexiones.

    Realiza peticiones periódicas al servidor hasta que responda o se
    agote el timeout.

    Args:
        url (str): URL del servidor a verificar
        timeout (int): Tiempo máximo de espera en segundos

    Returns:
        bool: True si el servidor responde, False si se agota el timeout

    Note:
        Usa verify=False porque verifica conexión SSL local con certificado
        autofirmado. En producción entre servidores, usar verify=True.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            requests.get(url, verify=False, timeout=1)
            return True
        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException):
            time.sleep(0.5)
    return False


# ============================================================================
# GUNICORN - Configuración del servidor WSGI
# ============================================================================

class StandaloneApplication(gunicorn.app.base.BaseApplication):
    """
    Aplicación standalone de Gunicorn.

    Permite ejecutar Gunicorn programáticamente (sin línea de comandos)
    con configuración personalizada. Implementa la interfaz requerida
    por gunicorn.app.base.BaseApplication.

    Attributes:
        options (dict): Opciones de configuración de Gunicorn
        application: Aplicación WSGI (Flask app)

    Example:
        >>> options = {'bind': '0.0.0.0:8000', 'workers': 4}
        >>> StandaloneApplication(app, options).run()
    """

    def __init__(self, app, options=None):
        """
        Inicializa la aplicación Gunicorn.

        Args:
            app: Aplicación WSGI (Flask app)
            options (dict, optional): Configuración de Gunicorn
        """
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        """
        Carga la configuración en Gunicorn.

        Itera sobre las opciones proporcionadas y las aplica a la
        configuración de Gunicorn si son válidas.
        """
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)

    def load(self):
        """
        Retorna la aplicación WSGI a ejecutar.

        Returns:
            La aplicación WSGI (Flask app)
        """
        return self.application


def start_gunicorn_server():
    """
    Inicia el servidor Gunicorn con SSL.

    Configuración:
        - 4 workers (procesos)
        - 2 threads por worker
        - SSL habilitado con certificados CA propios
        - Bind en todas las interfaces (0.0.0.0)
        - Hooks de Celery para iniciar workers embebidos

    Note:
        Esta función debe ejecutarse en el hilo principal debido a
        limitaciones de Gunicorn con signals en hilos secundarios.

    SSL:
        Los certificados (cert.pem, key.pem) son generados por el
        sistema de CA propio. Ver documentación en CA-README.md.
    """
    # Registrar función de limpieza para matar procesos de Celery al detener el servidor
    atexit.register(cleanup_celery_workers)

    # Registrar handlers de señales para cleanup
    signal.signal(signal.SIGTERM, lambda signum, frame: (cleanup_celery_workers(), sys.exit(0)))
    signal.signal(signal.SIGINT, lambda signum, frame: (cleanup_celery_workers(), sys.exit(0)))

    print("[INIT] ✅ Cleanup handlers registrados (SIGTERM, SIGINT, atexit)")

    # Definir hooks de Celery
    def _post_worker_init(worker):
        """Hook para iniciar Celery worker thread en cada worker de Gunicorn."""
        from .celery_worker import start_celery_worker_thread
        print(f"[GUNICORN] Worker {worker.pid} iniciado, arrancando Celery worker thread")
        start_celery_worker_thread()

    def _worker_exit(server_instance, worker):
        """Hook para detener Celery worker thread cuando worker termina."""
        from .celery_worker import stop_celery_worker_thread
        print(f"[GUNICORN] Worker {worker.pid} terminando, deteniendo Celery worker thread")
        stop_celery_worker_thread()

    options = {
        'bind': f'0.0.0.0:{server.port}',
        'workers': 1,  # 1 worker para evitar fork issues con CoreFoundation en macOS
        'threads': 4,  # Más threads por compensar menos workers
        'certfile': get_resource_path('ssl/cert.pem'),  # Certificado SSL
        'keyfile': get_resource_path('ssl/key.pem'),    # Clave privada SSL
        'worker_class': 'gthread',  # Tipo de worker (threads)
        'timeout': 120,  # Timeout de requests
        'loglevel': 'error',  # Solo mostrar errores, no warnings
        'preload_app': True,  # Precargar la app antes del fork para evitar issues con CoreFoundation
        # IMPORTANTE: Hooks de Celery para iniciar/detener workers embebidos
        'post_worker_init': _post_worker_init,
        'worker_exit': _worker_exit,
    }
    StandaloneApplication(app, options).run()


# ============================================================================
# MIDDLEWARE DE AUTENTICACIÓN
# ============================================================================

from functools import wraps

def require_token(f):
    """
    Decorador que verifica el token de autenticación en las peticiones.

    El token DEBE venir en el header Authorization:
    - Header: Authorization: Bearer <token>
    - O alternativamente: Authorization: <token>

    Returns:
        401: Si el token no está presente en el header
        403: Si el token es inválido
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Obtener el token del header Authorization
        auth_header = request.headers.get('Authorization')

        # Verificar si se proporcionó un token
        if not auth_header:
            return jsonify({
                'error': 'Token de autenticación requerido',
                'message': 'Debe proporcionar un token en el header Authorization'
            }), 401

        # Extraer el token (soporta "Bearer <token>" o solo "<token>")
        token = auth_header
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Remover "Bearer "

        # Verificar que el token sea válido
        if token != server.token:
            return jsonify({
                'error': 'Token inválido',
                'message': 'El token proporcionado no es válido'
            }), 403

        # Token válido, continuar con la petición
        return f(*args, **kwargs)

    return decorated_function


def require_auth(f):
    """
    Decorador híbrido que verifica autenticación para API y Web.

    Para API:
        - Token en header Authorization: Bearer <token>

    Para Web (Navegador):
        - Sesión activa con token validado

    Returns:
        - Redirect a /login: Si accede desde navegador sin sesión
        - 401/403: Si es petición API sin token válido
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar si ya está autenticado por sesión (navegador web)
        if 'authenticated' in session and session['authenticated']:
            return f(*args, **kwargs)

        # Verificar si hay token en el header Authorization (API)
        auth_header = request.headers.get('Authorization')
        if auth_header:
            # Extraer el token (soporta "Bearer <token>" o solo "<token>")
            token = auth_header
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]  # Remover "Bearer "

            if token == server.token:
                # Token válido, continuar
                return f(*args, **kwargs)
            else:
                return jsonify({
                    'error': 'Token inválido',
                    'message': 'El token proporcionado no es válido'
                }), 403

        # Si no es JSON y no tiene sesión, redirigir a login
        return redirect(url_for('login'))

    return decorated_function


# ============================================================================
# API ENDPOINTS - Control del Robot
# ============================================================================

@app.route('/status', methods=['GET'])
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
    # Autenticación
    machine_id = request.args.get('machine_id')
    license_key = request.args.get('license_key')

    if machine_id != server.machine_id or license_key != server.license_key:
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


@app.route('/execution', methods=['GET'])
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
    state = redis_state.load_execution_state(execution_id)

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


@app.route('/run', methods=['POST'])
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
        - Ejecuta la tarea de forma asíncrona usando ThreadPoolExecutor
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
    # Log al archivo
    log_msg = f"[ENDPOINT /run] Recibida petición POST"
    print("=" * 70)
    print(log_msg)
    print("=" * 70)

    # Escribir al archivo de log
    try:
        with open(REQUEST_LOG_FILE, 'a') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] {log_msg}\n")
    except:
        pass

    # Validar y parsear JSON
    try:
        data = request.json

        # Validar que sea un diccionario
        if data is None:
            log_msg = f"[ENDPOINT /run] ERROR: No JSON data provided"
            print(log_msg)
            try:
                with open(REQUEST_LOG_FILE, 'a') as f:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    f.write(f"[{timestamp}] {log_msg}\n")
            except:
                pass
            return app.response_class(
                response=json.dumps({'message': 'No JSON data provided'}),
                status=400,
                mimetype='application/json'
            )

        if not isinstance(data, dict):
            log_msg = f"[ENDPOINT /run] ERROR: Invalid JSON format - expected dict, got {type(data).__name__}: {data}"
            print(log_msg)
            try:
                with open(REQUEST_LOG_FILE, 'a') as f:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    f.write(f"[{timestamp}] {log_msg}\n")
            except:
                pass
            return app.response_class(
                response=json.dumps({'message': f'Invalid JSON format: expected dict, got {type(data).__name__}'}),
                status=400,
                mimetype='application/json'
            )

        log_msg = f"[ENDPOINT /run] Datos recibidos: {data}"
        print(log_msg)

        try:
            with open(REQUEST_LOG_FILE, 'a') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {log_msg}\n")
        except:
            pass

    except Exception as e:
        log_msg = f"[ENDPOINT /run] ERROR: Exception parsing JSON: {e}"
        print(log_msg)
        try:
            with open(REQUEST_LOG_FILE, 'a') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {log_msg}\n")
                import traceback
                f.write(f"[{timestamp}] Traceback:\n")
                traceback.print_exc(file=f)
        except:
            pass
        return app.response_class(
            response=json.dumps({'message': f'Error parsing JSON: {str(e)}'}),
            status=400,
            mimetype='application/json'
        )

    try:
        # Generar o extraer execution_id
        import uuid

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

        try:
            with open(REQUEST_LOG_FILE, 'a') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {log_msg}\n")
        except:
            pass

        # Cambiar estado a running con el execution_id
        log_msg = f"[ENDPOINT /run] Cambiando estado a 'running'"
        print(log_msg)

        try:
            with open(REQUEST_LOG_FILE, 'a') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {log_msg}\n")
        except:
            pass

        # IMPORTANTE: Establecer estado a running Y notificar al remoto
        # Esto debe hacerse ANTES de enviar la tarea a Celery
        server.change_status("running", notify_remote=True, execution_id=execution_id)

        # Verificar que se guardó correctamente
        log_msg = f"[ENDPOINT /run] Execution ID guardado: {server.execution_id}"
        print(log_msg)

        try:
            with open(REQUEST_LOG_FILE, 'a') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {log_msg}\n")
        except:
            pass

        # Ejecutar tarea de forma asíncrona con Celery
        log_msg = f"[ENDPOINT /run] Enviando tarea a Celery"
        print(log_msg)

        try:
            with open(REQUEST_LOG_FILE, 'a') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {log_msg}\n")
        except:
            pass

        # Enviar tarea a Celery (reemplaza executor.submit)
        task = run_robot_task.delay(data)

        # Guardar estado inicial en Redis (con estado 'running', NO 'pending')
        # IMPORTANTE: No sobrescribir el estado del servidor aquí
        redis_state.save_execution_state(execution_id, {
            'execution_id': execution_id,
            'status': 'running',  # ← CAMBIAR de 'pending' a 'running'
            'task_id': task.id,
            'started_at': time.time()
        })

        log_msg = f"[ENDPOINT /run] Tarea enviada a Celery: task_id={task.id}"
        print(log_msg)

        try:
            with open(REQUEST_LOG_FILE, 'a') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {log_msg}\n")
        except:
            pass

        log_msg = f"[ENDPOINT /run] ✅ Retornando respuesta exitosa"
        print(log_msg)

        try:
            with open(REQUEST_LOG_FILE, 'a') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {log_msg}\n")
        except:
            pass

        return app.response_class(
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

        # Escribir error al log
        try:
            with open(REQUEST_LOG_FILE, 'a') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {error_msg}\n")
        except:
            pass

        import traceback
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
        try:
            server.send_log(str(e))
        except Exception as log_error:
            print(f"[ENDPOINT /run] Error al enviar log: {log_error}")

        try:
            server.change_status("free", notify_remote=False)
        except Exception as status_error:
            print(f"[ENDPOINT /run] Error al cambiar estado: {status_error}")

        return app.response_class(
            response=json.dumps({'message': str(e)}),
            status=400,
            mimetype='application/json'
        )


@app.route('/stop', methods=['GET'])
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
    # Obtener execution_id del query parameter
    received_execution_id = request.args.get('execution_id')

    if not received_execution_id:
        print(f"[STOP] ❌ No se proporcionó execution_id")
        return app.response_class(
            response=json.dumps({'message': "execution_id required"}),
            status=400,
            mimetype='application/json'
        )

    # Validar contra Redis (reemplaza JSON file)
    state = redis_state.load_execution_state(received_execution_id)

    if not state:
        print(f"[STOP] ❌ Ejecución no encontrada en Redis")
        return app.response_class(
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
        server.execution_id = received_execution_id

        # Detener subprocess (si existe en este worker)
        server.stop()

        # Actualizar estado en Redis
        redis_state.save_execution_state(received_execution_id, {
            'status': 'failed',
            'exit_code': -1,
            'error': 'Stopped by user',
            'finished_at': time.time()
        })

        print(f"[STOP] ✅ Ejecución detenida correctamente")
        return app.response_class(
            response=json.dumps({'message': "OK"}),
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        print(f"[STOP] ❌ Error al detener: {e}")
        import traceback
        traceback.print_exc()
        return app.response_class(
            response=json.dumps({'message': str(e)}),
            status=200,
            mimetype='application/json'
        )


@app.route('/pause', methods=['GET'])
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
    # Obtener execution_id del query parameter
    received_execution_id = request.args.get('execution_id')

    if not received_execution_id:
        print(f"[PAUSE] ❌ No se proporcionó execution_id")
        return app.response_class(
            response=json.dumps({'message': "execution_id required"}),
            status=400,
            mimetype='application/json'
        )

    # Validar contra Redis (reemplaza JSON file)
    state = redis_state.load_execution_state(received_execution_id)

    if not state or state.get('status') not in ['running', 'pending']:
        print(f"[PAUSE] ❌ Ejecución no válida para pausar")
        return app.response_class(
            response=json.dumps({'message': "execution_id_mismatch"}),
            status=400,
            mimetype='application/json'
        )

    print(f"[PAUSE] ✅ Ejecución válida. Pausando...")
    print(f"[PAUSE] - Estado: {state.get('status')}")

    try:
        # Configurar execution_id en server
        server.execution_id = received_execution_id

        # Pausar (internamente usa Redis para comunicar al worker)
        server.pause()

        print(f"[PAUSE] ✅ Ejecución pausada correctamente")
        return app.response_class(
            response=json.dumps({'message': "OK"}),
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        print(f"[PAUSE] ❌ Error al pausar: {e}")
        import traceback
        traceback.print_exc()
        return app.response_class(
            response=json.dumps({'message': str(e)}),
            status=200,
            mimetype='application/json'
        )


@app.route('/resume', methods=['GET'])
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
    # Obtener execution_id del query parameter
    received_execution_id = request.args.get('execution_id')

    if not received_execution_id:
        print(f"[RESUME] ❌ No se proporcionó execution_id")
        return app.response_class(
            response=json.dumps({'message': "execution_id required"}),
            status=400,
            mimetype='application/json'
        )

    # Validar contra Redis (reemplaza JSON file)
    state = redis_state.load_execution_state(received_execution_id)

    if not state or state.get('status') != 'paused':
        print(f"[RESUME] ❌ Ejecución no válida para reanudar")
        return app.response_class(
            response=json.dumps({'message': "execution_id_mismatch"}),
            status=400,
            mimetype='application/json'
        )

    print(f"[RESUME] ✅ Ejecución válida. Reanudando...")
    print(f"[RESUME] - Estado: {state.get('status')}")

    try:
        # Configurar execution_id en server
        server.execution_id = received_execution_id

        # Reanudar (internamente usa Redis para comunicar al worker)
        server.resume()

        print(f"[RESUME] ✅ Ejecución reanudada correctamente")
        return app.response_class(
            response=json.dumps({'message': "OK"}),
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        print(f"[RESUME] ❌ Error al reanudar: {e}")
        import traceback
        traceback.print_exc()
        return app.response_class(
            response=json.dumps({'message': str(e)}),
            status=200,
            mimetype='application/json'
        )


@app.route('/block', methods=['GET'])
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
    server.status = "blocked"
    return app.response_class(
        response=json.dumps({'message': "blocked"}),
        status=300,
        mimetype='application/json'
    )


# ============================================================================
# UI ENDPOINTS - Interfaz gráfica
# ============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    GET/POST /login - Página de autenticación.

    GET:
        - Si viene token en query parameter (?token=xxx), valida y autentica automáticamente
        - Si ya está autenticado, redirige a home
        - Si no, muestra formulario de login

    POST:
        Valida el token del formulario y crea una sesión.

    Query Parameters (GET):
        - token: Token de autenticación para login automático

    Form Fields (POST):
        - token: Token de autenticación

    Returns:
        GET: Renderiza login.html o redirect a / si autenticación exitosa
        POST: Redirect a / si exitoso, o muestra error si falla

    Examples:
        https://robot1.automatehub.es/login?token=eff7df3018dc2b2271165865c0f78aa17ce5df27
        -> Autentica automáticamente y redirige a /
    """
    if request.method == 'GET':
        # NUEVO: Verificar si viene token en query parameter para login automático
        token_from_url = request.args.get('token')
        if token_from_url:
            # Validar token
            if token_from_url == server.token:
                # Token válido - crear sesión permanente (30 días)
                session['authenticated'] = True
                session['login_time'] = time.time()
                session.permanent = True  # Hacer sesión permanente por 30 días
                print(f"[LOGIN] ✅ Autenticación exitosa via URL (sesión permanente)")
                return redirect(url_for('home'))
            else:
                # Token inválido desde URL
                print(f"[LOGIN] ❌ Token inválido desde URL")
                return render_template('login.html',
                    error='Token inválido en el enlace. Por favor, verifica el token.')

        # Si ya está autenticado, redirigir a home
        if 'authenticated' in session and session['authenticated']:
            return redirect(url_for('home'))

        # Mostrar formulario de login
        return render_template('login.html', error=None)

    elif request.method == 'POST':
        token = request.form.get('token')

        # Validar token
        if token and token == server.token:
            # Crear sesión permanente (30 días)
            session['authenticated'] = True
            session['login_time'] = time.time()
            session.permanent = True  # Hacer sesión permanente por 30 días
            print(f"[LOGIN] ✅ Autenticación exitosa via formulario (sesión permanente)")
            return redirect(url_for('home'))
        else:
            # Token inválido
            return render_template('login.html',
                error='Token inválido. Por favor, verifica el token en config.json.')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    """
    GET/POST /logout - Cerrar sesión.

    Limpia la sesión del usuario y redirige al login.

    Returns:
        Redirect a /login
    """
    session.clear()
    return redirect(url_for('login'))


@app.route('/', methods=['GET'])
@require_auth
def home():
    """
    GET / - Página de inicio.

    Requiere autenticación por token.

    Redirige a:
        - /connected: Si el servidor está configurado
        - /connect: Si necesita configuración inicial

    Returns:
        Redirect
    """
    try:
        server.status = 'free'
        return redirect(url_for('connected'))
    except Exception:
        return redirect(url_for('connect'))


@app.route('/connect', methods=['GET', 'POST'])
@require_auth
def connect():
    """
    /connect - Página de configuración inicial.

    Requiere autenticación por token.

    GET:
        Muestra formulario de configuración con los valores actuales
        del config.json.

    POST:
        Guarda la configuración proporcionada y redirige a /connected.

    Form Fields:
        - ip: IP pública del robot
        - port: Puerto del servidor
        - token: Token de autenticación del orquestador
        - machine_id: ID único de la máquina
        - license_key: License key de la máquina
        - url: URL del orquestador/consola

    Returns:
        GET: Renderiza form.html
        POST: Redirect a /home
    """
    if request.method == "GET":
        config_data = get_config_data()
        message = "Set machine credentials from the Robot Console."

        return render_template(
            'form.html',
            ip=config_data.get("ip", os.popen('curl -s ifconfig.me').readline()),
            port=config_data["port"],
            token=config_data["token"],
            machine_id=config_data["machine_id"],
            license_key=config_data["license_key"],
            url=config_data["url"],
            message=message,
            color="white"
        )

    elif request.method == "POST":
        data = request.form

        # Actualizar configuración del servidor
        server.url = server.clean_url(data['url'])
        server.token = data['token']
        server.machine_id = data['machine_id']
        server.license_key = data['license_key']

        try:
            # Establecer estado como 'free' y notificar al servidor remoto
            server.change_status('free', notify_remote=True)

            # Guardar configuración
            write_to_config(data)

            return redirect(url_for("home"))

        except Exception:
            config_data = get_config_data()
            message = "Invalid credentials, check them in the console and try again."

            return render_template(
                'form.html',
                ip=config_data["ip"],
                port=config_data["port"],
                token=config_data["token"],
                machine_id=config_data["machine_id"],
                license_key=config_data["license_key"],
                url=config_data["url"],
                message=message,
                color="red"
            )


@app.route('/connected', methods=['GET', 'POST'])
@require_auth
def connected():
    """
    /connected - Página principal cuando el robot está conectado.

    Requiere autenticación por token.

    GET:
        Muestra el dashboard del robot con su estado actual.

    POST:
        Desconecta el robot y redirige a /connect.

    Returns:
        GET: Renderiza connected.html
        POST: Redirect a /connect
    """
    if request.method == 'GET':
        # Pasar datos del servidor al template
        server_data = {
            'status': server.status,
            'machine_id': server.machine_id,
            'license_key': server.license_key,
            'token': server.token,
            'url': server.url,
            'ip': server.ip,
            'port': server.port
        }
        return render_template('connected.html', server=server_data)

    elif request.method == "POST":
        server.stop_execution()
        server.change_status('closed', notify_remote=True)
        return redirect(url_for("connect"))


@app.route('/api/server-info', methods=['GET'])
@require_auth
def get_server_info():
    """
    GET /api/server-info - Obtiene información actualizada del servidor.

    Returns:
        JSON con estado actual del servidor y detalles de ejecución
    """
    # IMPORTANTE: Obtener estado desde Redis para tener el estado real
    # (puede haber tareas de Celery en otros workers)
    try:
        redis_server_status = redis_state.get_server_status()
        if redis_server_status:
            # Sincronizar estado local con Redis
            if server.status != redis_server_status:
                print(f"[API] Sincronizando estado: {server.status} -> {redis_server_status}")
                server.status = redis_server_status
            actual_status = redis_server_status
        else:
            actual_status = server.status
    except Exception as e:
        print(f"[API] Error obteniendo estado de Redis: {e}")
        actual_status = server.status

    # Información básica del servidor
    info = {
        'status': actual_status,
        'machine_id': server.machine_id,
        'license_key': server.license_key,
        'url': server.url,
        'ip': server.ip,
        'port': server.port,
        'has_active_process': server.run_robot_process is not None and server.run_robot_process.poll() is None
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
            if server.execution_id != active_execution.get('execution_id'):
                print(f"[API] Sincronizando execution_id: {server.execution_id} -> {active_execution.get('execution_id')}")
                server.execution_id = active_execution.get('execution_id')

    except Exception as e:
        print(f"[API] Error buscando ejecuciones activas: {e}")
        import traceback
        traceback.print_exc()

    return jsonify(info)


@app.route('/api/logs', methods=['GET'])
@require_auth
def get_logs():
    """
    GET /api/logs - Obtiene las últimas líneas del log del servidor.

    Query params:
        lines (int): Número de líneas a retornar (default: 100, max: 500)

    Returns:
        JSON con las últimas líneas del log
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


# ============================================================================
# TUNNEL MANAGEMENT - Gestión de túneles Cloudflare
# ============================================================================

@app.route('/tunnel/start', methods=['POST'])
@require_auth
def start_tunnel():
    """
    POST /tunnel/start - Inicia el túnel de Cloudflare en background.

    Returns:
        JSON: Estado de la operación
    """
    import shutil
    from pathlib import Path

    try:
        # Verificar si cloudflared está instalado
        if not shutil.which('cloudflared'):
            return jsonify({
                'success': False,
                'message': 'cloudflared no está instalado. Instalar con: brew install cloudflared'
            }), 400

        # Verificar configuración
        cloudflare_config = Path.home() / '.cloudflared' / 'config.yml'
        if not cloudflare_config.exists():
            return jsonify({
                'success': False,
                'message': 'Configuración de túnel no encontrada. Ejecutar setup_machine_tunnel.py primero.'
            }), 400

        # Verificar si ya está corriendo
        result = subprocess.run(
            ['pgrep', '-f', 'cloudflared tunnel run'],
            capture_output=True,
            text=True
        )

        if result.stdout.strip():
            return jsonify({
                'success': False,
                'message': 'El túnel ya está activo'
            }), 400

        # Obtener configuración y determinar subdominio
        from .config import get_config_data
        config = get_config_data()

        # Usar tunnel_subdomain si está configurado, si no usar machine_id
        subdomain_base = config.get('tunnel_subdomain', '').strip()
        if not subdomain_base:
            subdomain_base = config.get('machine_id', '').strip()

        subdomain = f"{subdomain_base.lower()}.automatehub.es" if subdomain_base else 'N/A'

        # Iniciar túnel en background
        subprocess.Popen(
            ['cloudflared', 'tunnel', 'run', 'robotrunner'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        # Esperar un momento para verificar que se inició
        time.sleep(2)

        # Verificar que se inició correctamente
        result = subprocess.run(
            ['pgrep', '-f', 'cloudflared tunnel run'],
            capture_output=True,
            text=True
        )

        if result.stdout.strip():
            return jsonify({
                'success': True,
                'message': f'Túnel iniciado correctamente',
                'subdomain': subdomain,
                'url': f'https://{subdomain}'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Error al iniciar el túnel'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@app.route('/tunnel/stop', methods=['POST'])
@require_auth
def stop_tunnel():
    """
    POST /tunnel/stop - Detiene el túnel de Cloudflare.

    Returns:
        JSON: Estado de la operación
    """
    try:
        # Buscar procesos de cloudflared
        result = subprocess.run(
            ['pgrep', '-f', 'cloudflared tunnel run'],
            capture_output=True,
            text=True
        )

        if not result.stdout.strip():
            return jsonify({
                'success': False,
                'message': 'No hay túneles activos'
            }), 400

        # Obtener los PIDs
        pids = result.stdout.strip().split('\n')

        # Matar cada proceso
        for pid in pids:
            if pid:
                subprocess.run(['kill', pid], check=True)

        return jsonify({
            'success': True,
            'message': 'Túnel detenido correctamente'
        }), 200

    except subprocess.CalledProcessError as e:
        return jsonify({
            'success': False,
            'message': f'Error al detener el túnel: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@app.route('/tunnel/status', methods=['GET'])
@require_auth
def tunnel_status():
    """
    GET /tunnel/status - Obtiene el estado del túnel de Cloudflare.

    Returns:
        JSON: Estado del túnel (active/inactive) y detalles
    """
    try:
        # Verificar si cloudflared está corriendo
        result = subprocess.run(
            ['pgrep', '-f', 'cloudflared tunnel run'],
            capture_output=True,
            text=True
        )

        is_active = bool(result.stdout.strip())

        # Obtener configuración y determinar subdominio
        from .config import get_config_data
        config = get_config_data()

        # Usar tunnel_subdomain si está configurado, si no usar machine_id
        subdomain_base = config.get('tunnel_subdomain', '').strip()
        if not subdomain_base:
            subdomain_base = config.get('machine_id', '').strip()

        subdomain = f"{subdomain_base.lower()}.automatehub.es" if subdomain_base else 'N/A'

        response_data = {
            'success': True,
            'active': is_active,
            'subdomain': subdomain,
            'url': f'https://{subdomain}' if is_active else None,
            'machine_id': config.get('machine_id', '')
        }

        if is_active:
            # Obtener PIDs
            pids = result.stdout.strip().split('\n')
            response_data['pids'] = pids

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


# ============================================================================
# SERVER MANAGEMENT - Gestión del servidor
# ============================================================================

@app.route('/server/restart', methods=['POST'])
@require_auth
def restart_server():
    """
    POST /server/restart - Reinicia el servidor Flask/Gunicorn.

    Este endpoint programa el reinicio del servidor después de enviar la respuesta.
    Nota: Solo funciona cuando se ejecuta con Gunicorn.

    Returns:
        JSON: Confirmación del reinicio programado
    """
    try:
        import signal

        def trigger_restart():
            """Función que se ejecutará después de enviar la respuesta."""
            time.sleep(1)  # Esperar a que se envíe la respuesta
            # Enviar señal HUP a Gunicorn para reiniciar los workers
            os.kill(os.getpid(), signal.SIGHUP)

        # Programar el reinicio en background (usando threading ya que es una tarea simple)
        import threading
        threading.Thread(target=trigger_restart, daemon=True).start()

        return jsonify({
            'success': True,
            'message': 'Servidor reiniciándose...'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al reiniciar: {str(e)}'
        }), 500


# ============================================================================
# SCREEN STREAMING - Gestión de streaming de pantalla
# ============================================================================

@app.route('/stream/start', methods=['POST'])
@require_auth
def start_streaming():
    """
    POST /stream/start - Inicia el streaming de pantalla via Celery task.

    Returns:
        JSON: Estado de la operación
    """
    print("[STREAM-API] POST /stream/start recibido")

    try:
        # Verificar si ya está activo consultando Redis
        redis_client = redis_state._get_redis_client()
        state = redis_client.hgetall('streaming:state')

        print(f"[STREAM-API] Estado actual en Redis: {state}")

        if state and state.get(b'active') == b'true':
            # Verificar si la tarea realmente existe en Celery
            task_id = state.get(b'task_id', b'').decode('utf-8')
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
                else:
                    print(f"[STREAM-API] ⚠️  Estado huérfano detectado (tarea {task_state}), limpiando...")
                    redis_client.delete('streaming:state')
                    redis_client.delete('streaming:stop_requested')
                    print("[STREAM-API] Estado huérfano limpiado, continuando con inicio")
            except Exception as e:
                print(f"[STREAM-API] Error verificando tarea, asumiendo huérfano: {e}")
                redis_client.delete('streaming:state')
                redis_client.delete('streaming:stop_requested')

        # Iniciar tarea de Celery en segundo plano
        print("[STREAM-API] Iniciando tarea de Celery...")
        task = start_streaming_task.delay(
            host='0.0.0.0',
            port=8765,
            fps=15,
            quality=75,
            use_ssl=True
        )

        print(f"[STREAM-API] ✅ Tarea de streaming iniciada: {task.id}")

        # Esperar un momento para que se registre en Redis
        time.sleep(0.5)

        # Verificar que se registró
        state = redis_client.hgetall('streaming:state')
        print(f"[STREAM-API] Estado después de iniciar: {state}")

        return jsonify({
            'success': True,
            'message': 'Streaming iniciado correctamente',
            'task_id': task.id
        }), 200

    except Exception as e:
        print(f"[STREAM-API] ❌ Error al iniciar streaming: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error al iniciar streaming: {str(e)}'
        }), 500


@app.route('/stream/stop', methods=['POST'])
@require_auth
def stop_streaming():
    """
    POST /stream/stop - Detiene el streaming de pantalla via Celery task.

    Returns:
        JSON: Estado de la operación
    """
    print("[STREAM-API] POST /stream/stop recibido")

    try:
        # Verificar si hay streaming activo en Redis
        redis_client = redis_state._get_redis_client()
        state = redis_client.hgetall('streaming:state')

        print(f"[STREAM-API] Estado actual en Redis: {state}")

        if not state or state.get(b'active') != b'true':
            print("[STREAM-API] No hay streaming activo para detener")
            return jsonify({
                'success': False,
                'message': 'No hay streaming activo'
            }), 400

        # Llamar a la tarea de detención
        print("[STREAM-API] Enviando señal de detención...")
        result = stop_streaming_task.delay()

        print(f"[STREAM-API] ✅ Señal de detención enviada: {result.id}")

        # Esperar un momento para verificar
        time.sleep(0.5)

        state = redis_client.hgetall('streaming:state')
        print(f"[STREAM-API] Estado después de detener: {state}")

        return jsonify({
            'success': True,
            'message': 'Streaming detenido correctamente',
            'task_id': result.id
        }), 200

    except Exception as e:
        print(f"[STREAM-API] ❌ Error al detener streaming: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error al detener streaming: {str(e)}'
        }), 500


@app.route('/stream/status', methods=['GET'])
@require_auth
def streaming_status():
    """
    GET /stream/status - Obtiene el estado del streaming desde Redis.

    Verifica que la tarea de Celery realmente esté corriendo y limpia estados huérfanos.

    Returns:
        JSON: Estado del streaming (active/inactive) y detalles
    """
    try:
        # Consultar estado desde Redis
        redis_client = redis_state._get_redis_client()
        state = redis_client.hgetall('streaming:state')

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
                    # Estados inválidos (huérfanos): PENDING, FAILURE, SUCCESS, REVOKED
                    if task_state not in ['STARTED', 'RETRY']:
                        print(f"[STREAM-STATUS] ⚠️  Estado huérfano detectado (tarea {task_state}), limpiando...")
                        redis_client.delete('streaming:state')
                        redis_client.delete('streaming:stop_requested')

                        # Retornar como inactivo
                        return jsonify({
                            'success': True,
                            'active': False,
                            'port': None,
                            'clients': 0
                        }), 200
                except Exception as e:
                    print(f"[STREAM-STATUS] Error verificando tarea: {e}")
                    # En caso de error, asumir huérfano y limpiar
                    redis_client.delete('streaming:state')
                    redis_client.delete('streaming:stop_requested')
                    return jsonify({
                        'success': True,
                        'active': False,
                        'port': None,
                        'clients': 0
                    }), 200

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
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


def require_auth_sse(f):
    """
    Decorador de autenticación especial para endpoints SSE.

    No redirecciona, sino que envía un mensaje de error via SSE
    si no está autenticado.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar si ya está autenticado por sesión (navegador web)
        if 'authenticated' in session and session['authenticated']:
            print("[STREAM-FEED] ✅ Autenticado via sesión")
            return f(*args, **kwargs)

        # Verificar si hay token en el header Authorization (API)
        auth_header = request.headers.get('Authorization')
        if auth_header:
            token = auth_header
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]

            if token == server.token:
                print("[STREAM-FEED] ✅ Autenticado via token")
                return f(*args, **kwargs)

        # Si no está autenticado, enviar error via SSE
        print("[STREAM-FEED] ❌ Acceso no autenticado")

        def send_error():
            yield "data: error_unauthorized\n\n"

        return flask.Response(
            send_error(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )

    return decorated_function


@app.route('/stream/feed')
@require_auth_sse
def stream_feed():
    """
    GET /stream/feed - Feed de video mediante Server-Sent Events.

    Este endpoint sirve el stream de video a través de HTTP usando SSE,
    lo que permite que funcione con cualquier IP y a través del túnel.

    Verifica el estado de streaming desde Redis y captura frames localmente.
    """
    def generate_frames():
        """Genera frames del streaming si está activo según Redis."""
        import time
        import base64

        # Crear streamer local para captura de frames
        local_streamer = None
        current_fps = 15
        current_quality = 75

        # Contador de intentos fallidos consecutivos
        inactive_count = 0
        max_inactive = 3  # Terminar después de 3 segundos inactivo

        print("[STREAM-FEED] Nueva conexión SSE establecida")

        try:
            while True:
                try:
                    # Verificar estado en Redis
                    redis_client = redis_state._get_redis_client()
                    state = redis_client.hgetall('streaming:state')

                    is_active = state and state.get(b'active') == b'true'

                    if is_active:
                        # Reset contador si está activo
                        inactive_count = 0

                        # Obtener configuración desde Redis
                        fps_str = state.get(b'fps', b'15').decode('utf-8')
                        quality_str = state.get(b'quality', b'75').decode('utf-8')
                        new_fps = int(fps_str)
                        new_quality = int(quality_str)

                        # Crear o recrear streamer si cambió la configuración
                        if not local_streamer or current_fps != new_fps or current_quality != new_quality:
                            if local_streamer:
                                print(f"[STREAM-FEED] Recreando streamer (fps={new_fps}, quality={new_quality})")
                            else:
                                print(f"[STREAM-FEED] Creando streamer (fps={new_fps}, quality={new_quality})")

                            local_streamer = ScreenStreamer(
                                port=8765,  # No se usa
                                quality=new_quality,
                                fps=new_fps,
                                ssl_certfile=get_resource_path('ssl/cert.pem'),
                                ssl_keyfile=get_resource_path('ssl/key.pem')
                            )
                            current_fps = new_fps
                            current_quality = new_quality

                        try:
                            # Actualizar timestamp de actividad de clientes
                            redis_client.set('streaming:last_client_activity', str(time.time()), ex=60)

                            # Capturar frame
                            frame_data = local_streamer.capture_screen()

                            # Codificar en base64
                            frame_b64 = base64.b64encode(frame_data).decode('utf-8')
                            message = f"data:image/jpeg;base64,{frame_b64}"

                            # Enviar como evento SSE
                            yield f"data: {message}\n\n"

                            # Control de FPS dinámico
                            time.sleep(1 / current_fps)

                        except GeneratorExit:
                            # Cliente desconectado
                            print("[STREAM-FEED] Cliente desconectado del feed")
                            break
                        except Exception as e:
                            print(f"[STREAM-FEED] Error generando frame: {e}")
                            yield f"data: error\n\n"
                            time.sleep(0.5)
                    else:
                        # Streaming inactivo según Redis
                        inactive_count += 1

                        # Limpiar streamer local si existe
                        if local_streamer:
                            local_streamer = None
                            print("[STREAM-FEED] Streamer local liberado")

                        if inactive_count >= max_inactive:
                            # Enviar mensaje final y terminar la conexión
                            print("[STREAM-FEED] Stream inactivo, cerrando conexión SSE")
                            yield f"data: stream_stopped\n\n"
                            break

                        # Enviar mensaje de inactivo mientras esperamos
                        yield f"data: inactive\n\n"
                        time.sleep(1)

                except GeneratorExit:
                    # Cliente cerró la conexión
                    print("[STREAM-FEED] Conexión cerrada por el cliente")
                    break
                except Exception as e:
                    print(f"[STREAM-FEED] Error en generador: {e}")
                    break

        finally:
            # Limpiar streamer local al finalizar
            if local_streamer:
                local_streamer = None
                print("[STREAM-FEED] Streamer local limpiado (finally)")

    return flask.Response(
        generate_frames(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


@app.route('/stream-view')
@require_auth
def stream_view():
    """
    GET /stream-view - Vista dedicada para el streaming de pantalla.

    Returns:
        HTML: Página completa para visualizar el streaming
    """
    return flask.render_template('stream_view.html')


@app.route('/settings', methods=['GET', 'POST'])
@require_auth
def settings():
    """
    GET/POST /settings - Página de configuración del servidor.

    GET: Muestra el formulario de configuración con los valores actuales
    POST: Guarda la nueva configuración en config.json

    Returns:
        HTML: Formulario de configuración
        Redirect: Después de guardar exitosamente
    """
    from .config import get_config_data, save_config_data

    if request.method == 'POST':
        try:
            # Obtener configuración actual para comparar cambios
            old_config = get_config_data()
            old_subdomain = old_config.get('tunnel_subdomain', '').strip()
            if not old_subdomain:
                old_subdomain = old_config.get('machine_id', '').strip()
            old_port = str(old_config.get('port', '5055'))

            # Obtener datos del formulario
            new_config = {
                'url': request.form.get('url', ''),
                'token': request.form.get('token', ''),
                'machine_id': request.form.get('machine_id', ''),
                'license_key': request.form.get('license_key', ''),
                'ip': request.form.get('ip', '0.0.0.0'),
                'port': request.form.get('port', '5055'),
                'tunnel_subdomain': request.form.get('tunnel_subdomain', ''),
                'tunnel_id': request.form.get('tunnel_id', '3d7de42c-4a8a-4447-b14f-053cc485ce6b')
            }

            # Determinar nuevo subdominio
            new_subdomain = new_config.get('tunnel_subdomain', '').strip()
            if not new_subdomain:
                new_subdomain = new_config.get('machine_id', '').strip()
            new_port = str(new_config.get('port', '5055'))

            # Verificar si cambió el subdominio o el puerto
            subdomain_changed = old_subdomain.lower() != new_subdomain.lower()
            port_changed = old_port != new_port
            tunnel_config_changed = subdomain_changed or port_changed

            # Verificar si el túnel está activo antes de hacer cambios
            tunnel_was_active = False
            if tunnel_config_changed:
                result = subprocess.run(
                    ['pgrep', '-f', 'cloudflared tunnel run'],
                    capture_output=True,
                    text=True
                )
                tunnel_was_active = bool(result.stdout.strip())

                # Si el túnel está activo, detenerlo primero
                if tunnel_was_active:
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        if pid:
                            subprocess.run(['kill', pid], check=False)
                    time.sleep(1)  # Esperar a que se detenga

            # Guardar configuración
            save_config_data(new_config)

            # Actualizar configuración de Cloudflare
            from pathlib import Path

            hostname = f"{new_subdomain.lower()}.automatehub.es"

            # Actualizar archivo de configuración de Cloudflare
            cloudflare_config_path = Path.home() / '.cloudflared' / 'config.yml'
            tunnel_id = new_config.get('tunnel_id', '3d7de42c-4a8a-4447-b14f-053cc485ce6b')
            credentials_path = Path.home() / '.cloudflared' / f'{tunnel_id}.json'

            config_content = f"""tunnel: {tunnel_id}
            credentials-file: {credentials_path}
            
            ingress:
              # Subdominio configurado: {hostname}
              - hostname: {hostname}
                service: https://localhost:{new_port}
                originRequest:
                  noTLSVerify: true
              - service: http_status:404
            """

            cloudflare_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cloudflare_config_path, 'w') as f:
                f.write(config_content)

            # Crear ruta DNS en Cloudflare
            subprocess.run(
                ['cloudflared', 'tunnel', 'route', 'dns', 'robotrunner', hostname],
                capture_output=True,
                text=True
            )

            # Si el túnel estaba activo, reiniciarlo con la nueva configuración
            if tunnel_was_active:
                subprocess.Popen(
                    ['cloudflared', 'tunnel', 'run', 'robotrunner'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                time.sleep(2)  # Esperar a que se inicie

            # Actualizar el servidor global con la nueva configuración
            global server
            config_data = get_config_data()
            server = Server(config_data)

            # Si cambió el puerto, programar reinicio del servidor
            if port_changed:
                import signal

                def trigger_restart_with_new_port():
                    time.sleep(1)
                    os.kill(os.getpid(), signal.SIGHUP)

                # Usar threading para tarea simple de restart
                import threading
                threading.Thread(target=trigger_restart_with_new_port, daemon=True).start()

                # Retornar respuesta JSON con el nuevo puerto para que el frontend redirija
                return jsonify({
                    'success': True,
                    'port_changed': True,
                    'new_port': new_port,
                    'message': f'Configuración guardada. Reiniciando servidor en puerto {new_port}...'
                }), 200

            # Mensaje apropiado según lo que pasó
            if tunnel_config_changed and tunnel_was_active:
                flash(f'Configuración guardada y túnel reiniciado con nuevo subdominio: {hostname}', 'success')
            elif tunnel_config_changed:
                flash(f'Configuración guardada. Nuevo subdominio: {hostname}. Inicia el túnel para aplicar cambios.', 'success')
            else:
                flash('Configuración guardada correctamente.', 'success')

            return redirect(url_for('settings'))

        except Exception as e:
            flash(f'Error al guardar configuración: {str(e)}', 'danger')
            return redirect(url_for('settings'))

    # GET: Mostrar formulario con valores actuales
    config = get_config_data()
    return render_template('settings.html', config=config)


# ============================================================================
# UTILIDADES - Gestión de procesos Gunicorn
# ============================================================================

def find_gunicorn_processes():
    """
    Encuentra procesos de Gunicorn corriendo en el sistema.

    Returns:
        list: Lista de PIDs de procesos de Gunicorn
    """
    import signal

    pids = []
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True,
            timeout=5
        )

        for line in result.stdout.split('\n'):
            if 'gunicorn' in line and 'grep' not in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        pids.append(int(parts[1]))
                    except (ValueError, IndexError):
                        pass

    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        # Si falla, asumir que no hay procesos (compatibilidad Windows)
        pass

    return pids


def kill_gunicorn_processes(pids, force=False):
    """
    Mata procesos de Gunicorn.

    Args:
        pids (list): Lista de PIDs a matar
        force (bool): Si True, usa SIGKILL en lugar de SIGTERM

    Returns:
        bool: True si todos los procesos fueron terminados
    """
    import signal

    if not pids:
        return True

    for pid in pids:
        try:
            if force:
                os.kill(pid, signal.SIGKILL)
            else:
                os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass

    return True


def check_and_kill_existing_gunicorn():
    """
    Verifica si hay procesos de Gunicorn corriendo y los detiene.

    Esta función se ejecuta al iniciar la aplicación para evitar
    conflictos de puerto con instancias anteriores.

    Returns:
        bool: True si se pudieron detener todos los procesos, False si no
    """
    pids = find_gunicorn_processes()

    if not pids:
        return True

    print("=" * 70)
    print("⚠️  ATENCIÓN: Procesos de Gunicorn detectados")
    print("=" * 70)
    print(f"Se encontraron {len(pids)} proceso(s) de Gunicorn corriendo.")
    print(f"PIDs: {', '.join(map(str, pids))}")
    print()
    print("Estos procesos deben detenerse para iniciar el servidor.")
    print()

    # Preguntar al usuario
    try:
        response = input("¿Deseas detenerlos automáticamente? (s/n): ").strip().lower()

        if response in ['s', 'y', 'si', 'yes']:
            print()
            print("🔧 Deteniendo procesos...")

            # Intentar terminación grácil
            kill_gunicorn_processes(pids, force=False)
            time.sleep(2)

            # Verificar si quedaron procesos
            remaining = find_gunicorn_processes()

            if remaining:
                print("⚠️  Algunos procesos no respondieron. Forzando terminación...")
                kill_gunicorn_processes(remaining, force=True)
                time.sleep(1)

                # Verificación final
                final_check = find_gunicorn_processes()
                if final_check:
                    print("❌ No se pudieron detener todos los procesos.")
                    print("   Por favor, detenlos manualmente con:")
                    print(f"   kill -9 {' '.join(map(str, final_check))}")
                    print("   O ejecuta: ./scripts/kill_gunicorn.sh")
                    return False

            print("✅ Procesos detenidos correctamente")
            print()
            return True

        else:
            print()
            print("❌ No se puede continuar con procesos corriendo.")
            print()
            print("Para detenerlos manualmente:")
            print("   ./scripts/kill_gunicorn.sh")
            print("   python scripts/kill_gunicorn.py")
            print(f"   kill -TERM {' '.join(map(str, pids))}")
            print()
            return False

    except (KeyboardInterrupt, EOFError):
        print()
        print("❌ Operación cancelada por el usuario")
        return False


# ============================================================================
# CLEANUP - Funciones de limpieza al detener el servidor
# ============================================================================

def cleanup_celery_workers():
    """
    Detiene todos los procesos de Celery asociados al proyecto robotrunner.

    Esta función se ejecuta automáticamente al detener el servidor
    via atexit y signal handlers.

    Estrategia (siguiendo el patrón del proyecto):
        1. Intenta shutdown grácil con celery_app.control.shutdown()
        2. Espera con timeout (5 segundos)
        3. Si quedan procesos, envía SIGTERM
        4. Si aún quedan procesos, fuerza con SIGKILL
    """
    print("\n[CLEANUP] Deteniendo workers de Celery...")

    def find_celery_pids():
        """Busca PIDs de workers de Celery relacionados con src.celery_config."""
        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=5
            )

            pids = []
            for line in result.stdout.split('\n'):
                # Buscar procesos que contengan 'celery' y 'src.celery_config'
                if 'celery' in line and 'src.celery_config' in line and 'grep' not in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            pid = int(parts[1])
                            pids.append(pid)
                        except (ValueError, IndexError):
                            pass
            return pids
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            print(f"[CLEANUP] Error buscando PIDs: {e}")
            return []

    try:
        # Paso 1: Buscar workers activos
        celery_pids = find_celery_pids()

        if not celery_pids:
            print("[CLEANUP] No se encontraron workers de Celery activos")
            return

        print(f"[CLEANUP] Encontrados {len(celery_pids)} worker(s) de Celery: {celery_pids}")

        # Paso 2: Intentar shutdown grácil con control API de Celery
        print("[CLEANUP] Intentando shutdown grácil con celery_app.control.shutdown()...")
        try:
            celery_app.control.shutdown()
            print("[CLEANUP] Señal de shutdown enviada a workers")
        except Exception as e:
            print(f"[CLEANUP] ⚠️  Error al enviar shutdown: {e}")

        # Paso 3: Esperar a que los workers terminen (timeout: 5 segundos)
        print("[CLEANUP] Esperando 5 segundos para terminación grácil...")
        time.sleep(5)

        # Paso 4: Verificar si quedaron procesos
        remaining_pids = find_celery_pids()

        if not remaining_pids:
            print("[CLEANUP] ✅ Workers de Celery detenidos grácilmente")
            return

        # Paso 5: Si quedaron procesos, enviar SIGTERM
        print(f"[CLEANUP] {len(remaining_pids)} worker(s) no terminaron grácilmente")
        print(f"[CLEANUP] Enviando SIGTERM a: {remaining_pids}")

        for pid in remaining_pids:
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"[CLEANUP] Enviada señal SIGTERM a PID {pid}")
            except (ProcessLookupError, PermissionError) as e:
                print(f"[CLEANUP] No se pudo terminar PID {pid}: {e}")

        # Paso 6: Esperar 2 segundos más
        time.sleep(2)

        # Paso 7: Verificar si aún quedan procesos
        remaining_pids = find_celery_pids()

        if not remaining_pids:
            print("[CLEANUP] ✅ Workers de Celery detenidos con SIGTERM")
            return

        # Paso 8: Forzar terminación con SIGKILL
        print(f"[CLEANUP] {len(remaining_pids)} worker(s) aún activos, forzando terminación...")
        for pid in remaining_pids:
            try:
                os.kill(pid, signal.SIGKILL)
                print(f"[CLEANUP] Enviada señal SIGKILL a PID {pid}")
            except (ProcessLookupError, PermissionError) as e:
                print(f"[CLEANUP] No se pudo forzar terminación de PID {pid}: {e}")

        print("[CLEANUP] ✅ Workers de Celery detenidos con SIGKILL")

    except Exception as e:
        print(f"[CLEANUP] Error al detener workers de Celery: {e}")


# ============================================================================
# MAIN - Punto de entrada de la aplicación
# ============================================================================

def main():
    """
    Punto de entrada principal de la aplicación.

    Flujo:
        1. Configurar entorno (macOS fork safety)
        2. Parsear argumentos de línea de comandos
        3. Cargar configuración
        4. Inicializar servidor
        5. Decidir modo de ejecución:
           a. --server-only: Solo servidor (sin GUI)
           b. Normal: Servidor + GUI con webview

    Modos:
        --server-only:
            - Ejecuta solo Gunicorn en el hilo principal
            - Útil para producción sin GUI
            - Útil para ser llamado como subprocess

        Normal (sin argumentos):
            - Lanza servidor como subprocess
            - Espera a que el servidor esté listo
            - Abre GUI con webview
            - Al cerrar GUI, termina el servidor
    """
    global server

    # ========================================================================
    # FIX PARA macOS: Deshabilitar fork safety check de Objective-C
    # ========================================================================
    # Gunicorn usa fork() para crear workers, pero macOS tiene problemas
    # con Objective-C cuando se hace fork después de inicializar ciertos
    # frameworks (como los que usa webview).
    #
    # Esta variable de ambiente desactiva el check de seguridad, permitiendo
    # que Gunicorn funcione correctamente en macOS.
    #
    # Referencias:
    # - https://github.com/benoitc/gunicorn/issues/1905
    # - https://bugs.python.org/issue33725
    os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'

    # ========================================================================
    # ARGUMENTOS DE LÍNEA DE COMANDOS
    # ========================================================================
    parser = argparse.ArgumentParser(
        description='Robot Runner - Ejecuta robots de automatización remotamente',
        epilog='Para más información, ver documentación en docs/',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Comandos especiales
    special_group = parser.add_argument_group('Comandos Especiales')
    special_group.add_argument(
        '--show-config', action='store_true',
        help='Muestra la configuración actual y sale'
    )
    special_group.add_argument(
        '--setup-tunnel', action='store_true',
        help='Configura el túnel de Cloudflare automáticamente'
    )
    special_group.add_argument(
        '--tunnel-status', action='store_true',
        help='Verifica el estado del túnel de Cloudflare'
    )
    special_group.add_argument(
        '--start-tunnel', action='store_true',
        help='Inicia el túnel de Cloudflare'
    )
    special_group.add_argument(
        '--stop-tunnel', action='store_true',
        help='Detiene el túnel de Cloudflare'
    )

    # Configuración del servidor
    server_group = parser.add_argument_group('Configuración del Servidor')
    server_group.add_argument(
        '--url', type=str,
        help='URL del orquestador/consola (ej: https://console.example.com)'
    )
    server_group.add_argument(
        '--token', type=str,
        help='Token de autenticación para el orquestador'
    )
    server_group.add_argument(
        '--machine_id', type=str,
        help='ID único de esta máquina'
    )
    server_group.add_argument(
        '--license_key', type=str,
        help='License key de esta máquina'
    )
    server_group.add_argument(
        '--folder', type=str,
        help='Directorio donde se encuentran los robots'
    )
    server_group.add_argument(
        '--ip', type=str,
        help='IP pública de esta máquina (default: auto-detect)'
    )
    server_group.add_argument(
        '--port', type=int,
        help='Puerto en el que escuchar (default: 5055)'
    )

    # Configuración del túnel
    tunnel_group = parser.add_argument_group('Configuración del Túnel Cloudflare')
    tunnel_group.add_argument(
        '--tunnel-subdomain', type=str,
        help='Subdominio para el túnel (default: machine_id)'
    )
    tunnel_group.add_argument(
        '--tunnel-id', type=str,
        help='ID del túnel de Cloudflare (default: 3d7de42c-4a8a-4447-b14f-053cc485ce6b)'
    )

    # Opciones de ejecución
    execution_group = parser.add_argument_group('Opciones de Ejecución')
    execution_group.add_argument(
        '--server-only', action='store_true',
        help='Ejecutar solo el servidor sin GUI (para subprocess)'
    )
    execution_group.add_argument(
        '--save', action='store_true',
        help='Guardar la configuración proporcionada en config.json'
    )
    execution_group.add_argument(
        '--no-save', action='store_true',
        help='No guardar la configuración (solo usar valores para esta sesión)'
    )

    # ========================================================================
    # CARGAR CONFIGURACIÓN
    # ========================================================================
    # Orden de prioridad:
    # 1. Argumentos de línea de comandos
    # 2. Archivo config.json
    # 3. Valores por defecto

    # Verificar instancia única (comentado por ahora)
    # s = check_already_running()

    # Cargar config.json
    config = get_config_data()

    # Sobrescribir con argumentos CLI
    config = get_args(parser, config)

    # Guardar configuración actualizada solo si se indica
    should_save = config.pop('_should_save', False)
    if should_save:
        # Limpiar campos internos antes de guardar
        config_to_save = {k: v for k, v in config.items() if not k.startswith('_')}
        write_to_config(config_to_save)
        print(f"✅ Configuración guardada en {Path.home() / 'Robot' / 'config.json'}")

    # ========================================================================
    # VERIFICAR PROCESOS EXISTENTES DE GUNICORN
    # ========================================================================
    # Solo verificar en modo normal (con GUI), no en modo --server-only
    if '--server-only' not in sys.argv:
        if not check_and_kill_existing_gunicorn():
            print("\n⚠️  No se puede continuar. Saliendo...")
            sys.exit(1)

    # ========================================================================
    # ASEGURAR QUE REDIS ESTÉ CORRIENDO
    # ========================================================================
    # Redis es necesario para Celery y para el estado compartido
    print("🔍 Verificando Redis...")
    try:
        redis_manager.ensure_redis_running()
        print("✅ Redis está listo")
    except Exception as e:
        print(f"❌ Error con Redis: {e}")
        print("   Por favor instala Redis e intenta de nuevo:")
        print("   - macOS: brew install redis")
        print("   - Linux: sudo apt-get install redis-server")
        print("   - Windows: Instala Memurai o usa WSL")
        sys.exit(1)

    # ========================================================================
    # INICIALIZAR SERVIDOR
    # ========================================================================
    server = Server(config)

    # Configurar Redis state manager con machine_id
    redis_state.set_machine_id(config['machine_id'])

    # Recuperar ejecuciones huérfanas (running/paused) y marcarlas como fallidas
    redis_state.mark_orphaned_executions_as_failed()

    # Establecer estado inicial a "free" y notificar al orquestador
    print("[INIT] Estableciendo estado inicial a 'free'")
    server.change_status("free", notify_remote=True)

    # ========================================================================
    # MODO DE EJECUCIÓN
    # ========================================================================

    if '--server-only' in sys.argv:
        # ====================================================================
        # MODO: Solo servidor (sin GUI)
        # ====================================================================
        # Este modo es usado cuando:
        # 1. Se ejecuta manualmente con --server-only
        # 2. Se ejecuta como subprocess desde el modo normal
        print(f"🚀 Starting Gunicorn server on https://0.0.0.0:{server.port}")
        print(f"📋 Workers: 4 | Threads per worker: 2")
        print(f"🔒 SSL: Enabled (cert.pem, key.pem)")
        print(f"⏸️  Press Ctrl+C to stop")
        print("-" * 60)

        start_gunicorn_server()

    else:
        # ====================================================================
        # MODO: Servidor + GUI
        # ====================================================================
        # Flujo:
        # 1. Lanza Gunicorn como subprocess en background
        # 2. Espera a que el servidor responda
        # 3. Abre GUI con webview
        # 4. Al cerrar GUI, termina el servidor

        print("=" * 60)
        print("  Robot Runner - Inicializando")
        print("=" * 60)
        print(f"📡 Servidor: https://0.0.0.0:{server.port}")
        print(f"🖥️  GUI: webview")
        print("-" * 60)

        # Lanzar servidor como subprocess
        print(f"🚀 Launching Gunicorn server...")

        # Ejecutar el módulo src.app en lugar de __file__ para compatibilidad
        server_process = subprocess.Popen(
            [sys.executable, '-m', 'src.app', '--server-only'],
            cwd=PROJECT_ROOT,  # Ejecutar desde el directorio raíz del proyecto
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Esperar a que el servidor esté listo
        print("⏳ Waiting for server to start...")
        if wait_for_server(f'https://127.0.0.1:{server.port}/', timeout=30):
            print("✅ Server ready!")
            print(f"🖥️  Launching GUI...")
            print("-" * 60)
        else:
            # Servidor no arrancó
            print("❌ Server failed to start!")
            print("\n📋 Server output:")
            print("-" * 60)

            # Mostrar errores del servidor
            try:
                stdout, stderr = server_process.communicate(timeout=2)
                if stderr:
                    print("STDERR:")
                    print(stderr.decode())
                if stdout:
                    print("\nSTDOUT:")
                    print(stdout.decode())
            except subprocess.TimeoutExpired:
                print("(timeout reading server output)")

            server_process.terminate()
            sys.exit(1)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    main()