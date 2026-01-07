# FASE 5: División de app.py - Plan Detallado

## Resumen Ejecutivo

**Objetivo:** Dividir `src/app.py` (2,960 líneas monolíticas) en módulos especializados bajo `api/`

**Estado:** ✅ Arquitectura diseñada | 🔄 Migración incremental en progreso

**Archivos Creados:**
- ✅ `api/__init__.py` - Gestión del servidor global
- ✅ `api/auth.py` - 3 decoradores de autenticación (159 líneas)
- ✅ `api/middleware.py` - Logging y inicialización (165 líneas)

**Pendiente:** Migrar 22 rutas a módulos especializados (ver roadmap abajo)

---

## Análisis de src/app.py

### Estadísticas
- **Líneas totales:** 2,960
- **Rutas:** 22
- **Funciones helper:** 15+
- **Dependencias:** Flask, Celery, Redis, Gunicorn, Cloudflare Tunnel

### Categorías de Rutas

| Categoría | Rutas | Líneas Aprox | Prioridad |
|-----------|-------|--------------|-----------|
| REST API Control | 7 | ~700 | 🔴 Alta |
| Web UI | 5 | ~400 | 🔴 Alta |
| Streaming | 5 | ~400 | 🟡 Media |
| API Info/Logs | 2 | ~200 | 🟢 Baja |
| Tunnel Management | 3 | ~200 | 🟢 Baja |
| Server Management | 1 | ~50 | 🟢 Baja |

---

## Nueva Arquitectura

```
api/
├── __init__.py              # ✅ Server global + exports
├── auth.py                  # ✅ @require_token, @require_auth, @require_auth_sse
├── middleware.py            # ✅ Logging, server init
├── app.py                   # 🔄 Flask factory [SIGUIENTE]
├── wsgi.py                  # 🔄 Gunicorn entry point [SIGUIENTE]
│
├── web/                     # 🔴 PRIORIDAD ALTA
│   ├── __init__.py
│   ├── auth.py              # /login, /logout
│   ├── ui.py                # /, /connect, /connected
│   └── settings.py          # /settings
│
├── rest/                    # 🔴 PRIORIDAD ALTA
│   ├── __init__.py
│   ├── execution.py         # /run, /stop, /pause, /resume, /block
│   ├── status.py            # /status, /execution
│   └── info.py              # /api/server-info, /api/logs
│
├── streaming/               # 🟡 PRIORIDAD MEDIA
│   ├── __init__.py
│   ├── control.py           # /stream/start, /stream/stop, /stream/status
│   └── feed.py              # /stream/feed, /stream-view
│
├── tunnel/                  # 🟢 PRIORIDAD BAJA
│   ├── __init__.py
│   └── routes.py            # /tunnel/start, /tunnel/stop, /tunnel/status
│
└── server/                  # 🟢 PRIORIDAD BAJA
    ├── __init__.py
    └── routes.py            # /server/restart
```

---

## Roadmap de Migración

### PASO 1: Flask Factory ✅ (COMPLETADO - Archivos base)
**Archivos:**
- [x] `api/__init__.py` - Server management
- [x] `api/auth.py` - Authentication decorators
- [x] `api/middleware.py` - Request logging & initialization

**Resultado:** Infraestructura base lista para rutas

---

### PASO 2: Flask App Factory 🔄 (EN PROGRESO)
**Archivo:** `api/app.py`

**Contenido:**
```python
def create_app(config=None):
    \"\"\"
    Flask application factory.
    
    Returns configured Flask app with all blueprints registered.
    \"\"\"
    app = Flask(__name__)
    
    # Configure Flask
    configure_app(app, config)
    
    # Register middleware
    register_middleware(app)
    
    # Register blueprints
    register_blueprints(app)
    
    return app
```

**Tareas:**
- [ ] Crear `create_app()` factory
- [ ] Extraer configuración de Flask
- [ ] Registrar middlewares
- [ ] Sistema de registro de blueprints

