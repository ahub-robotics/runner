# REST API Documentation - Robot Runner v2.0

Documentación completa de la API REST de Robot Runner.

---

## Base URL

```
https://localhost:5001
```

Todos los endpoints requieren HTTPS con certificado SSL válido.

---

## Autenticación

Consulta [authentication.md](authentication.md) para detalles completos.

### Token Authentication

Todos los endpoints de API requieren un token de autenticación en el header:

```http
Authorization: Bearer <token>
```

El token se configura en `config.json` y debe mantenerse seguro.

---

## Endpoints

### Status & Monitoring

#### `GET /status`

Obtiene el estado actual del robot.

**Authentication**: Bearer Token

**Query Parameters**:
- `machine_id` (string, required): ID de la máquina
- `license_key` (string, required): Clave de licencia

**Response**:
```json
"free" | "running" | "blocked" | "closed"
```

**Estados**:
- `free`: Robot disponible para ejecuciones
- `running`: Robot ejecutando un proceso
- `blocked`: Robot bloqueado manualmente
- `closed`: Credenciales inválidas

**Example**:
```bash
curl -X GET "https://localhost:5001/status?machine_id=ROBOT-01&license_key=abc123" \
  -H "Authorization: Bearer your-token-here"
```

---

#### `GET /execution`

Obtiene el estado de una ejecución específica.

**Authentication**: Bearer Token

**Query Parameters**:
- `id` (string, required): ID de la ejecución

**Response**:
```json
{
  "status": "working" | "completed" | "fail" | "stopped",
  "execution_id": "exec-123",
  "task_id": "celery-task-456",
  "started_at": "2026-01-08T10:30:00Z",
  "completed_at": "2026-01-08T10:35:00Z"
}
```

**Example**:
```bash
curl -X GET "https://localhost:5001/execution?id=exec-123" \
  -H "Authorization: Bearer your-token-here"
```

---

### Robot Execution

#### `POST /run`

Inicia la ejecución de un robot.

**Authentication**: Bearer Token

**Content-Type**: `application/json`

**Request Body**:
```json
{
  "robot_file": "path/to/robot.robot",
  "params": {
    "env": "production",
    "variable1": "value1"
  },
  "execution_id": "exec-123"  // Optional, will be generated if not provided
}
```

**Response** (Success - 200):
```json
{
  "message": "running",
  "execution_id": "exec-123",
  "task_id": "celery-task-456",
  "status": "running"
}
```

**Response** (Error - 400):
```json
{
  "message": "No JSON data provided"
}
```

**Response** (Error - 409):
```json
{
  "message": "Robot is already running"
}
```

**Example**:
```bash
curl -X POST "https://localhost:5001/run" \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "robot_file": "tests/example.robot",
    "params": {"env": "test"},
    "execution_id": "exec-001"
  }'
```

---

#### `GET /stop`

Detiene una ejecución en curso.

**Authentication**: Bearer Token

**Query Parameters**:
- `execution_id` (string, required): ID de la ejecución a detener

**Response** (Success - 200):
```json
{
  "message": "OK",
  "execution_id": "exec-123",
  "status": "stopped"
}
```

**Response** (Error - 400):
```json
{
  "message": "execution_id mismatch or not found"
}
```

**Example**:
```bash
curl -X GET "https://localhost:5001/stop?execution_id=exec-123" \
  -H "Authorization: Bearer your-token-here"
```

---

#### `GET /pause`

Pausa una ejecución en curso (SIGSTOP).

**Authentication**: Bearer Token

**Query Parameters**:
- `execution_id` (string, required): ID de la ejecución a pausar

**Response**:
```json
{
  "message": "OK",
  "execution_id": "exec-123",
  "status": "paused"
}
```

**Example**:
```bash
curl -X GET "https://localhost:5001/pause?execution_id=exec-123" \
  -H "Authorization: Bearer your-token-here"
```

---

#### `GET /resume`

Reanuda una ejecución pausada (SIGCONT).

**Authentication**: Bearer Token

**Query Parameters**:
- `execution_id` (string, required): ID de la ejecución a reanudar

**Response**:
```json
{
  "message": "OK",
  "execution_id": "exec-123",
  "status": "running"
}
```

---

#### `GET /block`

Bloquea el robot para prevenir nuevas ejecuciones.

**Authentication**: Bearer Token

**Response**:
```json
{
  "message": "OK",
  "status": "blocked"
}
```

---

### Streaming

#### `POST /stream/start`

Inicia el streaming de video de la pantalla.

**Authentication**: Bearer Token

**Content-Type**: `application/json`

**Request Body**:
```json
{
  "fps": 10,        // Optional, default: 10
  "quality": 70     // Optional, default: 70 (JPEG quality 1-100)
}
```

**Response** (Success - 200):
```json
{
  "message": "Streaming started",
  "task_id": "celery-stream-456",
  "status": "active"
}
```

**Example**:
```bash
curl -X POST "https://localhost:5001/stream/start" \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{"fps": 15, "quality": 80}'
```

---

#### `POST /stream/stop`

Detiene el streaming de video.

**Authentication**: Bearer Token

**Response**:
```json
{
  "message": "Streaming stopped",
  "status": "inactive"
}
```

