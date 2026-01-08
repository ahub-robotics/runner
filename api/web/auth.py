"""
Web UI Authentication Routes.

Provides login/logout functionality for the web interface:
    - GET/POST /login: Authentication page with token validation
    - GET/POST /logout: Session termination
"""
import time
from flask import Blueprint, render_template, request, session, redirect, url_for
from api import get_server


# Create blueprint
web_auth_bp = Blueprint('web_auth', __name__)


@web_auth_bp.route('/login', methods=['GET', 'POST'])
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
    server = get_server()
    
    if request.method == 'GET':
        # NUEVO: Verificar si viene token en query parameter para login automático
        token_from_url = request.args.get('token')
        if token_from_url:
            # Validar token
            if server and token_from_url == server.token:
                # Token válido - crear sesión permanente (30 días)
                session['authenticated'] = True
                session['login_time'] = time.time()
                session.permanent = True  # Hacer sesión permanente por 30 días
                print(f"[LOGIN] ✅ Autenticación exitosa via URL (sesión permanente)")
                return redirect(url_for('web_ui.home'))
            else:
                # Token inválido desde URL
                print(f"[LOGIN] ❌ Token inválido desde URL")
                return render_template('login.html',
                    error='Token inválido en el enlace. Por favor, verifica el token.')

        # Si ya está autenticado, redirigir a home
        if 'authenticated' in session and session['authenticated']:
            return redirect(url_for('web_ui.home'))

        # Mostrar formulario de login
        return render_template('login.html', error=None)

    elif request.method == 'POST':
        token = request.form.get('token')

        # Validar token
        if server and token and token == server.token:
            # Crear sesión permanente (30 días)
            session['authenticated'] = True
            session['login_time'] = time.time()
            session.permanent = True  # Hacer sesión permanente por 30 días
            print(f"[LOGIN] ✅ Autenticación exitosa via formulario (sesión permanente)")
            return redirect(url_for('web_ui.home'))
        else:
            # Token inválido
            return render_template('login.html',
                error='Token inválido. Por favor, verifica el token en config.json.')


@web_auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """
    GET/POST /logout - Cerrar sesión.

    Limpia la sesión del usuario y redirige al login.

    Returns:
        Redirect a /login
    """
    session.clear()
    print("[LOGOUT] Sesión cerrada")
    return redirect(url_for('web_auth.login'))
