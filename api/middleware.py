"""
Middleware for request logging and server initialization.

Provides:
    - Server lazy initialization (WSGI compatibility)
    - HTTP request logging to shared file
    - Automatic token-based authentication from URL parameters
"""
import time
from datetime import datetime
from pathlib import Path
from flask import request, session


# Archivo de log para peticiones HTTP (compartido entre servidor y GUI)
REQUEST_LOG_FILE = Path.home() / 'Robot' / 'requests.log'


def init_server_if_needed(app):
    """
    Inicializa el servidor si aún no ha sido inicializado.

    Esta función se llama antes de cada petición para asegurar que
    el servidor esté disponible incluso cuando Flask se ejecuta como WSGI.

    Nota: Con Gunicorn, el servidor se inicializa en post_worker_init.
    Esta función es un fallback para desarrollo o WSGI sin Gunicorn.

    Args:
        app: Flask application instance
    """
    from . import get_server, set_server
    from shared.config.loader import get_config_data
    from shared.state.redis_state import redis_state
    from executors.server import Server

    current_server = get_server()

    if current_server is None:
        print("[MIDDLEWARE] 🔧 Servidor no inicializado, inicializando ahora...")

        try:
            config = get_config_data()
            server = Server(config)

            # Store globally
            set_server(server)

            # Also store in app-level variable for easy access
            app._server = server

            # Configurar Redis state manager con machine_id
            redis_state.set_machine_id(config['machine_id'])

            # Recuperar ejecuciones huérfanas (running/paused) y marcarlas como fallidas
            # Esto es importante para recuperarse de crashes o reinicios del servidor
            redis_state.mark_orphaned_executions_as_failed()

            # Establecer estado inicial a "free" y notificar al orquestador
            print("[MIDDLEWARE] ✅ Estableciendo estado inicial a 'free'")
            server.change_status("free", notify_remote=True)

            print(f"[MIDDLEWARE] ✅ Servidor inicializado (machine_id: {config['machine_id']})")
            return server
        except Exception as e:
            print(f"[MIDDLEWARE] ❌ Error inicializando servidor: {e}")
            import traceback
            traceback.print_exc()
            return None

    # Servidor ya inicializado (probablemente por post_worker_init)
    return current_server


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


def before_request_middleware(app):
    """
    Middleware que se ejecuta antes de cada petición.
    
    - Inicializa el servidor si no está inicializado
    - Guarda el tiempo de inicio
    - Verifica si hay un token en los query parameters para autenticación automática
    
    Args:
        app: Flask application instance
    """
    # Inicializar el servidor si aún no ha sido inicializado
    server = init_server_if_needed(app)

    # Guardar tiempo de inicio
    request.start_time = time.time()

    # AUTENTICACIÓN AUTOMÁTICA: Verificar si viene token en query parameter
    # Esto permite autenticar desde cualquier URL: /?token=xxx, /connected?token=xxx, etc.
    if 'authenticated' not in session or not session.get('authenticated'):
        token_from_url = request.args.get('token')
        if token_from_url and server:
            # Validar token
            if token_from_url == server.token:
                # Token válido - crear sesión permanente (30 días)
                session['authenticated'] = True
                session['login_time'] = time.time()
                session.permanent = True  # Hacer sesión permanente por 30 días
                print(f"[AUTH] ✅ Autenticación automática desde URL: {request.path}")
                # No redirigir, continuar con la petición normalmente


def after_request_middleware(response):
    """
    Middleware que se ejecuta después de cada petición.
    Registra la petición en el archivo de log compartido.
    
    Args:
        response: Flask response object
        
    Returns:
        response: Same Flask response object
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


def register_middleware(app):
    """
    Register all middleware with the Flask app.
    
    Args:
        app: Flask application instance
    """
    @app.before_request
    def before_request():
        before_request_middleware(app)
    
    @app.after_request
    def after_request(response):
        return after_request_middleware(response)
