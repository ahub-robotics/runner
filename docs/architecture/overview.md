# Arquitectura del Sistema - Robot Runner v2.0

## Resumen Ejecutivo

Robot Runner v2.0 implementa una **arquitectura modular híbrida** que separa responsabilidades en capas especializadas. Esta refactorización (de app.py monolítico de 2,960 líneas) mejora mantenibilidad, testabilidad y escalabilidad.

### Principios de Diseño

1. **Separación de Responsabilidades**: Cada módulo tiene un propósito claro y único
2. **Flask Blueprints**: Organización modular de rutas por dominio
3. **Lazy Initialization**: Servidor inicializado en primer request (compatible con WSGI)
4. **Shared State**: Redis como fuente única de verdad para estado distribuido
5. **Async Tasks**: Celery para operaciones de larga duración
6. **Testabilidad**: Dependencias inyectables y mocks fáciles

---

## Arquitectura de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENTE                                  │
│  (Orquestador, Browser, API Consumer)                           │
└────────────────────┬────────────────────────────────────────────┘
                     │ HTTPS (SSL/TLS)
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│                      ENTRY POINTS                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  run.py      │  │ gunicorn     │  │ tray_app.py  │          │
│  │  (Delegator) │  │ (Production) │  │ (GUI)        │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│                      API LAYER (Flask)                           │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  api/app.py - Flask Application Factory                     ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  web/        │  │  rest/       │  │  streaming/  │          │
│  │  (Web UI)    │  │  (API REST)  │  │  (SSE Feed)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │  tunnel/     │  │  server/     │                             │
│  │  (Cloudflare)│  │  (Mgmt)      │                             │
│  └──────────────┘  └──────────────┘                             │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│                   BUSINESS LOGIC LAYER                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ executors/   │  │ streaming/   │  │ shared/      │          │
│  │ (Robots)     │  │ (Video)      │  │ (Common)     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Redis       │  │  Celery      │  │  Filesystem  │          │
│  │  (State)     │  │  (Tasks)     │  │  (Logs, SSL) │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Estructura de Directorios

```
robotrunner/
│
├── api/                         # 🔌 API Layer - Interfaz externa
│   ├── __init__.py              # Server global management
│   ├── app.py                   # Flask application factory
│   ├── wsgi.py                  # WSGI entry point (Gunicorn)
│   ├── auth.py                  # Authentication decorators
│   ├── middleware.py            # Request logging, initialization
│   │
│   ├── web/                     # Web UI (Browser)
│   │   ├── auth.py              # /login, /logout
│   │   ├── ui.py                # /, /connect, /connected
│   │   └── settings.py          # /settings
│   │
│   ├── rest/                    # REST API (Orquestador)
│   │   ├── status.py            # /status, /execution
│   │   ├── execution.py         # /run, /stop, /pause, /resume
│   │   └── info.py              # /api/server-info, /api/logs
│   │
│   ├── streaming/               # Video Streaming (SSE)
│   │   ├── control.py           # /stream/start, /stream/stop
│   │   └── feed.py              # /stream/feed (SSE)
│   │
│   ├── tunnel/                  # Cloudflare Tunnel
│   │   └── routes.py            # /tunnel/*
│   │
│   └── server/                  # Server Management
│       └── routes.py            # /server/restart
│
├── executors/                   # 🤖 Robot Execution
│   ├── runner.py                # Runner class (RobotFramework execution)
│   ├── server.py                # Server class (orchestrator)
│   ├── tasks.py                 # Celery tasks (run_robot_task)
│   └── process_manager.py       # Process control (pause/resume/stop)
│
├── streaming/                   # 📹 Video Streaming
│   ├── streamer.py              # ScreenStreamer class (capture)
│   ├── tasks.py                 # Celery tasks (start_streaming_task)
│   └── capture.py               # Capture utilities (mss, PIL)
│
├── shared/                      # 🔧 Shared/Common
│   ├── config/                  # Configuration management
│   │   ├── loader.py            # get_config_data, write_config
│   │   └── cli.py               # CLI args parsing
│   │
│   ├── state/                   # State management
│   │   ├── redis_client.py      # Redis singleton client
│   │   ├── redis_manager.py     # Redis lifecycle
│   │   └── redis_state.py       # State operations
│   │
│   ├── celery_app/              # Celery configuration
│   │   ├── config.py            # Celery app config
│   │   └── worker.py            # Worker thread management
│   │
│   └── utils/                   # Utilities
│       ├── process.py           # Process management (kill_process)
│       ├── ssl_utils.py         # SSL/TLS helpers
│       └── tunnel.py            # Tunnel utilities
│
├── cli/                         # 💻 CLI Entry Points
│   ├── run_server.py            # Server entry point
│   └── run_tray.py              # Tray app entry point
│
├── gui/                         # 🖼️ GUI
│   └── tray_app.py              # System tray application
│
├── tests/                       # 🧪 Tests
│   ├── conftest.py              # Shared fixtures
│   ├── unit/                    # Unit tests (43 tests)
│   ├── integration/             # Integration tests (15+ tests)
│   └── manual/                  # Manual tests (debugging)
│
├── templates/                   # 📄 HTML Templates (Flask)
├── static/                      # 🎨 Static Assets (CSS, JS, images)
├── ssl/                         # 🔒 SSL Certificates
│
├── run.py                       # 🚀 Main entry point (delegator)
├── gunicorn_config.py           # ⚙️ Gunicorn configuration
├── app.spec                     # 📦 PyInstaller spec
└── config.json                  # ⚙️ Runtime configuration
```