---

#### `GET /stream/status`

Obtiene el estado actual del streaming.

**Authentication**: Bearer Token

**Response**:
```json
{
  "active": true,
  "fps": 10,
  "quality": 70,
  "task_id": "celery-stream-456"
}
```

---

#### `GET /stream/feed`

Endpoint SSE (Server-Sent Events) para recibir frames de video.

**Authentication**: Bearer Token OR Session Cookie

**Content-Type**: `text/event-stream`

**Response**: Stream continuo de eventos SSE

```
data: /9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAIBA... (base64 JPEG)

data: /9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAIBA...

data: /9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAIBA...
```

**Example** (JavaScript):
```javascript
const eventSource = new EventSource('/stream/feed');

eventSource.onmessage = (event) => {
  const frameBase64 = event.data;
  const imgElement = document.getElementById('video-frame');
  imgElement.src = `data:image/jpeg;base64,${frameBase64}`;
};
```

---

### Tunnel Management

#### `POST /tunnel/start`

Inicia un túnel de Cloudflare.

**Authentication**: Bearer Token

**Content-Type**: `application/json`

**Request Body**:
```json
{
  "subdomain": "robot-01"
}
```

**Response**:
```json
{
  "message": "Tunnel started",
  "subdomain": "robot-01",
  "url": "https://robot-01.tunnel.example.com"
}
```

---

#### `POST /tunnel/stop`

Detiene el túnel de Cloudflare.

**Authentication**: Bearer Token

**Response**:
```json
{
  "message": "Tunnel stopped"
}
```

---

#### `GET /tunnel/status`

Obtiene el estado del túnel.

**Authentication**: Bearer Token

**Response**:
```json
{
  "active": true,
  "subdomain": "robot-01",
  "pid": 12345
}
```

---

### Server Management

#### `POST /server/restart`

Reinicia el servidor Gunicorn (graceful reload con SIGHUP).

**Authentication**: Bearer Token

**Response**:
```json
{
  "message": "Server restarting..."
}
```

**Note**: El servidor se reiniciará después de enviar la respuesta (delay de 2 segundos).

---

#### `GET /api/server-info`

Obtiene información del servidor.

**Authentication**: Session OR Bearer Token

**Response**:
```json
{
  "machine_id": "ROBOT-01",
  "status": "free",
  "version": "2.0.0",
  "port": 5001,
  "ssl_enabled": true,
  "uptime_seconds": 3600
}
```

---

#### `GET /api/logs`

Obtiene los últimos logs del servidor.

**Authentication**: Session OR Bearer Token

**Query Parameters**:
- `lines` (int, optional): Número de líneas a retornar (default: 100)

**Response**:
```json
{
  "success": true,
  "logs": [
    "[2026-01-08 10:30:00] Server started",
    "[2026-01-08 10:31:00] Execution exec-123 started",
    "[2026-01-08 10:35:00] Execution exec-123 completed"
  ],
  "total": 3
}
```

---

## Error Responses

### 401 Unauthorized
```json
{
  "error": "Token requerido"
}
```

### 403 Forbidden
```json
{
  "error": "Token inválido"
}
```

### 400 Bad Request
```json
{
  "message": "Execution ID mismatch or not found"
}
```

### 409 Conflict
```json
{
  "message": "Robot is already running"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "message": "Detailed error message"
}
```

---

## Rate Limiting

Actualmente no hay rate limiting implementado. Se recomienda implementar en producción.

---

## Webhooks

Robot Runner puede notificar al orquestador sobre cambios de estado via webhooks configurados en `config.json`:

```json
{
  "notify_url": "https://orquestador.com/webhook/robot-status",
  "notify_on_status_change": true
}
```

---

## SDK Examples

### Python

```python
import requests

BASE_URL = "https://localhost:5001"
TOKEN = "your-token-here"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Start execution
response = requests.post(
    f"{BASE_URL}/run",
    headers=headers,
    json={
        "robot_file": "test.robot",
        "params": {"env": "test"},
        "execution_id": "exec-001"
    },
    verify=False  # For self-signed certs
)

print(response.json())

# Check status
response = requests.get(
    f"{BASE_URL}/execution?id=exec-001",
    headers=headers,
    verify=False
)

print(response.json())
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');
const https = require('https');

const BASE_URL = 'https://localhost:5001';
const TOKEN = 'your-token-here';

const agent = new https.Agent({
  rejectUnauthorized: false // For self-signed certs
});

// Start execution
axios.post(`${BASE_URL}/run`, {
  robot_file: 'test.robot',
  params: { env: 'test' },
  execution_id: 'exec-001'
}, {
  headers: {
    'Authorization': `Bearer ${TOKEN}`
  },
  httpsAgent: agent
})
.then(response => console.log(response.data))
.catch(error => console.error(error));
```

---

## API Versioning

Actualmente la API está en **v2.0**. Cambios breaking se comunicarán con anticipación.

---

## Próximos Pasos

- Consultar [Authentication](authentication.md) para detalles de autenticación
- Ver [Endpoints Reference](endpoints.md) para especificación OpenAPI completa

---

**Actualizado**: 2026-01-08
**Versión**: 2.0.0
