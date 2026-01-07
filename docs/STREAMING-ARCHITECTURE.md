# Arquitectura del Sistema de Streaming

## Resumen

El sistema de streaming de video ha sido simplificado para usar Celery + Redis de manera efectiva:

- **Tareas de Celery**: Gestionan solo el **estado** del streaming en Redis
- **Endpoint SSE**: `/stream/feed` maneja la **captura y transmisión** real de frames
- **Redis**: Base de datos de estado compartida entre todos los workers

## Arquitectura Simplificada

```
┌─────────────────────────────────────────┐
│         Frontend (Browser)              │
│  - Botones: Start/Stop                  │
│  - EventSource SSE (/stream/feed)       │
└─────────────────────────────────────────┘
              ↓ POST                ↓ GET (SSE)
┌─────────────────────────────────────────┐
│         Flask Endpoints                 │
├─────────────────────────────────────────┤
│ POST /stream/start → Celery Task        │
│ POST /stream/stop  → Celery Task        │
│ GET  /stream/status → Lee Redis         │
│ GET  /stream/feed  → Captura + SSE      │
└─────────────────────────────────────────┘
       ↓                           ↓
┌──────────────┐           ┌──────────────┐
│ Celery Tasks │           │ ScreenStreamer│
│  (Estado)    │           │  (Captura)    │
└──────────────┘           └──────────────┘
       ↓
┌──────────────┐
│    Redis     │
│ streaming:   │
│   state      │
└──────────────┘
```

## Componentes

### 1. Tareas de Celery (`/src/streaming_tasks.py`)

**`start_streaming_task`**:
- Marca el streaming como activo en Redis
- Guarda configuración (fps, quality, task_id)
- Mantiene la tarea viva con un loop
- Verifica cada segundo si se solicitó detener

**`stop_streaming_task`**:
- Envía señal de detención via Redis
- La tarea de inicio detecta la señal y termina

**`get_streaming_status`**:
- Lee el estado desde Redis
- Retorna información de configuración

### 2. Endpoints de Flask (`/src/app.py`)

**POST `/stream/start`**:
```python
1. Verifica si ya está activo (Redis)
2. Lanza start_streaming_task.delay()
3. Retorna task_id
```

**POST `/stream/stop`**:
```python
1. Verifica que esté activo (Redis)
2. Lanza stop_streaming_task.delay()
3. Retorna confirmación
```

**GET `/stream/status`**:
```python
1. Lee streaming:state desde Redis
2. Retorna {active, fps, quality, task_id}
```

**GET `/stream/feed`** (SSE):
```python
while True:
    1. Lee streaming:state desde Redis
    2. Si active == true:
        a. Crea ScreenStreamer local (si no existe)
        b. Captura frame
        c. Codifica en base64
        d. Yield como SSE: "data: <image>\n\n"
        e. Sleep(1/fps)
    3. Si active == false:
        - Envía "data: stream_stopped\n\n"
        - Cierra conexión
```

### 3. Estado en Redis

**Clave**: `streaming:state` (Hash)

**Campos**:
```
active: "true" | "false"
task_id: "abc-123-def-456"
host: "0.0.0.0"
port: "8765"
fps: "15"
quality: "75"
started_at: "1234567890.123"
```

**Clave**: `streaming:stop_requested` (String, TTL 60s)
```
"true" → Señal para detener
```

## Flujo de Operación

### Inicio de Streaming

```
Usuario → Click "Iniciar"
  ↓
Frontend → POST /stream/start
  ↓
Flask → start_streaming_task.delay()
  ↓
Celery Worker → Escribe Redis: streaming:state{active: true}
  ↓              Mantiene loop (task viva)
Frontend → EventSource.connect('/stream/feed')
  ↓
Flask/stream/feed → while True:
  ├─ Lee Redis: active?
  ├─ Si true: Captura frame → Yield SSE
  └─ Si false: Cierra conexión
```

### Detención de Streaming

```
Usuario → Click "Detener"
  ↓
Frontend → POST /stream/stop
  ↓
Flask → stop_streaming_task.delay()
  ↓
Celery Worker → Escribe Redis: streaming:stop_requested = "true"
  ↓
Tarea de inicio (loop) → Detecta señal → Limpia Redis → Termina
  ↓
/stream/feed → Detecta active=false → Cierra SSE
```

## Ventajas de Esta Arquitectura