---

## Capas Arquitectónicas

### 1. API Layer (`api/`)
**Responsabilidad**: Interfaz externa, autenticación, routing

- **Flask Blueprints**: Organización modular por dominio
- **Authentication**: 3 decoradores (@require_token, @require_auth, @require_auth_sse)
- **Middleware**: Logging, lazy server initialization
- **Factory Pattern**: `create_app()` para testabilidad

**Tecnologías**: Flask, Flask Blueprints, Gunicorn

### 2. Business Logic Layer (`executors/`, `streaming/`)
**Responsabilidad**: Lógica de negocio core

- **Executors**: Ejecución de robots con RobotFramework
- **Streaming**: Captura y transmisión de video
- **Async Tasks**: Celery para operaciones de larga duración

**Tecnologías**: RobotFramework, MSS, PIL, Celery

### 3. Shared Layer (`shared/`)
**Responsabilidad**: Código común reutilizable

- **Config**: Gestión centralizada de configuración
- **State**: Redis como fuente única de verdad
- **Celery**: Worker management
- **Utils**: Funciones de utilidad cross-cutting

**Tecnologías**: Redis, Celery, PyYAML

### 4. Infrastructure Layer
**Responsabilidad**: Servicios externos y persistencia

- **Redis**: Estado distribuido (executions, streaming)
- **Celery**: Cola de tareas async
- **Filesystem**: Logs, certificados SSL, configs

**Tecnologías**: Redis, Celery, OS filesystem

---

## Patrones de Diseño

### 1. Application Factory Pattern
```python
# api/app.py
def create_app(config=None):
    app = Flask(__name__)
    configure_flask(app, config)
    register_middleware(app)
    register_blueprints(app)
    return app
```

**Beneficios**:
- Testabilidad (configs inyectables)
- Multiple instances con diferentes configs
- Lazy initialization

### 2. Blueprint Pattern
```python
# api/rest/status.py
rest_status_bp = Blueprint('rest_status', __name__)

@rest_status_bp.route('/status', methods=['GET'])
@require_token
def get_robot_status():
    # ...
```

**Beneficios**:
- Modularidad por dominio
- Código organizado
- Rutas prefijadas