---

### PASO 3: Web UI Routes (Prioridad Alta)
**Archivos:** `api/web/auth.py`, `api/web/ui.py`, `api/web/settings.py`

**Rutas a migrar:**

#### `api/web/auth.py` (~100 líneas)
- `GET/POST /login` (líneas 1236-1302)
- `GET/POST /logout` (líneas 1305-1316)

#### `api/web/ui.py` (~200 líneas)
- `GET /` (líneas 1319-1338)
- `GET/POST /connect` (líneas 1341-1418)
- `GET/POST /connected` (líneas 1419-1453)

#### `api/web/settings.py` (~150 líneas)
- `GET/POST /settings` (líneas 2276-2428)

**Blueprint:**
```python
from flask import Blueprint

web_ui_bp = Blueprint('web_ui', __name__)

# Register routes...
```

---

### PASO 4: REST API Control (Prioridad Alta)
**Archivos:** `api/rest/status.py`, `api/rest/execution.py`, `api/rest/info.py`

#### `api/rest/status.py` (~150 líneas)
- `GET /status` (líneas 558-612)
- `GET /execution` (líneas 615-675)

#### `api/rest/execution.py` (~500 líneas)
- `POST /run` (líneas 677-951) ⚠️ Endpoint más largo
- `GET /stop` (líneas 952-1045)
- `GET /pause` (líneas 1046-1128)
- `GET /resume` (líneas 1129-1207)
- `GET /block` (líneas 1208-1229)

#### `api/rest/info.py` (~200 líneas)
- `GET /api/server-info` (líneas 1456-1554)
- `GET /api/logs` (líneas 1557-1620)

**Blueprint:**
```python
rest_api_bp = Blueprint('rest_api', __name__)

# All routes use @require_token
```

---

### PASO 5: Streaming Endpoints (Prioridad Media)
**Archivos:** `api/streaming/control.py`, `api/streaming/feed.py`

#### `api/streaming/control.py` (~200 líneas)
- `POST /stream/start` (líneas 1861-1941)
- `POST /stream/stop` (líneas 1944-1994)
- `GET /stream/status` (líneas 1997-2086)

#### `api/streaming/feed.py` (~150 líneas)
- `GET /stream/feed` (líneas 2132-2261) - SSE endpoint
- `GET /stream-view` (líneas 2264-2273)

**Blueprint:**
```python
streaming_bp = Blueprint('streaming', __name__, url_prefix='/stream')
```

---

### PASO 6: Tunnel Management (Prioridad Baja)
**Archivo:** `api/tunnel/routes.py` (~200 líneas)

**Rutas:**
- `POST /tunnel/start` (líneas 1626-1713)
- `POST /tunnel/stop` (líneas 1716-1761)
- `GET /tunnel/status` (líneas 1764-1819)

**Dependencias:**
- Cloudflare `cloudflared` binary
- `~/.cloudflared/config.yml`
- Process management (subprocess)

---

### PASO 7: Server Management (Prioridad Baja)
**Archivo:** `api/server/routes.py` (~50 líneas)

**Ruta:**
- `POST /server/restart` (líneas 1820-1854)

---

### PASO 8: Gunicorn Entry Point
**Archivo:** `api/wsgi.py`

**Contenido:**
```python
from api.app import create_app

app = create_app()

if __name__ == '__main__':
    # For development only
    app.run()
```

---

## Estrategia de Migración

### 1. Copiar, No Mover (Inicialmente)
- Mantener `src/app.py` funcional durante migración
- Crear nuevos módulos en `api/`
- Probar cada módulo independientemente
- Una vez estable, eliminar código antiguo

### 2. Testing Incremental
- Cada módulo migrado debe tener tests
- Verificar que rutas funcionan igual
- Probar autenticación en cada endpoint
- Validar responses con Postman/curl

