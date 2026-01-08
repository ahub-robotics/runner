# Flujo de Datos - Robot Runner v2.0

Escenarios y diagramas de flujo de datos a través del sistema.

---

## Índice

1. [Flujo de Ejecución de Robot](#flujo-de-ejecución-de-robot)
2. [Flujo de Streaming de Video](#flujo-de-streaming-de-video)
3. [Flujo de Autenticación](#flujo-de-autenticación)
4. [Flujo de Estado (Redis)](#flujo-de-estado-redis)
5. [Flujo de Tunnel Management](#flujo-de-tunnel-management)

---

## Flujo de Ejecución de Robot

### Escenario: Orquestador ejecuta un robot remoto

```
┌────────────┐
│Orquestador │
└─────┬──────┘
      │ 1. POST /run
      │    {robot_file, params, execution_id}
      │    Authorization: Bearer <token>
      ↓
┌─────────────────────────────────────────┐
│           API Layer (Flask)              │
│  ┌────────────────────────────────────┐ │
│  │ api/rest/execution.py               │ │
│  │ @require_token                      │ │
│  └────────┬───────────────────────────┘ │
│           │ 2. Validate token           │
│           ↓                              │
│  ┌────────────────────────────────────┐ │
│  │ executors/tasks.py                  │ │
│  │ run_robot_task.delay()             │ │
│  └────────┬───────────────────────────┘ │
└───────────┼──────────────────────────────┘
            │ 3. Enqueue Celery task
            ↓
┌─────────────────────────────────────────┐
│         Infrastructure (Redis)           │
│  ┌────────────────────────────────────┐ │
│  │ Celery Queue                        │ │
│  │ Task: run_robot_task                │ │
│  │ Args: {robot_file, params, exec_id}│ │
│  └────────┬───────────────────────────┘ │
└───────────┼──────────────────────────────┘
            │ 4. Celery worker picks task
            ↓
┌─────────────────────────────────────────┐
│         Executors Layer                  │
│  ┌────────────────────────────────────┐ │
│  │ executors/tasks.py                  │ │
│  │ run_robot_task()                   │ │
│  └────────┬───────────────────────────┘ │
│           │ 5. Save state: running      │
│           ↓                              │
│  ┌────────────────────────────────────┐ │
│  │ Redis State                         │ │
│  │ execution:123 = {                   │ │
│  │   status: "running",                │ │
│  │   task_id: "celery-456"            │ │
│  │ }                                   │ │
│  └────────┬───────────────────────────┘ │
│           │                              │
│           ↓ 6. Execute robot            │
│  ┌────────────────────────────────────┐ │
│  │ executors/runner.py                 │ │
│  │ Runner.run()                       │ │
│  │   subprocess.Popen(robot_file)     │ │
│  └────────┬───────────────────────────┘ │
│           │ 7. Wait for completion      │
│           ↓                              │
│  ┌────────────────────────────────────┐ │
│  │ Redis State                         │ │
│  │ execution:123 = {                   │ │
│  │   status: "completed",              │ │
│  │   result_code: 0                    │ │
│  │ }                                   │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
            │ 8. Return to API
            ↓
┌─────────────┐
│Orquestador  │ 9. GET /execution?id=123
│ (Polling)   │    → {status: "completed"}
└─────────────┘
```

### Paso a Paso

1. **Request**: Orquestador envía POST /run con token
2. **Authentication**: `@require_token` valida el token
3. **Enqueue**: Celery task `run_robot_task` se encola
4. **Worker Picks**: Worker de Celery toma la tarea
5. **Save State**: Estado inicial se guarda en Redis (running)
6. **Execute**: `Runner` ejecuta el robot con subprocess
7. **Wait**: Se espera a que el proceso termine
8. **Update State**: Estado final se guarda en Redis (completed/failed)
9. **Poll**: Orquestador consulta estado via GET /execution

### Estados de Ejecución

```
[start] → running → completed ✓
                  → failed ✗
                  → stopped (manual)
```

---

## Flujo de Streaming de Video

### Escenario: Orquestador inicia streaming y consume frames

```
┌────────────┐
│Orquestador │
└─────┬──────┘
      │ 1. POST /stream/start
      │    {fps: 10, quality: 70}
      │    Authorization: Bearer <token>
      ↓
┌─────────────────────────────────────────┐
│       API Layer (Flask)                  │
│  ┌────────────────────────────────────┐ │
│  │ api/streaming/control.py            │ │
│  │ @require_token                      │ │
│  └────────┬───────────────────────────┘ │
│           │ 2. Enqueue streaming task   │
│           ↓                              │
│  ┌────────────────────────────────────┐ │
│  │ streaming/tasks.py                  │ │
│  │ start_streaming_task.delay()       │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
            │ 3. Celery worker marks active
            ↓
┌─────────────────────────────────────────┐
│         Streaming Layer                  │
│  ┌────────────────────────────────────┐ │
│  │ Redis State                         │ │
│  │ streaming:status = {                │ │
│  │   active: true,                     │ │
│  │   fps: 10,                          │ │
│  │   quality: 70                       │ │
│  │ }                                   │ │
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘

┌────────────┐
│Orquestador │
└─────┬──────┘
      │ 4. GET /stream/feed (SSE connection)
      │    Authorization: Bearer <token>
      ↓
┌─────────────────────────────────────────┐
│       API Layer (Flask)                  │
│  ┌────────────────────────────────────┐ │
│  │ api/streaming/feed.py               │ │
│  │ @require_auth_sse                   │ │
│  └────────┬───────────────────────────┘ │
│           │ 5. Check Redis state        │
│           ↓                              │
│  ┌────────────────────────────────────┐ │
│  │ streaming/streamer.py               │ │
│  │ ScreenStreamer()                   │ │
│  │   while active:                     │ │
│  │     frame = capture_frame()         │ │
│  │     yield "data: {frame_b64}\n\n"  │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
            │ 6. Stream SSE frames
            ↓
┌────────────┐
│Orquestador │  ← data: /9j/4AAQSkZ... (JPEG base64)
│ (Consume)  │  ← data: /9j/4AAQSkZ...
└────────────┘  ← data: /9j/4AAQSkZ...

┌────────────┐
│Orquestador │
└─────┬──────┘
      │ 7. POST /stream/stop
      ↓
┌─────────────────────────────────────────┐
│       API Layer (Flask)                  │
│  ┌────────────────────────────────────┐ │
│  │ api/streaming/control.py            │ │
│  │ - Revoke Celery task                │ │
│  │ - Update Redis: active = false      │ │
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
            │ 8. SSE connection closes
            ↓
┌────────────┐
│Orquestador │  Connection closed
└────────────┘
```

### Paso a Paso

1. **Start Request**: POST /stream/start con fps y quality
2. **Enqueue Task**: `start_streaming_task` se encola en Celery
3. **Mark Active**: Worker marca streaming como activo en Redis
4. **Connect SSE**: Cliente se conecta a GET /stream/feed
5. **Check State**: Endpoint verifica que streaming está activo
6. **Stream Frames**: `ScreenStreamer` captura y envía frames via SSE
7. **Stop Request**: POST /stream/stop detiene el streaming
8. **Close Connection**: Conexión SSE se cierra

### Arquitectura Streaming

**Separación de Responsabilidades**:
- **Celery Task**: Solo gestiona **estado** (active/inactive) en Redis
- **SSE Endpoint**: Maneja **captura y transmisión** real de frames

**Beneficios**:
- Escalable: Múltiples consumidores SSE
- Resiliente: Desconexión SSE no afecta estado
- Simple: Cada componente tiene una responsabilidad

---

## Flujo de Autenticación

### Escenario 1: API Authentication (Token)

```
┌────────────┐
│   Client   │
└─────┬──────┘
      │ GET /status
      │ Authorization: Bearer abc123xyz
      ↓
┌─────────────────────────────────────────┐
│       API Layer (Flask)                  │
│  ┌────────────────────────────────────┐ │
│  │ @require_token decorator            │ │
│  │ 1. Extract token from header        │ │
│  │ 2. Get server.token from config     │ │
│  │ 3. Compare tokens                   │ │
│  └────────┬───────────────────────────┘ │
│           │                              │
│           ├─ Match? → Allow (200)       │
│           └─ No match? → Deny (403)     │
└─────────────────────────────────────────┘
```

### Escenario 2: Web UI Authentication (Session)

```
┌─────────┐
│ Browser │
└────┬────┘
     │ GET /connected
     │ (no session)
     ↓
┌─────────────────────────────────────────┐
│       API Layer (Flask)                  │
│  ┌────────────────────────────────────┐ │
│  │ @require_auth decorator             │ │
│  │ 1. Check session['authenticated']   │ │
│  │ 2. Not authenticated?               │ │
│  └────────┬───────────────────────────┘ │
│           │                              │
│           └─ Redirect /login (302)      │
└─────────────────────────────────────────┘
     │
     ↓
┌─────────┐
│ Browser │ GET /login
└────┬────┘
     │ POST /login
     │ {token: "abc123xyz"}
     ↓
┌─────────────────────────────────────────┐
│  ┌────────────────────────────────────┐ │
│  │ api/web/auth.py                     │ │
│  │ 1. Validate token                   │ │
│  │ 2. session['authenticated'] = True  │ │
│  │ 3. Redirect /connected (302)        │ │
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

### Escenario 3: SSE Authentication

```
┌────────────┐
│   Client   │
└─────┬──────┘
      │ GET /stream/feed
      │ (no auth)
      ↓
┌─────────────────────────────────────────┐
│  ┌────────────────────────────────────┐ │
│  │ @require_auth_sse decorator         │ │
│  │ 1. Check session OR token           │ │
│  │ 2. Not authenticated?               │ │
│  └────────┬───────────────────────────┘ │
│           │                              │
│           └─ Send SSE error event       │
│              (NOT redirect)              │
└─────────────────────────────────────────┘
     │
     ↓
┌────────────┐
│   Client   │  ← event: error_unauthorized
└────────────┘    data: {"error": "Not authenticated"}
```

---

## Flujo de Estado (Redis)

### Sincronización de Estado entre Workers

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Gunicorn     │     │ Gunicorn     │     │ Gunicorn     │
│ Worker 1     │     │ Worker 2     │     │ Worker 3     │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                     │                     │
       │ 1. POST /run       │                     │
       │    execution:123    │                     │
       │    status=running   │                     │
       ↓                     │                     │
┌─────────────────────────────────────────────────────────┐
│                       Redis                              │
│  execution:123 = {status: "running", task_id: "xyz"}   │
└─────────────────────────────────────────────────────────┘
       │                     ↓                     │
       │              2. GET /execution?id=123     │
       │                 (reads from Redis)        │
       │                     │                     │
       │                     │              3. GET /stop?id=123
       │                     │                 (reads from Redis)
       │                     │                     ↓
       │                     │              ┌─────────────────┐
       │                     │              │ Update Redis:   │
       │                     │              │ status=stopped  │
       │                     │              └─────────────────┘
       │                     ↓                     │
       ↓                     ↓                     ↓
┌─────────────────────────────────────────────────────────┐
│                       Redis                              │
│  execution:123 = {status: "stopped", ...}               │
└─────────────────────────────────────────────────────────┘
```

**Key Point**: Redis como **fuente única de verdad** permite que múltiples workers Gunicorn (sin estado compartido) sincronicen el estado de ejecuciones.

### Cleanup de Executions Huérfanas

```
[Server Restart]
       ↓
┌─────────────────────────────────────────┐
│  api/middleware.py                       │
│  init_server_if_needed()                │
│  1. Check Redis for executions with     │
│     status="running"                     │
│  2. These are orphaned (previous server)│
│  3. Mark as "failed"                    │
└─────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────┐
│            Redis State                   │
│  execution:orphan-1 → status=failed     │
│  execution:orphan-2 → status=failed     │
└─────────────────────────────────────────┘
```

---

## Flujo de Tunnel Management

### Escenario: Iniciar Cloudflare Tunnel

```
┌────────────┐
│   Client   │
└─────┬──────┘
      │ POST /tunnel/start
      │ {subdomain: "robot-01"}
      ↓
┌─────────────────────────────────────────┐
│       API Layer (Flask)                  │
│  ┌────────────────────────────────────┐ │
│  │ api/tunnel/routes.py                │ │
│  │ 1. Read ~/.cloudflared/config.yml   │ │
│  │ 2. Update subdomain                 │ │
│  │ 3. Write config.yml                 │ │
│  └────────┬───────────────────────────┘ │
│           │                              │
│           ↓ 4. Start cloudflared        │
│  ┌────────────────────────────────────┐ │
│  │ subprocess.Popen([                  │ │
│  │   "cloudflared",                    │ │
│  │   "tunnel",                         │ │
│  │   "run",                            │ │
│  │   "robot-tunnel"                    │ │
│  │ ])                                  │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
            │ 5. Tunnel establishes
            ↓
┌──────────────────────────────────────────┐
│       Cloudflare Network                  │
│  robot-01.tunnel.example.com            │
│         ↓                                 │
│  https://localhost:5001                  │
└──────────────────────────────────────────┘
```

---

## Diagrams Summary

Para diagramas visuales, consulta:
- [diagrams/execution-flow.png](diagrams/) - Flujo de ejecución
- [diagrams/streaming-flow.png](diagrams/) - Flujo de streaming
- [diagrams/auth-flow.png](diagrams/) - Flujo de autenticación
- [diagrams/state-sync.png](diagrams/) - Sincronización de estado

---

**Actualizado**: 2026-01-08
**Versión**: 2.0.0