### 3. Singleton Pattern (Redis Client)
```python
# shared/state/redis_client.py
_redis_client = None

def get_redis_client():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(...)
    return _redis_client
```

**Beneficios**:
- Una sola conexión Redis
- Thread-safe
- Lazy initialization

### 4. Decorator Pattern (Authentication)
```python
# api/auth.py
def require_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Validate token
        return f(*args, **kwargs)
    return decorated_function
```

**Beneficios**:
- Separation of concerns
- Reusabilidad
- Code composition

---

## Flujo de Requests

### 1. Request HTTP → API Layer
```
Cliente → HTTPS → Gunicorn → Flask → Blueprint → Handler
```

### 2. Authentication
```
Handler → @require_token → Validate token → Allow/Deny
```

### 3. Business Logic
```
Handler → Server/Runner → Celery Task → Redis State → Response
```

### 4. Response
```
Response → Middleware (logging) → Client
```

---

## Gestión de Estado

### Redis como Fuente Única de Verdad

```python
# Execution state
redis_state.save_execution_state({
    'execution_id': 'exec-123',
    'status': 'running',
    'task_id': 'celery-task-456'
})

# Streaming state
redis_state.set_streaming_status({
    'active': True,
    'fps': 10,
    'quality': 70
})

# Server status
redis_state.set_server_status('running')
```

**Beneficios**:
- Estado compartido entre workers de Gunicorn
- Persistencia entre reinicios
- Detección de executions huérfanas

---

## Escalabilidad

### Horizontal Scaling
- **Gunicorn Workers**: Múltiples procesos paralelos
- **Celery Workers**: Distribución de tareas
- **Redis**: Estado compartido centralizado

### Vertical Scaling
- **Async I/O**: Celery para operaciones bloqueantes
- **Process Pooling**: Gunicorn process management
- **Connection Pooling**: Redis connection pool

---

## Seguridad

### 1. Transport Layer
- **HTTPS**: SSL/TLS certificates
- **Certificate Authority**: Custom CA para robots

### 2. Authentication Layer
- **Token Authentication**: Bearer token en headers
- **Machine Validation**: machine_id + license_key
- **Session Management**: Flask sessions para web UI

### 3. Authorization Layer
- **Decorators**: @require_token, @require_auth
- **Role-based**: Web UI vs API access

---

## Observabilidad

### Logging
```python
# Structured logging
logger.info(f"[EXEC:{execution_id}] Robot started", extra={
    'execution_id': execution_id,
    'robot_file': robot_file
})
```

### Monitoring
- **Request Logs**: Middleware logging a `request_log.txt`
- **Server Logs**: Application logs a `logs/server.log`
- **Redis State**: Estado persistente consultable

### Debugging
- **Test Suite**: 171 tests (unit + integration)
- **Manual Tests**: Scripts en `tests/manual/`
- **Coverage**: >70% cobertura de código

---

## Tecnologías Clave

| Capa | Tecnología | Propósito |
|------|------------|-----------|
| **Web Framework** | Flask 2.3+ | HTTP server, routing, templating |
| **WSGI Server** | Gunicorn | Production-grade server |
| **Task Queue** | Celery 5.3+ | Async task execution |
| **Message Broker** | Redis 5.0+ | Task queue + state storage |
| **Automation** | RobotFramework | Robot execution engine |
| **Streaming** | MSS + PIL | Screen capture |
| **SSL/TLS** | OpenSSL | Certificate management |
| **Tunnel** | Cloudflare | Secure external access |
| **Testing** | pytest | Test framework |
| **Packaging** | PyInstaller | Executable creation |

---

## Próximos Pasos

- Leer [Componentes](components.md) para detalles de cada módulo
- Revisar [Flujo de Datos](data-flow.md) para escenarios específicos
- Consultar [Diagramas](diagrams/) para visualizaciones

---

**Actualizado**: 2026-01-08
**Versión**: 2.0.0
