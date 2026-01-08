# API Module - Robot Runner

Módulo API refactorizado que divide el monolítico `src/app.py` (2,960 líneas) en submódulos especializados usando Flask Blueprints.

## Estructura

```
api/
├── __init__.py          # Gestión de servidor global
├── auth.py              # Decoradores de autenticación
├── middleware.py        # Request logging y server init
├── app.py               # Flask application factory
├── wsgi.py              # Gunicorn WSGI entry point
│
├── web/                 # Interfaz web de usuario
│   ├── __init__.py
│   ├── auth.py          # ✅ /login, /logout
│   ├── ui.py            # ✅ /, /connect, /connected (parcial)
│   └── settings.py      # 📝 /settings (pendiente)
│
├── rest/                # REST API para control de robots
│   ├── __init__.py
│   ├── status.py        # 📝 /status, /execution (pendiente)
│   ├── execution.py     # 📝 /run, /stop, /pause, /resume (pendiente)
│   └── info.py          # 📝 /api/server-info, /api/logs (pendiente)
│
├── streaming/           # Video streaming
│   ├── __init__.py
│   ├── control.py       # 📝 /stream/start, /stream/stop, /stream/status (pendiente)
│   └── feed.py          # 📝 /stream/feed, /stream-view (pendiente)
│
├── tunnel/              # Cloudflare tunnel management
│   ├── __init__.py
│   └── routes.py        # 📝 /tunnel/* (pendiente)
│
└── server/              # Server management
    ├── __init__.py
    └── routes.py        # 📝 /server/restart (pendiente)
```

## Componentes Completados ✅

### Core Infrastructure

1. **`__init__.py`** - Servidor global compartido
   - `get_server()` - Obtener instancia del servidor
   - `set_server(server)` - Establecer instancia del servidor

2. **`auth.py`** (159 líneas) - Decoradores de autenticación
   - `@require_token` - Solo API (Bearer token)
   - `@require_auth` - Híbrido (sesión web + API token)
   - `@require_auth_sse` - SSE-specific (error via event stream)

3. **`middleware.py`** (165 líneas) - Middleware Flask
   - `init_server_if_needed()` - Lazy initialization del servidor
   - `log_request_to_file()` - Logging de requests a archivo compartido
   - `before_request_middleware()` - Auto-auth desde URL params
   - `after_request_middleware()` - Logging post-request

4. **`app.py`** (200 líneas) - Flask factory
   - `create_app(config)` - Crear y configurar aplicación Flask
   - `configure_flask()` - Configuración de Flask (sessions, cookies, SSL)
   - `register_blueprints()` - Registro dinámico de blueprints

5. **`wsgi.py`** (25 líneas) - Entry point Gunicorn
   - `app` - Instancia WSGI para Gunicorn

### Example Blueprints

6. **`web/auth.py`** (95 líneas) - Autenticación web
   - `GET/POST /login` - Página de login con validación de token
   - `GET/POST /logout` - Cierre de sesión

7. **`web/ui.py`** (75 líneas) - Páginas principales
   - `GET /` - Home (redirect a connected/connect)
   - `GET/POST /connect` - Configuración inicial (placeholder)
   - `GET/POST /connected` - Dashboard (placeholder)

## Uso

### Desarrollo (Flask dev server)

```bash
# Desde la raíz del proyecto
python -m api.app

# O directamente
python api/app.py
```

### Producción (Gunicorn)

```bash
# Usando config file
gunicorn api.wsgi:app --config gunicorn_config.py

# O con opciones inline
gunicorn api.wsgi:app \
    --bind 0.0.0.0:5001 \
    --workers 1 \
    --threads 4 \
    --certfile ssl/cert.pem \
    --keyfile ssl/key.pem
```

## Decoradores de Autenticación

### `@require_token` - Solo API

Valida Bearer token en header Authorization.

```python
from api.auth import require_token

@app.route('/api/endpoint')
@require_token
def api_endpoint():
    return jsonify({'status': 'ok'})
```