### 1. **Simplicidad**
- No hay servidores WebSocket complejos
- No hay manejo de asyncio en múltiples threads
- Tareas de Celery son simples: solo estado

### 2. **Compatibilidad**
- SSE funciona a través de proxies/túneles HTTP
- No requiere puertos adicionales
- Compatible con autenticación existente

### 3. **Escalabilidad**
- Cualquier worker de Gunicorn puede servir `/stream/feed`
- Estado compartido via Redis (sincronización automática)
- Múltiples clientes pueden conectarse simultáneamente

### 4. **Mantenibilidad**
- Separación clara: Estado (Celery) vs Transmisión (SSE)
- Fácil de debuggear: logs claros en cada componente
- Código más limpio y comprensible

## Diagnóstico y Pruebas

### Script de diagnóstico

```bash
python scripts/test_streaming.py
```

**Verifica**:
- ✅ Conexión a Redis
- ✅ Registro de tareas de Celery
- ✅ Workers activos
- ✅ Inicio/detención de streaming (opcional)

### Logs a revisar

**Inicio**:
```
[STREAM-API] POST /stream/start recibido
[STREAM-API] Estado actual en Redis: {}
[STREAM-API] Iniciando tarea de Celery...
[STREAM-API] ✅ Tarea de streaming iniciada: abc-123
[STREAMING-TASK] Iniciando streaming
[STREAMING-TASK] ✅ Streaming marcado como activo en Redis
[STREAM-FEED] Nueva conexión SSE establecida
[STREAM-FEED] Creando streamer (fps=15, quality=75)
```

**Detención**:
```
[STREAM-API] POST /stream/stop recibido
[STREAM-API] Enviando señal de detención...
[STREAM-API] ✅ Señal de detención enviada: def-456
[STREAMING-TASK] 🛑 Detención solicitada desde Redis
[STREAMING-TASK] ✅ Streaming detenido correctamente
[STREAM-FEED] Stream inactivo, cerrando conexión SSE
```

### Verificación manual con Redis CLI

```bash
redis-cli -p 6378

# Ver estado actual
HGETALL streaming:state

# Ver señal de stop
GET streaming:stop_requested

# Limpiar manualmente si es necesario
DEL streaming:state
DEL streaming:stop_requested
```

## Troubleshooting

### Problema: No se inicia el streaming

**Síntomas**: Click en "Iniciar" pero no aparece video

**Diagnóstico**:
1. Verificar logs de Flask: `[STREAM-API] ✅ Tarea de streaming iniciada`
2. Verificar Redis: `redis-cli HGETALL streaming:state`
3. Verificar workers: `[STREAMING-TASK] Iniciando streaming`

**Causas posibles**:
- ❌ Workers de Celery no están activos → Iniciar servidor
- ❌ Tarea no registrada → Verificar imports en `celery_worker.py`
- ❌ Redis no está corriendo → `redis-cli ping`

### Problema: Video se detiene solo

**Síntomas**: Streaming se inicia pero se detiene después de unos segundos

**Diagnóstico**:
1. Verificar logs de `/stream/feed`: Errores de captura?
2. Verificar estado en Redis: `streaming:state` existe?

**Causas posibles**:
- ❌ Error en captura de pantalla → Ver logs de ScreenStreamer
- ❌ Estado de Redis se limpió → Verificar si la tarea sigue viva

### Problema: No se puede detener

**Síntomas**: Click en "Detener" pero el streaming continúa

**Diagnóstico**:
1. Verificar logs: `[STREAMING-TASK] 🛑 Detención solicitada`
2. Verificar Redis: `GET streaming:stop_requested` debe ser "true"

**Causas posibles**:
- ❌ Tarea de Celery está colgada → Reiniciar servidor
- ❌ Loop no detecta señal → Verificar código de `start_streaming_task`

## Configuración

### Parámetros de streaming (en `/stream/start`)

```python
fps=15          # Frames por segundo (10-30)
quality=75      # Calidad JPEG (1-100)
```

**Recomendaciones**:
- Red local: fps=30, quality=85
- Internet: fps=15, quality=75
- Móvil/lento: fps=10, quality=60

## Conclusión

Esta arquitectura simplificada proporciona:
- ✅ Gestión de estado robusta via Celery + Redis
- ✅ Transmisión eficiente via SSE
- ✅ Fácil diagnóstico y mantenimiento
- ✅ Escalabilidad con múltiples workers

Todo el sistema está diseñado para ser simple, confiable y fácil de debuggear.
