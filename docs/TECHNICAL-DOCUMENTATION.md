# 📘 Documentación Técnica - Robot Runner

## Índice

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Componentes Principales](#componentes-principales)
4. [Stack Tecnológico](#stack-tecnológico)
5. [Flujos de Datos](#flujos-de-datos)
6. [Sistema de Seguridad SSL/TLS](#sistema-de-seguridad-ssltls)
7. [API REST](#api-rest)
8. [Gestión de Estado](#gestión-de-estado)
9. [Concurrencia y Asincronía](#concurrencia-y-asincronía)
10. [Empaquetado y Distribución](#empaquetado-y-distribución)
11. [Consideraciones de Despliegue](#consideraciones-de-despliegue)

---

## 1. Resumen Ejecutivo

**Robot Runner** es una aplicación servidor-cliente que permite ejecutar y controlar robots de automatización (scripts) de forma remota a través de una API REST, con una interfaz gráfica integrada.

### Características Clave

- ✅ **API REST** para control remoto
- ✅ **Interfaz gráfica** nativa con webview
- ✅ **HTTPS** con Certificate Authority (CA) propia
- ✅ **Autenticación** basada en credenciales
- ✅ **Ejecución asíncrona** sin bloquear el servidor
- ✅ **Multiplataforma** (Windows, macOS, Linux)

### Métricas

| Métrica | Valor |
|---------|-------|
| Versión | 2.0 |
| Lenguaje | Python 3.12+ |
| Endpoints API | 9 |
| Workers Gunicorn | 4 |
| Threads por Worker | 2 |
| Capacidad concurrente | ~16 requests simultáneos |
| Puerto por defecto | 5055 (HTTPS) |

---

## 2. Arquitectura del Sistema

### 2.1 Arquitectura General

```
┌─────────────────────────────────────────────────────────────┐
│                     Robot Runner                             │
│                                                              │
│  ┌────────────────┐         ┌─────────────────────────┐    │
│  │                │         │                         │    │
│  │   Webview GUI  │◄────────┤  Gunicorn WSGI Server   │    │
│  │   (Frontend)   │ HTTPS   │  (Backend)              │    │
│  │                │         │                         │    │
│  └────────────────┘         │  ┌──────────────────┐   │    │
│                             │  │   Flask App      │   │    │
│                             │  │   (Routes)       │   │    │
│                             │  └────────┬─────────┘   │    │
│                             │           │             │    │
│                             │  ┌────────▼─────────┐   │    │
│                             │  │  Server Class    │   │    │
│                             │  │  (Business Logic)│   │    │
│                             │  └──────────────────┘   │    │
│                             └─────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTPS API
                                    │
                          ┌─────────▼────────┐
                          │                  │
                          │   Orchestrator   │
                          │   (Remote)       │
                          │                  │
                          └──────────────────┘
```

### 2.2 Arquitectura de Procesos

```
┌─────────────────────────────────────────────────────────┐
│  Proceso Principal (GUI Mode)                           │
│                                                          │
│  1. python app.py                                       │
│     │                                                    │
│     ├─► subprocess.Popen()                              │
│     │   └─► python app.py --server-only                │
│     │       └─► Gunicorn (Main Thread)                  │
│     │           ├─► Worker 1 (Process)                  │
│     │           │   ├─► Thread 1                        │
│     │           │   └─► Thread 2                        │
│     │           ├─► Worker 2 (Process)                  │
│     │           │   ├─► Thread 1                        │
│     │           │   └─► Thread 2                        │
│     │           ├─► Worker 3 (Process)                  │
│     │           │   ├─► Thread 1                        │
│     │           │   └─► Thread 2                        │
│     │           └─► Worker 4 (Process)                  │
│     │               ├─► Thread 1                        │
│     │               └─► Thread 2                        │
│     │                                                    │
│     └─► webview.start() (Main Thread)                   │
│         └─► Chromium/WebKit Engine                      │
│             └─► Muestra interfaz Flask                  │
│                                                          │
└──────────────────────────────────────────────────────────┘

Total de threads potenciales: 8 (4 workers × 2 threads)
```

### 2.3 Flujo de Inicio (Modo GUI)

```
1. main() ejecuta
   │
   ├─► Configurar entorno (macOS fork safety)
   │
   ├─► Parsear argumentos CLI
   │
   ├─► Cargar config.json
   │
   ├─► Inicializar Server(config)
   │
   ├─► subprocess.Popen([python, app.py, --server-only])
   │   └─► Gunicorn inicia en proceso hijo
   │       └─► Workers escuchan en 0.0.0.0:5055
   │
   ├─► wait_for_server() - Polling hasta que responda
   │
   ├─► webview.create_window(url=https://127.0.0.1:5055)
   │
   ├─► webview.start() - Bloquea hasta que se cierre
   │
   └─► server_process.terminate() - Limpieza
```

---

## 3. Componentes Principales

### 3.1 Flask Application (app.py)

**Responsabilidad:** Framework web que maneja requests HTTP y routing.

**Componentes:**
- `app = flask.Flask(__name__)`
- Endpoints API (`/status`, `/run`, `/stop`, etc.)
- Endpoints UI (`/`, `/connect`, `/connected`)
- Configuración y middleware

**Configuración:**
```python
app.config = {
    'UPLOAD_FOLDER': 'uploads',
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024  # 16 MB
}
```

### 3.2 Gunicorn WSGI Server

**Responsabilidad:** Servidor HTTP de producción con soporte SSL y concurrencia.

**Características:**
- **Workers:** 4 procesos independientes
- **Threads:** 2 threads por worker
- **Worker Class:** `gthread` (green threads)
- **SSL:** Certificados propios (cert.pem, key.pem)
- **Timeout:** 120 segundos

**Configuración:**
```python
options = {
    'bind': '0.0.0.0:5055',
    'workers': 4,
    'threads': 2,
    'certfile': 'cert.pem',
    'keyfile': 'key.pem',
    'worker_class': 'gthread',
    'timeout': 120
}
```

**¿Por qué Gunicorn?**
- ✅ Robusto y probado en producción
- ✅ Soporte nativo para SSL
- ✅ Manejo de múltiples requests concurrentes
- ✅ Aislamiento de workers (fault tolerance)
- ✅ Compatible con Flask WSGI

### 3.3 Server Class (server.py)

**Responsabilidad:** Lógica de negocio, ejecución de robots y gestión de estado.

**Atributos principales:**
```python
class Server:
    - url: str              # URL del orquestador
    - token: str            # Token de autenticación
    - machine_id: str       # ID de la máquina
    - license_key: str      # License key
    - port: int             # Puerto del servidor
    - status: str           # Estado actual ('free', 'running', etc.)
    - run_robot_process     # Proceso del robot en ejecución
    - execution_id: str     # ID de la ejecución actual
```

**Métodos principales:**
```python
- run(data)           # Ejecuta un robot
- stop()              # Detiene la ejecución
- pause()             # Pausa la ejecución
- resume()            # Reanuda la ejecución
- send_log(message)   # Envía logs al orquestador
- clean_url(url)      # Normaliza URLs
```

### 3.4 Webview GUI

**Responsabilidad:** Interfaz gráfica nativa que muestra la UI web.

**Motor:**
- **Windows:** Edge (Chromium)
- **macOS:** WebKit
- **Linux:** GTK WebKit2

**Características:**
```python
window = webview.create_window(
    title='Robot Runner',
    url='https://127.0.0.1:5055/',
    width=1024,
    height=768
)
webview.start()
```

**Ventajas:**
- ✅ Nativo (no requiere navegador externo)
- ✅ Menor consumo de recursos que Electron
- ✅ Mejor integración con el SO
- ✅ Más ligero

### 3.5 ThreadPoolExecutor

**Responsabilidad:** Ejecutar tareas de robot de forma asíncrona.

**Configuración:**
```python
executor = ThreadPoolExecutor(max_workers=4)
```

**Uso:**
```python
# No bloqueante
executor.submit(server.run, data)
```

**Beneficios:**
- ✅ No bloquea el servidor HTTP
- ✅ Permite responder a otros requests mientras el robot corre
- ✅ Manejo automático de threads

---

## 4. Stack Tecnológico

### 4.1 Backend

| Componente | Tecnología | Versión | Propósito |
|------------|------------|---------|-----------|
| **Runtime** | Python | 3.12+ | Lenguaje principal |
| **Web Framework** | Flask | 3.0.0 | Routing y requests |
| **WSGI Server** | Gunicorn | 23.0.0 | Servidor de producción |
| **HTTP Client** | Requests | 2.32.2 | Peticiones HTTP |
| **Process Executor** | ThreadPoolExecutor | stdlib | Ejecución asíncrona |

### 4.2 Frontend

| Componente | Tecnología | Versión | Propósito |
|------------|------------|---------|-----------|
| **GUI Framework** | pywebview | 5.2 | Ventana nativa |
| **Template Engine** | Jinja2 | 3.1.4 | Templates HTML |
| **Static Files** | HTML/CSS/JS | - | Interfaz web |

### 4.3 Seguridad

| Componente | Tecnología | Propósito |
|------------|------------|-----------|
| **SSL/TLS** | OpenSSL | Cifrado HTTPS |
| **Certificados** | CA propia | Autenticación |
| **Hash** | SHA256 | Firmas digitales |
| **Encryption** | RSA 4096 | Clave CA |
| **Encryption** | RSA 2048 | Claves robots |

### 4.4 Empaquetado

| Componente | Tecnología | Versión | Propósito |
|------------|------------|---------|-----------|
| **Bundler** | PyInstaller | 6.10.0 | Ejecutables |
| **Compression** | UPX | - | Compresión binarios |

---

## 5. Flujos de Datos

### 5.1 Flujo: Ejecutar Robot

```
1. Orquestador
   │
   ├─► POST https://robot:5055/run
   │   Headers: Content-Type: application/json
   │   Body: {
   │     "robot_file": "mi_robot.robot",
   │     "params": {...}
   │   }
   │
   ▼
2. Gunicorn Worker (SSL Handshake)
   │
   ├─► Valida certificado del orquestador
   │
   ▼
3. Flask Route: /run
   │
   ├─► Parsea JSON
   │
   ├─► executor.submit(server.run, data)
   │   │
   │   └─► Thread Pool
   │       │
   │       └─► server.run(data)
   │           ├─► Inicia proceso del robot
   │           ├─► server.status = 'running'
   │           └─► server.execution_id = uuid()
   │
   ├─► Retorna inmediatamente:
   │   Response: {"message": "running"}
   │   Status: 200
   │
   ▼
4. Robot ejecutándose en background
   │
   ├─► Logs enviados a orquestador (server.send_log)
   │
   └─► Al terminar: server.status = 'free'
```

### 5.2 Flujo: Verificar Estado

```
1. Orquestador
   │
   ├─► GET https://robot:5055/status?machine_id=XXX&license_key=YYY
   │
   ▼
2. Gunicorn Worker
   │
   ▼
3. Flask Route: /status
   │
   ├─► Valida credenciales:
   │   if machine_id != server.machine_id or
   │      license_key != server.license_key:
   │       return "closed"
   │
   ├─► Verifica proceso:
   │   if server.run_robot_process:
   │       if process.poll() is not None:
   │           status = "free"  # Terminado
   │       else:
   │           status = "running"  # Activo
   │   else:
   │       status = "free"  # Sin proceso
   │
   └─► Response: "free" | "running" | "blocked" | "closed"
```

### 5.3 Flujo: Configuración Inicial (GUI)

```
1. Usuario abre app
   │
   ▼
2. GET /
   │
   └─► Redirect a /connect (primera vez)
   │   o
   └─► Redirect a /connected (ya configurado)
   │
   ▼
3. /connect (GET)
   │
   ├─► Carga config.json
   │
   └─► Renderiza form.html con valores actuales
   │
   ▼
4. Usuario llena formulario
   │
   ▼
5. /connect (POST)
   │
   ├─► Valida credenciales
   │
   ├─► Actualiza server.url, server.token, etc.
   │
   ├─► write_to_config(data) → Guarda en config.json
   │
   └─► Redirect a /connected
```

---

## 6. Sistema de Seguridad SSL/TLS

### 6.1 Arquitectura de Certificate Authority (CA)

```
┌──────────────────────────────────────────────────────┐
│             Certificate Authority Propia             │
│                                                      │
│  ┌────────────────┐                                 │
│  │   ca-key.pem   │  ← Clave privada (4096 RSA)    │
│  │   (SECRETO)    │     Nunca compartir             │
│  └────────┬───────┘                                 │
│           │                                          │
│           │ Firma certificados                       │
│           │                                          │
│  ┌────────▼───────┐                                 │
│  │  ca-cert.pem   │  ← Certificado público         │
│  │  (COMPARTIR)   │     Instalar en orquestador    │
│  └────────────────┘                                 │
└──────────────────────────────────────────────────────┘
           │
           │ Firma cada robot
           │
    ┌──────┴──────┬──────────┬──────────┐
    ▼             ▼          ▼          ▼
┌─────────┐ ┌──────────┐ ┌────────┐ ┌────────┐
│ Robot 1 │ │ Robot 2  │ │Robot 3 │ │Robot N │
│cert.pem │ │ cert.pem │ │cert    │ │cert    │
│key.pem  │ │ key.pem  │ │key     │ │key     │
│IP:.100  │ │ IP:.200  │ │IP:.50  │ │IP:...  │
└─────────┘ └──────────┘ └────────┘ └────────┘

┌───────────────────────────────────────────┐
│         Orquestador                       │
│  verify='/opt/certs/robot-ca.pem'        │
│  → Confía en TODOS los robots firmados   │
└───────────────────────────────────────────┘
```

### 6.2 Proceso de Validación SSL

```
1. Orquestador conecta a Robot (192.168.1.100:5055)
   │
   ├─► TCP Handshake
   │
   ├─► TLS ClientHello
   │
   ▼
2. Robot envía certificado (cert.pem)
   │
   └─► Contiene:
       - Subject: robot-1
       - Issuer: Robot Runner Root CA
       - Public Key: [clave pública del robot]
       - SAN: IP:192.168.1.100, localhost
       - Signature: [firmado con ca-key.pem]
   │
   ▼
3. Orquestador valida certificado
   │
   ├─► Lee Issuer: "Robot Runner Root CA"
   │
   ├─► Busca ca-cert.pem (configurado con verify=)
   │
   ├─► Extrae clave pública de ca-cert.pem
   │
   ├─► Verifica firma del certificado:
   │   a) Descifra firma con clave pública CA
   │   b) Calcula hash SHA256 del certificado
   │   c) Compara: ¿hash coincide?
   │       ✅ Sí → Certificado válido
   │       ❌ No → SSLError
   │
   ├─► Verifica fecha de validez
   │
   ├─► Verifica que IP coincide con SAN
   │
   └─► ✅ Todas las validaciones OK
   │
   ▼
4. Intercambio de claves (Key Exchange)
   │
   └─► Generan clave de sesión simétrica (AES)
   │
   ▼
5. Comunicación cifrada establecida
   │
   └─► Todo el tráfico va cifrado con AES-256
```

### 6.3 Ventajas del Sistema CA

| Aspecto | Certificado Compartido | CA Propia |
|---------|------------------------|-----------|
| **Escalabilidad** | ❌ Limitado por IPs en SAN | ✅ Infinitos robots |
| **Mantenimiento** | ❌ Regenerar y redistribuir | ✅ Solo regenerar robot |
| **Seguridad** | ⚠️ Misma clave compartida | ✅ Clave única por robot |
| **Orquestador** | ❌ Actualizar con cada robot | ✅ Configurar una vez |
| **IP Dinámica** | ❌ Regenerar todo | ✅ Solo regenerar robot |

---

## 7. API REST

### 7.1 Endpoints de Control

#### `GET /status`

**Descripción:** Obtiene el estado actual del robot.

**Query Parameters:**
- `machine_id` (string, required): ID de la máquina
- `license_key` (string, required): License key

**Respuesta:**
```json
"free"      // Disponible
"running"   // Ejecutando tarea
"blocked"   // Bloqueado manualmente
"closed"    // Credenciales inválidas
```

**Códigos de Estado:**
- `200 OK`: Siempre

**Ejemplo:**
```bash
curl -k "https://192.168.1.100:5055/status?machine_id=ABC&license_key=XYZ"
```

#### `POST /run`

**Descripción:** Ejecuta un robot.

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "robot_file": "mi_robot.robot",
  "params": {
    "env": "production",
    "timeout": 3600
  }
}
```

**Respuesta:**
```json
{
  "message": "running"
}
```

**Códigos de Estado:**
- `200 OK`: Tarea iniciada
- `400 Bad Request`: Error al iniciar

**Ejemplo:**
```bash
curl -k -X POST https://192.168.1.100:5055/run \
  -H "Content-Type: application/json" \
  -d '{
    "robot_file": "test.robot",
    "params": {}
  }'
```

#### `GET /stop`

**Descripción:** Detiene la ejecución actual.

**Respuesta:**
```json
{
  "message": "OK"
}
```

**Códigos de Estado:**
- `200 OK`: Siempre

#### `GET /execution`

**Descripción:** Consulta estado de una ejecución específica.

**Query Parameters:**
- `id` (string, required): ID de la ejecución

**Respuesta:**
```json
{
  "status": "working"  // o "fail", "pending"
}
```

#### `GET /block`

**Descripción:** Bloquea el robot manualmente.

**Respuesta:**
```json
{
  "message": "blocked"
}
```

**Códigos de Estado:**
- `300`: Success (código personalizado)

#### `GET /pause`

**Descripción:** Pausa la ejecución actual.

**Nota:** Depende de la implementación del robot.

#### `GET /resume`

**Descripción:** Reanuda la ejecución pausada.

### 7.2 Endpoints de UI

#### `GET /`

**Descripción:** Página de inicio (redirige).

#### `GET /connect`

**Descripción:** Formulario de configuración.

#### `POST /connect`

**Descripción:** Guarda configuración.

#### `GET /connected`

**Descripción:** Dashboard principal.

#### `POST /connected`

**Descripción:** Desconecta el robot.

---

## 8. Gestión de Estado

### 8.1 Estados del Robot

```
┌──────────┐
│   free   │  ← Estado inicial
└────┬─────┘
     │
     │ POST /run
     ▼
┌──────────┐
│ running  │  ← Ejecutando tarea
└────┬─────┘
     │
     │ Tarea termina / GET /stop
     ▼
┌──────────┐
│   free   │
└──────────┘

     │ GET /block
     ▼
┌──────────┐
│ blocked  │  ← Bloqueado manualmente
└──────────┘

Credenciales inválidas:
┌──────────┐
│  closed  │  ← Sin autenticación
└──────────┘
```

### 8.2 Transiciones de Estado

| Estado Actual | Acción | Estado Nuevo |
|---------------|--------|--------------|
| `free` | POST /run | `running` |
| `running` | Tarea termina | `free` |
| `running` | GET /stop | `free` |
| `free` | GET /block | `blocked` |
| `blocked` | POST /run | `running` |
| `*` | Credenciales inválidas | `closed` |

### 8.3 Persistencia

**Configuración (`config.json`):**
```json
{
  "url": "https://console.example.com",
  "token": "abc123",
  "machine_id": "MACHINE001",
  "license_key": "LICENSE001",
  "ip": "192.168.1.100",
  "port": "5055"
}
```

**Estado en memoria:**
- `server.status`: Estado actual del robot
- `server.run_robot_process`: Proceso en ejecución
- `server.execution_id`: ID de la ejecución actual

---

## 9. Concurrencia y Asincronía

### 9.1 Modelo de Concurrencia

```
┌─────────────────────────────────────────────────────┐
│  Gunicorn Master Process                            │
│                                                      │
│  ┌────────────────┐  ┌────────────────┐            │
│  │   Worker 1     │  │   Worker 2     │            │
│  │   (Process)    │  │   (Process)    │            │
│  │                │  │                │            │
│  │ ┌────┐ ┌────┐ │  │ ┌────┐ ┌────┐ │            │
│  │ │ T1 │ │ T2 │ │  │ │ T1 │ │ T2 │ │            │
│  │ └────┘ └────┘ │  │ └────┘ └────┘ │            │
│  └────────────────┘  └────────────────┘            │
│                                                      │
│  ┌────────────────┐  ┌────────────────┐            │
│  │   Worker 3     │  │   Worker 4     │            │
│  │   (Process)    │  │   (Process)    │            │
│  │                │  │                │            │
│  │ ┌────┐ ┌────┐ │  │ ┌────┐ ┌────┐ │            │
│  │ │ T1 │ │ T2 │ │  │ │ T1 │ │ T2 │ │            │
│  │ └────┘ └────┘ │  │ └────┘ └────┘ │            │
│  └────────────────┘  └────────────────┘            │
│                                                      │
└─────────────────────────────────────────────────────┘

Request 1 ──► Worker 1, Thread 1
Request 2 ──► Worker 1, Thread 2
Request 3 ──► Worker 2, Thread 1
...
Request 8 ──► Worker 4, Thread 2
Request 9 ──► Cola (espera a que se libere un thread)
```

### 9.2 ThreadPoolExecutor

**Propósito:** Ejecutar robots sin bloquear el servidor HTTP.

```python
# Configuración
executor = ThreadPoolExecutor(max_workers=4)

# Uso
@app.route('/run', methods=['POST'])
def run_robot():
    data = request.json

    # No bloqueante - retorna inmediatamente
    executor.submit(server.run, data)

    return jsonify({"message": "running"})
```

**Capacidad:**
- **Gunicorn:** 8 threads (4 workers × 2 threads)
- **ThreadPoolExecutor:** 4 workers adicionales
- **Total:** 12 threads concurrentes

### 9.3 Consideraciones de Thread Safety

**Thread-Safe:**
- ✅ Flask request context (thread-local)
- ✅ Lectura de configuración
- ✅ Estado de server (con cuidado)

**NO Thread-Safe:**
- ❌ Modificación concurrente de server.status
- ❌ Escritura simultánea a config.json

**Mitigación:**
```python
# Usar locks para modificaciones críticas
import threading

lock = threading.Lock()

def update_status(new_status):
    with lock:
        server.status = new_status
```

---

## 10. Empaquetado y Distribución

### 10.1 PyInstaller

**Archivo de configuración (`app.spec`):**
```python
a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('config.json', '.'),
        ('Robots', 'Robots'),
        ('cert.pem', '.'),
        ('key.pem', '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='RobotRunner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='logo.ico',
)
```

**Comando de compilación:**
```bash
pyinstaller app.spec
```

**Resultado:**
```
dist/
├── RobotRunner/           # Directorio (Linux/macOS)
│   ├── RobotRunner        # Ejecutable
│   ├── cert.pem           # Certificados incluidos
│   ├── key.pem
│   ├── templates/
│   └── static/
│
└── RobotRunner.exe        # Windows (single file optional)
```

### 10.2 Recursos Empaquetados

**Función `get_resource_path()`:**
```python
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller extrae recursos aquí
        return os.path.join(sys._MEIPASS, relative_path)
    # Desarrollo
    return os.path.join(os.path.abspath("."), relative_path)
```

**Uso:**
```python
cert_path = get_resource_path('cert.pem')
# Desarrollo: /path/to/project/cert.pem
# Ejecutable: /tmp/_MEIxxxxxx/cert.pem
```

---

## 11. Consideraciones de Despliegue

### 11.1 Requisitos del Sistema

**Mínimo:**
- CPU: 2 cores
- RAM: 2 GB
- Disco: 500 MB
- SO: Windows 10+, macOS 10.14+, Linux (Ubuntu 20.04+)

**Recomendado:**
- CPU: 4 cores
- RAM: 4 GB
- Disco: 1 GB
- SO: Windows 11, macOS 13+, Ubuntu 22.04+

### 11.2 Puertos

| Puerto | Protocolo | Propósito |
|--------|-----------|-----------|
| 5055 | HTTPS | API y GUI (por defecto) |

**Configuración de firewall:**
```bash
# Linux (ufw)
sudo ufw allow 5055/tcp

# Windows (PowerShell como Admin)
New-NetFirewallRule -DisplayName "Robot Runner" -Direction Inbound -LocalPort 5055 -Protocol TCP -Action Allow

# macOS
# No requiere configuración adicional para localhost
```

### 11.3 Certificados SSL

**Ubicación:**
- **Desarrollo:** Raíz del proyecto (`cert.pem`, `key.pem`)
- **Producción:** Empaquetados en ejecutable

**Renovación:**
```bash
# Regenerar certificado para un robot
./generate_robot_cert.sh robot-1 192.168.1.100

# Reempaquetar
pyinstaller app.spec

# Redistribuir solo ese robot
```

### 11.4 Logs y Monitoreo

**Logs de Gunicorn:**
```
stdout/stderr del servidor
```

**Logs de aplicación:**
```python
# Usar el método send_log del servidor
server.send_log("Mensaje de log")
```

**Monitoreo de estado:**
```bash
# Verificar si el servidor responde
curl -k https://127.0.0.1:5055/status?machine_id=XXX&license_key=YYY

# Verificar certificados
./verify_certs.sh
```

### 11.5 Actualizaciones

**Proceso:**
1. Generar nueva versión
   ```bash
   pyinstaller app.spec
   ```

2. Detener instancia actual
   ```bash
   # GUI: Cerrar ventana
   # Servidor: Ctrl+C o kill PID
   ```

3. Reemplazar ejecutable

4. Iniciar nueva versión
   ```bash
   ./RobotRunner
   ```

**Notas:**
- La configuración (`config.json`) se preserva
- Los certificados se actualizan si regeneras `cert.pem`/`key.pem`
- Hacer backup de configuración antes de actualizar

### 11.6 Troubleshooting

**Problema: Puerto ocupado**
```bash
# Identificar proceso
lsof -i :5055  # Linux/macOS
netstat -ano | findstr :5055  # Windows

# Terminar proceso
kill -9 <PID>  # Linux/macOS
taskkill /PID <PID> /F  # Windows
```

**Problema: Certificado inválido**
```bash
# Verificar certificados
./verify_certs.sh

# Regenerar si es necesario
./generate_robot_cert.sh robot-1 <IP>
```

**Problema: GUI no abre**
```bash
# Verificar que webview está instalado
pip show pywebview

# Probar modo servidor solo
python app.py --server-only

# Acceder manualmente
open https://127.0.0.1:5055
```

---

## 12. Referencias

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [pywebview Documentation](https://pywebview.flowrl.com/)
- [PyInstaller Manual](https://pyinstaller.org/)
- [OpenSSL Documentation](https://www.openssl.org/docs/)

---

**Documento actualizado:** 2025-11-17
**Versión:** 2.0
**Mantenedor:** Robot Runner Team