### 3. Imports y Dependencias
**Cambios necesarios:**
```python
# Antes (src/app.py)
from .config import get_config_data
from .server import Server
from .tasks import run_robot_task

# Después (api/*)
from shared.config.loader import get_config_data
from executors.server import Server
from executors.tasks import run_robot_task
```

### 4. Decoradores
**Todas las rutas usan:**
- `@require_token` - Solo API
- `@require_auth` - Híbrido (web + API)
- `@require_auth_sse` - Streaming SSE

**Import:**
```python
from api.auth import require_token, require_auth, require_auth_sse
```

---

## Checklist de Migración

### Por Cada Módulo:

- [ ] Crear archivo bajo `api/`
- [ ] Copiar rutas del rango de líneas indicado
- [ ] Actualizar imports a shared/executors/streaming
- [ ] Crear Blueprint y registrar rutas
- [ ] Importar decoradores de `api.auth`
- [ ] Probar rutas con curl/Postman
- [ ] Escribir tests unitarios
- [ ] Documentar cambios en este archivo

---

## Compatibilidad Hacia Atrás

### Mantener `src/app.py` Funcional
Durante la transición, `src/app.py` debe seguir funcionando:

```python
# src/app.py (versión de transición)

# Importar el nuevo sistema
try:
    from api.app import create_app as new_create_app
    USE_NEW_API = True
except ImportError:
    USE_NEW_API = False

if USE_NEW_API:
    # Usar nuevo sistema modular
    app = new_create_app()
else:
    # Fallback al sistema monolítico
    app = flask.Flask(__name__)
    # ... configuración antigua ...
```

---

## Métricas de Éxito

### Objetivos:
- ✅ Reducir `src/app.py` de 2,960 a <500 líneas
- ✅ Cada módulo <300 líneas
- ✅ Cobertura de tests >70% por módulo
- ✅ Sin regresiones funcionales
- ✅ Tiempo de respuesta sin degradación

### Progreso Actual:
- **Líneas migradas:** ~324 (auth.py + middleware.py)
- **% Completado:** ~11%
- **Módulos creados:** 3/15
- **Tests escritos:** 0/50 (pendiente)

---

## Próximos Pasos Inmediatos

1. **Crear `api/app.py`** - Flask factory con registro de blueprints
2. **Migrar Web UI Auth** - `api/web/auth.py` (/login, /logout)
3. **Migrar REST Status** - `api/rest/status.py` (/status, /execution)
4. **Tests Unitarios** - Para módulos migrados
5. **Validación End-to-End** - Probar flujos completos

---

## Notas Técnicas

### Manejo del Servidor Global
El servidor (`Server` instance) es compartido entre todos los módulos:

```python
# api/__init__.py
_server = None

def get_server():
    return _server

# Usado en decoradores y middleware
from api import get_server
server = get_server()
```

### Lazy Initialization
El servidor se inicializa en el primer request (middleware):

```python
@app.before_request
def before_request():
    init_server_if_needed(app)
```

Esto asegura compatibilidad con Gunicorn (WSGI).

### Blueprint URL Prefixes
```python
# Sin prefijo (raíz)
web_ui_bp = Blueprint('web_ui', __name__)
# Rutas: /, /login, /connect

# Con prefijo
streaming_bp = Blueprint('streaming', __name__, url_prefix='/stream')
# Rutas: /stream/start, /stream/feed

tunnel_bp = Blueprint('tunnel', __name__, url_prefix='/tunnel')
# Rutas: /tunnel/start, /tunnel/status
```

---

## Referencias

- Plan completo: `/Users/.../robotrunner_windows/.claude/plans/crispy-herding-rocket.md`
- Análisis app.py: Explore agent analysis (a6bdfe3)
- Código base: `src/app.py` (2,960 líneas)

---

**Última actualización:** 2026-01-07  
**Autor:** Claude Sonnet 4.5  
**Estado:** 🔄 En progreso (11% completado)
