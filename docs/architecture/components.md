# Componentes del Sistema - Robot Runner v2.0

Descripción detallada de cada componente de la arquitectura modular.

---

## Índice

1. [API Layer](#api-layer)
2. [Executors Layer](#executors-layer)
3. [Streaming Layer](#streaming-layer)
4. [Shared Layer](#shared-layer)
5. [CLI & GUI](#cli--gui)
6. [Infrastructure](#infrastructure)

---

## API Layer

### `api/app.py` - Application Factory

**Responsabilidad**: Crear y configurar la aplicación Flask

```python
def create_app(config=None):
    """
    Flask application factory.
    Returns configured Flask app with all blueprints registered.
    """
    app = Flask(__name__)
    configure_flask(app, config)
    register_middleware(app)
    register_blueprints(app)
    return app
```

**Funciones clave**:
- `create_app()`: Factory principal
- `configure_flask()`: Configuración de Flask (SECRET_KEY, TEMPLATES, etc.)
- `register_middleware()`: Registra before/after request hooks
- `register_blueprints()`: Registra todos los blueprints

**Dependencias**: `Flask`, `api.middleware`, blueprints

---

### `api/__init__.py` - Server Management

**Responsabilidad**: Gestión global de la instancia Server

```python
_server = None

def get_server():
    """Get the global server instance."""
    return _server

def set_server(server):
    """Set the global server instance."""
    global _server
    _server = server
```

**Uso**: Compartir instancia Server entre todos los blueprints

**Pattern**: Singleton (módulo-level)

---

### `api/auth.py` - Authentication Decorators

**Responsabilidad**: Decoradores de autenticación para endpoints

#### Decoradores

**1. `@require_token`** - API Authentication
```python
@require_token
def api_endpoint():
    # Solo accesible con Bearer token válido
```

- **Uso**: Endpoints de API REST
- **Validación**: Token en header `Authorization: Bearer <token>`
- **Response**: 401 (sin token), 403 (token inválido)

**2. `@require_auth`** - Hybrid Authentication
```python
@require_auth
def hybrid_endpoint():
    # Accesible con session O token
```

- **Uso**: Endpoints híbridos (web + API)
- **Validación**: Session cookie O Bearer token
- **Response**: Redirect a /login (web) o 401 (API)

**3. `@require_auth_sse`** - SSE Authentication
```python
@require_auth_sse
def sse_endpoint():
    # Autenticación para Server-Sent Events
```

- **Uso**: Endpoints de streaming SSE
- **Validación**: Session cookie O Bearer token
- **Response**: SSE error event (no redirect)

---

### `api/middleware.py` - Request Middleware

**Responsabilidad**: Logging, inicialización, hooks

#### Funciones

**1. `init_server_if_needed(app)`**
```python
def init_server_if_needed(app):
    """Initialize server instance on first request (lazy initialization)."""
    server = get_server()
    if server is None:
        config = get_config_data()
        server = Server(config)
        set_server(server)
        # Configure Redis
        redis_state.set_machine_id(config['machine_id'])
        redis_state.mark_orphaned_executions_as_failed()
        server.change_status("free", notify_remote=True)
    return server
```

**2. `log_request_to_file(request)`**
```python
def log_request_to_file(request):
    """Log request details to shared log file."""
    with open(REQUEST_LOG_FILE, 'a') as f:
        f.write(f"{timestamp} {request.method} {request.path}\n")
```

**3. Hooks**
- `@app.before_request`: Server initialization, auto-authentication
- `@app.after_request`: Request logging

---

### Blueprints

### `api/web/` - Web UI

#### `web/auth.py`
```python
web_auth_bp = Blueprint('web_auth', __name__)

@web_auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with token validation."""

@web_auth_bp.route('/logout')
def logout():
    """Logout and clear session."""
```

**Rutas**:
- `GET/POST /login`: Formulario de login con token
- `GET /logout`: Cerrar sesión

#### `web/ui.py`
```python
web_ui_bp = Blueprint('web_ui', __name__)

@web_ui_bp.route('/')
@require_auth
def index():
    """Home page."""

@web_ui_bp.route('/connected')
@require_auth
def connected():
    """Main control panel."""
```

**Rutas**:
- `GET /`: Home page (auto-login)
- `GET/POST /connect`: Connection wizard
- `GET/POST /connected`: Control panel

#### `web/settings.py`
```python
web_settings_bp = Blueprint('web_settings', __name__)

@web_settings_bp.route('/settings', methods=['GET', 'POST'])
@require_auth
def settings():
    """Settings page (edit config)."""
```

**Rutas**:
- `GET/POST /settings`: Configuración del servidor

---

### `api/rest/` - REST API

#### `rest/status.py`
```python
rest_status_bp = Blueprint('rest_status', __name__)

@rest_status_bp.route('/status', methods=['GET'])
@require_token
def get_robot_status():
    """Get robot status (free/running/blocked/closed)."""

@rest_status_bp.route('/execution', methods=['GET'])
@require_token
def get_execution_status():
    """Get execution status by ID."""
```

**Rutas**:
- `GET /status?machine_id=X&license_key=Y`: Estado del robot
- `GET /execution?id=X`: Estado de ejecución

#### `rest/execution.py`
```python
rest_execution_bp = Blueprint('rest_execution', __name__)

@rest_execution_bp.route('/run', methods=['POST'])
@require_token
def post_run():
    """Start robot execution (async via Celery)."""

@rest_execution_bp.route('/stop', methods=['GET'])
@require_token
def get_stop():
    """Stop running execution."""
```

**Rutas**:
- `POST /run`: Ejecutar robot (JSON body)
- `GET /stop?execution_id=X`: Detener ejecución
- `GET /pause?execution_id=X`: Pausar ejecución
- `GET /resume?execution_id=X`: Reanudar ejecución
- `GET /block`: Bloquear robot

#### `rest/info.py`
```python
rest_info_bp = Blueprint('rest_info', __name__)

@rest_info_bp.route('/api/server-info', methods=['GET'])
@require_auth
def get_server_info():
    """Get server information."""

@rest_info_bp.route('/api/logs', methods=['GET'])
@require_auth
def get_logs():
    """Get server logs."""
```

**Rutas**:
- `GET /api/server-info`: Info del servidor
- `GET /api/logs?lines=100`: Últimas N líneas de log

---

### `api/streaming/` - Video Streaming

#### `streaming/control.py`
```python
streaming_control_bp = Blueprint('streaming_control', __name__, url_prefix='/stream')

@streaming_control_bp.route('/start', methods=['POST'])
@require_token
def post_stream_start():
    """Start screen streaming (async via Celery)."""

@streaming_control_bp.route('/stop', methods=['POST'])
@require_token
def post_stream_stop():
    """Stop screen streaming."""
```

**Rutas**:
- `POST /stream/start`: Iniciar streaming (JSON: fps, quality)
- `POST /stream/stop`: Detener streaming
- `GET /stream/status`: Estado del streaming

#### `streaming/feed.py`
```python
streaming_feed_bp = Blueprint('streaming_feed', __name__, url_prefix='/stream')

@streaming_feed_bp.route('/feed')
@require_auth_sse
def stream_feed():
    """SSE endpoint for video frames."""
    def generate():
        streamer = ScreenStreamer(fps=10, quality=70)
        while True:
            frame_base64 = streamer.capture_frame()
            yield f"data: {frame_base64}\n\n"
    return Response(generate(), mimetype='text/event-stream')
```

**Rutas**:
- `GET /stream/feed`: Stream SSE de frames (base64-encoded JPEG)
- `GET /stream-view`: Página HTML viewer

---

### `api/tunnel/` - Cloudflare Tunnel

```python
tunnel_bp = Blueprint('tunnel', __name__, url_prefix='/tunnel')

@tunnel_bp.route('/start', methods=['POST'])
@require_token
def post_tunnel_start():
    """Start Cloudflare tunnel with subdomain."""

@tunnel_bp.route('/stop', methods=['POST'])
@require_token
def post_tunnel_stop():
    """Stop Cloudflare tunnel."""
```

**Rutas**:
- `POST /tunnel/start`: Iniciar tunnel (JSON: subdomain)
- `POST /tunnel/stop`: Detener tunnel
- `GET /tunnel/status`: Estado del tunnel

---

### `api/server/` - Server Management

```python
server_mgmt_bp = Blueprint('server_mgmt', __name__, url_prefix='/server')

@server_mgmt_bp.route('/restart', methods=['POST'])
@require_token
def post_server_restart():
    """Restart Gunicorn server (SIGHUP)."""
```

**Rutas**:
- `POST /server/restart`: Reiniciar servidor (graceful reload)

---

## Executors Layer

### `executors/runner.py` - Runner Class

**Responsabilidad**: Ejecutar robots con RobotFramework

```python
class Runner:
    def __init__(self, robot_file, params=None):
        self.robot_file = robot_file
        self.params = params or {}
        self.process = None

    def run(self):
        """Execute robot using subprocess."""
        cmd = self._build_command()
        self.process = subprocess.Popen(cmd, ...)
        return self.process

    def stop(self):
        """Stop running robot."""
        if self.process:
            self.process.terminate()
```

**Métodos**:
- `run()`: Ejecutar robot
- `stop()`: Detener robot
- `pause()`: Pausar (SIGSTOP)
- `resume()`: Reanudar (SIGCONT)

---

### `executors/server.py` - Server Class

**Responsabilidad**: Orquestar ejecuciones y gestionar estado

```python
class Server:
    def __init__(self, config):
        self.machine_id = config['machine_id']
        self.license_key = config['license_key']
        self.token = config['token']
        self.status = "free"  # free/running/blocked/closed
        self.run_robot_process = None
        self.execution_id = None

    def change_status(self, new_status, notify_remote=False):
        """Change server status and notify orquestador."""
        self.status = new_status
        redis_state.set_server_status(new_status)
        if notify_remote:
            # POST to orquestador
```

**Métodos**:
- `change_status()`: Cambiar estado
- `notify_orquestador()`: Notificar cambios
- `get_status()`: Obtener estado actual

---

### `executors/tasks.py` - Celery Tasks

**Responsabilidad**: Tareas asíncronas de ejecución

```python
@celery_app.task(bind=True)
def run_robot_task(self, robot_file, params, execution_id):
    """
    Execute robot in background.
    Updates Redis state throughout execution.
    """
    # Update state: running
    redis_state.save_execution_state({
        'execution_id': execution_id,
        'status': 'running',
        'task_id': self.request.id
    })

    # Run robot
    runner = Runner(robot_file, params)
    result = runner.run()

    # Update state: completed/failed
    redis_state.save_execution_state({
        'execution_id': execution_id,
        'status': 'completed' if result == 0 else 'failed'
    })

    return result
```

**Tasks**:
- `run_robot_task`: Ejecutar robot (async)

---

### `executors/process_manager.py` - Process Management

**Responsabilidad**: Control de procesos (pause/resume/stop)

```python
def pause_process(pid):
    """Pause process (SIGSTOP)."""
    os.kill(pid, signal.SIGSTOP)

def resume_process(pid):
    """Resume process (SIGCONT)."""
    os.kill(pid, signal.SIGCONT)

def kill_process(pid, force=False):
    """Kill process (SIGTERM or SIGKILL)."""
    signal_type = signal.SIGKILL if force else signal.SIGTERM
    os.kill(pid, signal_type)
```

---

## Streaming Layer

### `streaming/streamer.py` - ScreenStreamer Class

**Responsabilidad**: Capturar frames de pantalla

```python
class ScreenStreamer:
    def __init__(self, fps=10, quality=70):
        self.fps = fps
        self.quality = quality
        self.sct = mss.mss()

    def capture_frame(self):
        """Capture screenshot and return base64-encoded JPEG."""
        screenshot = self.sct.grab(self.sct.monitors[1])
        img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)

        # Compress to JPEG
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=self.quality)

        # Encode base64
        return base64.b64encode(buffer.getvalue()).decode()
```

**Métodos**:
- `capture_frame()`: Capturar y codificar frame
- `set_fps()`: Ajustar FPS
- `set_quality()`: Ajustar calidad JPEG

---

### `streaming/tasks.py` - Streaming Tasks

**Responsabilidad**: Tareas asíncronas de streaming

```python
@celery_app.task(bind=True)
def start_streaming_task(self, fps=10, quality=70):
    """
    Mark streaming as active in Redis.
    Actual streaming happens in /stream/feed endpoint.
    """
    redis_state.set_streaming_status({
        'active': True,
        'fps': fps,
        'quality': quality,
        'task_id': self.request.id
    })

    # Keep task alive while streaming is active
    while redis_state.get_streaming_status().get('active'):
        time.sleep(1)
```

**Tasks**:
- `start_streaming_task`: Iniciar streaming (async)

---

## Shared Layer

### `shared/config/loader.py` - Configuration

**Responsabilidad**: Gestión de configuración

```python
def get_config_data():
    """Load configuration from config.json."""
    with open('config.json', 'r') as f:
        return json.load(f)

def write_config(config_data):
    """Write configuration to config.json."""
    with open('config.json', 'w') as f:
        json.dump(config_data, f, indent=4)
```

**Funciones**:
- `get_config_data()`: Cargar config
- `write_config()`: Guardar config
- `validate_config()`: Validar estructura

---

### `shared/state/redis_state.py` - Redis State

**Responsabilidad**: Gestión de estado en Redis

```python
def save_execution_state(execution_data):
    """Save execution state to Redis."""
    redis_client.hset(
        f"execution:{execution_data['execution_id']}",
        mapping=execution_data
    )

def load_execution_state(execution_id):
    """Load execution state from Redis."""
    return redis_client.hgetall(f"execution:{execution_id}")

def set_server_status(status):
    """Set server status in Redis."""
    redis_client.set("server:status", status)

def mark_orphaned_executions_as_failed():
    """Mark executions from previous server instance as failed."""
    # Find executions with status=running
    # Update to status=failed
```

**Funciones**:
- `save_execution_state()`: Guardar estado de ejecución
- `load_execution_state()`: Cargar estado de ejecución
- `set_server_status()`: Actualizar estado del servidor
- `set_streaming_status()`: Actualizar estado de streaming
- `mark_orphaned_executions_as_failed()`: Cleanup de orphans

---

### `shared/celery_app/config.py` - Celery Config

**Responsabilidad**: Configuración de Celery

```python
celery_app = Celery('robotrunner')

celery_app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_send_sent_event=True,
)
```

---

### `shared/utils/process.py` - Process Utilities

**Responsabilidad**: Utilidades de gestión de procesos

```python
def find_gunicorn_processes():
    """Find Gunicorn process PIDs."""
    # Method 1: pgrep
    # Method 2: lsof (by port)
    return pids

def kill_process(pid, force=False):
    """Kill process (cross-platform)."""
    if platform.system() == 'Windows':
        # taskkill /PID {pid} /F
    else:
        # os.kill(pid, SIGTERM/SIGKILL)
```

---

## CLI & GUI

### `cli/run_server.py` - Server Entry Point

**Responsabilidad**: Entry point standalone del servidor

```python
def main():
    """Run Gunicorn server with embedded Celery workers."""
    # Verify Redis
    # Load config
    # Start Gunicorn
    # Hooks: start Celery workers
```

---

### `gui/tray_app.py` - System Tray

**Responsabilidad**: Aplicación de bandeja del sistema

```python
class TrayApp:
    def __init__(self):
        self.icon = self.create_icon()
        self.menu = self.create_menu()

    def start_server(self):
        """Start Gunicorn server."""

    def stop_server(self):
        """Stop Gunicorn server."""

    def run(self):
        """Run tray app."""
        self.icon.run()
```

---

## Infrastructure

### Redis
- **Puerto**: 6379
- **Uso**: State storage, Celery broker
- **Keys**:
  - `execution:{id}`: Estado de ejecución
  - `server:status`: Estado del servidor
  - `streaming:status`: Estado del streaming

### Celery
- **Broker**: Redis
- **Backend**: Redis
- **Workers**: Embedded en Gunicorn via hooks
- **Tasks**: `run_robot_task`, `start_streaming_task`

---

## Interacción entre Componentes

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│   API    │────▶│ Executors│────▶│  Redis   │
│ (Flask)  │     │ (Runner) │     │ (State)  │
└──────────┘     └──────────┘     └──────────┘
     │                │                  ▲
     │                ▼                  │
     │           ┌──────────┐           │
     │           │  Celery  │───────────┘
     │           │ (Tasks)  │
     │           └──────────┘
     │
     ▼
┌──────────┐
│  Shared  │
│ (Config) │
└──────────┘
```

---

**Próximos pasos**:
- Leer [Flujo de Datos](data-flow.md) para escenarios específicos
- Revisar [Diagramas](diagrams/) para visualizaciones

---

**Actualizado**: 2026-01-08
**Versión**: 2.0.0
