"""
Authentication decorators for API and Web routes.

Provides three authentication strategies:
    - @require_token: API-only (Bearer token in Authorization header)
    - @require_auth: Hybrid (session for web, token for API)
    - @require_auth_sse: SSE-specific (sends error via event stream)
"""
from functools import wraps
from flask import jsonify, request, session, redirect, url_for, Response


def get_server():
    """
    Get the global server instance.
    
    Import here to avoid circular dependencies.
    """
    from . import _server
    return _server


def require_token(f):
    """
    Decorador que verifica el token de autenticación en las peticiones API.

    El token DEBE venir en el header Authorization:
    - Header: Authorization: Bearer <token>
    - O alternativamente: Authorization: <token>

    Returns:
        401: Si el token no está presente en el header
        403: Si el token es inválido
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        server = get_server()
        
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
        server = get_server()
        
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
        return redirect(url_for('web_auth.login'))

    return decorated_function


def require_auth_sse(f):
    """
    Decorador de autenticación especial para endpoints SSE.

    No redirecciona, sino que envía un mensaje de error via SSE
    si no está autenticado.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        server = get_server()
        
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

        # Headers seguros para WSGI/Waitress (sin 'Connection')
        return Response(
            send_error(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )

    return decorated_function