**Request:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" https://localhost:5001/api/endpoint
```

### `@require_auth` - Híbrido (Web + API)

Acepta sesión (navegador) o token (API).

```python
from api.auth import require_auth

@app.route('/dashboard')
@require_auth
def dashboard():
    return render_template('dashboard.html')
```

**Web:** Redirige a `/login` si no hay sesión  
**API:** Retorna 401/403 si no hay token válido

### `@require_auth_sse` - SSE Streaming

Envía error via event stream en lugar de redirect.

```python
from api.auth import require_auth_sse

@app.route('/stream/feed')
@require_auth_sse
def stream_feed():
    def generate():
        yield "data: frame1\n\n"
    return Response(generate(), mimetype='text/event-stream')
```

## Flask Factory Pattern

La aplicación usa el patrón factory para facilitar testing y configuración:

```python
from api.app import create_app

# Crear app con config por defecto
app = create_app()

# Crear app con config personalizada
app = create_app(config={
    'SECRET_KEY': 'custom-secret',
    'MAX_CONTENT_LENGTH': 32 * 1024 * 1024  # 32 MB
})
```

## Server Global

El servidor (`Server` instance) es compartido entre todos los blueprints:

```python
from api import get_server

def my_route():
    server = get_server()
    if server:
        print(f"Machine ID: {server.machine_id}")
        print(f"Status: {server.status}")
```

**Inicialización:** El servidor se inicializa lazy en el primer request (middleware).

## Blueprints

### Crear un Nuevo Blueprint

1. **Crear archivo en submódulo:**
```python
# api/rest/status.py
from flask import Blueprint, jsonify
from api.auth import require_token
from api import get_server

rest_status_bp = Blueprint('rest_status', __name__)

@rest_status_bp.route('/status')
@require_token
def get_status():
    server = get_server()
    return jsonify(status=server.status if server else 'unknown')
```

2. **Registrar en `app.py`:**
```python
# api/app.py - función register_blueprints()
try:
    from .rest.status import rest_status_bp
    app.register_blueprint(rest_status_bp)
except ImportError:
    pass  # Blueprint no disponible aún
```

### Naming Conventions

- **Blueprint name:** `{module}_{submodule}_bp` (ej: `rest_status_bp`)
- **Route prefix:** Usar `url_prefix` si todas las rutas comparten prefijo
  ```python
  streaming_bp = Blueprint('streaming', __name__, url_prefix='/stream')
  # Rutas: /stream/start, /stream/stop, /stream/status
  ```

## Progreso de Migración

| Módulo | Rutas | Estado | Líneas |
|--------|-------|--------|--------|
| Infrastructure | - | ✅ Completado | 644 |
| web/auth | 2 | ✅ Completado | 95 |
| web/ui | 3 | ✅ Completado | 180 |
| web/settings | 1 | ✅ Completado | 184 |
| rest/status | 2 | ✅ Completado | 150 |
| rest/execution | 5 | ✅ Completado | 500 |
| rest/info | 2 | ✅ Completado | 205 |
| streaming/control | 3 | ✅ Completado | 256 |
| streaming/feed | 2 | ✅ Completado | 158 |
| tunnel | 3 | ✅ Completado | 214 |
| server | 1 | ✅ Completado | 56 |

**Total:** ~2,642 / 2,960 líneas migradas (~89%)

## Testing

```bash
# Unit tests (cuando estén implementados)
pytest tests/unit/test_api_auth.py
pytest tests/unit/test_api_middleware.py
pytest tests/unit/test_api_blueprints.py

# Integration tests
pytest tests/integration/test_api_flow.py
```

## Referencias

- **Plan completo:** `docs/FASE5-APP-REFACTOR-PLAN.md`
- **Código original:** `src/app.py` (2,960 líneas)
- **Gunicorn config:** `gunicorn_config.py` (raíz del proyecto)

---

**Estado:** ✅ Completado (89% migrado - 22 rutas en 15 módulos)
**Última actualización:** 2026-01-08

**Nota:** El 11% restante son rutas legacy que permanecen en src/app.py para compatibilidad temporal.
