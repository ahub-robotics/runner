# Solución al Problema de Streaming

## Problema Detectado

El estado en Redis indica que el streaming está activo, pero la tarea de Celery no está corriendo realmente. Esto causa que:
- Aparezca el botón "Detener" en lugar de "Iniciar"
- No se muestre video en la pantalla
- Al intentar iniciar de nuevo, diga que ya está activo

## Solución Implementada

He agregado **verificación automática de estados huérfanos**:
- Cada vez que se consulta el estado, verifica si la tarea de Celery realmente existe
- Si la tarea no existe o terminó, limpia automáticamente el estado de Redis
- Esto previene estados inconsistentes

## Cómo Usar

### 1. Limpiar Estado Actual (Una Vez)

```bash
./scripts/clean_streaming.sh
```

O manualmente:
```bash
redis-cli -p 6378 DEL streaming:state
redis-cli -p 6378 DEL streaming:stop_requested
```

### 2. Reiniciar el Servidor

```bash
# Detener el servidor actual (Ctrl+C)
# Luego reiniciar:
python run.py
```

### 3. Probar el Streaming

1. Ir a: `https://localhost:5055/stream-view`
2. Debería aparecer el botón "Iniciar" (verde)
3. Click en "Iniciar" → Debería ver el video de tu pantalla
4. Click en "Detener" → El video debería parar

## Diagnóstico

### Ver Estado Actual en Redis

```bash
redis-cli -p 6378 HGETALL streaming:state
```

**Respuesta esperada (inactivo)**:
```
(empty array)
```

**Respuesta esperada (activo)**:
```
1) "active"
2) "true"
3) "task_id"
4) "abc-123-def-456"
5) "fps"
6) "15"
...
```

### Verificar Tareas de Celery

```bash
python scripts/test_streaming.py
```

Esto mostrará:
- ✅ Conexión a Redis
- ✅ Tareas registradas
- ✅ Workers activos

### Ver Logs en Tiempo Real

Cuando inicies el servidor (`python run.py`), verás logs como:

**Al iniciar streaming**:
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

**Si detecta estado huérfano**:
```
[STREAM-STATUS] ⚠️  Estado huérfano detectado (tarea PENDING), limpiando...
```

## Verificación de que Funciona

### Test 1: Estado Inicial
```bash
curl -k https://localhost:5055/stream/status -H "Authorization: Bearer tu_token"
```

Debería retornar:
```json
{"success": true, "active": false, "port": null, "clients": 0}
```

### Test 2: Iniciar Streaming
```bash
curl -k -X POST https://localhost:5055/stream/start -H "Authorization: Bearer tu_token"
```

Debería retornar:
```json
{"success": true, "message": "Streaming iniciado correctamente", "task_id": "..."}
```

### Test 3: Verificar Estado Activo
```bash
curl -k https://localhost:5055/stream/status -H "Authorization: Bearer tu_token"
```

Debería retornar:
```json
{"success": true, "active": true, "port": 8765, "fps": 15, "quality": 75, ...}
```

### Test 4: Conectar al Feed (en navegador)
```
https://localhost:5055/stream/feed
```

Debería empezar a recibir frames en formato SSE.

## Qué Hacer si Sigue sin Funcionar

### 1. Verificar que Redis está corriendo
```bash
redis-cli -p 6378 ping
```

Debe responder: `PONG`

### 2. Verificar que los workers de Celery están activos
```bash
python scripts/test_streaming.py
```

Debe mostrar: `✅ Workers activos: N`

### 3. Ver logs detallados

En el terminal donde corre `python run.py`, busca:
- `[STREAM-API]` → Logs de los endpoints
- `[STREAMING-TASK]` → Logs de las tareas de Celery
- `[STREAM-FEED]` → Logs de la transmisión SSE

### 4. Verificar permisos de captura de pantalla

En macOS, puede que necesites dar permisos de captura de pantalla:
- System Preferences → Security & Privacy → Privacy → Screen Recording
- Agrega Python o Terminal a la lista

### 5. Probar captura manual

```python
from src.emisor import ScreenStreamer
streamer = ScreenStreamer(port=8765, quality=75, fps=15)
frame = streamer.capture_screen()
print(f"Frame capturado: {len(frame)} bytes")
```

Si esto falla, el problema es con la captura de pantalla, no con Celery.

## Resumen de Cambios

### Archivos Modificados

1. **`/src/app.py`**:
   - Endpoint `/stream/start`: Verifica y limpia estados huérfanos antes de iniciar
   - Endpoint `/stream/status`: Verifica que la tarea de Celery realmente exista

2. **`/src/streaming_tasks.py`**:
   - Simplificado para solo gestionar estado en Redis
   - No hay WebSocket, asyncio, ni threads complejos

### Scripts Nuevos

- **`scripts/clean_streaming.sh`**: Limpia el estado manualmente
- **`scripts/test_streaming.py`**: Diagnóstico completo del sistema

## Contacto

Si el problema persiste después de seguir todos estos pasos:
1. Corre `python scripts/test_streaming.py` y comparte el resultado
2. Comparte los logs del servidor (líneas con `[STREAM-` o `[STREAMING-`)
3. Comparte el output de `redis-cli -p 6378 HGETALL streaming:state`
