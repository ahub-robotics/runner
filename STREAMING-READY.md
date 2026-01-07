# ✅ Sistema de Streaming LISTO

## Estado Actual

✅ **Servidor corriendo** en https://localhost:5001
✅ **Workers de Celery activos** (4 workers)
✅ **Tareas de streaming registradas** (3 tareas)
✅ **Redis funcionando** en puerto 6378
✅ **Estado limpio** (sin estados huérfanos)

## Cómo Probar el Streaming

### Opción 1: Navegador (Recomendado)

1. **Abre el navegador** y navega a:
   ```
   https://localhost:5001/stream-view
   ```

2. **Inicia sesión** si te pide credenciales

3. **Click en "Iniciar"** (botón verde)
   - Deberías ver el video de tu pantalla en tiempo real

4. **Click en "Detener"** (botón rojo)
   - El video debería parar

### Opción 2: Comandos para Debugging

```bash
# 1. Ver logs en tiempo real
tail -f logs/server.log | grep -E "\[STREAM|\[STREAMING"

# 2. Ver estado de streaming
redis-cli -p 6378 HGETALL streaming:state

# 3. Limpiar estado manualmente (si es necesario)
./scripts/clean_streaming.sh
```

## Qué Buscar en los Logs

### Cuando inicies el streaming:
```
[STREAM-API] POST /stream/start recibido
[STREAM-API] Estado actual en Redis: {}
[STREAM-API] Iniciando tarea de Celery...
[STREAM-API] ✅ Tarea de streaming iniciada: <task_id>
[STREAMING-TASK] Iniciando streaming
[STREAMING-TASK] ✅ Streaming marcado como activo en Redis
[STREAM-FEED] Nueva conexión SSE establecida
[STREAM-FEED] Creando streamer (fps=15, quality=75)
```

### Si se detecta estado huérfano:
```
[STREAM-STATUS] ⚠️  Estado huérfano detectado (tarea PENDING), limpiando...
```

### Cuando detengas el streaming:
```
[STREAM-API] POST /stream/stop recibido
[STREAM-API] Enviando señal de detención...
[STREAMING-TASK] 🛑 Detención solicitada desde Redis
[STREAMING-TASK] ✅ Streaming detenido correctamente
```

## Arquitectura Simplificada

```
Usuario (Navegador)
    ↓
[Botones Start/Stop] → POST /stream/start|stop
    ↓
Celery Task (marca estado en Redis)
    ↓
Redis: streaming:state {active: true/false}
    ↓
[EventSource SSE] → GET /stream/feed
    ↓
Lee Redis → Captura pantalla → Envía frames
```

## Solución de Problemas

### Problema: Botón "Detener" aparece pero no hay video

**Causa**: Estado huérfano en Redis (tarea de Celery murió pero Redis no se limpió)

**Solución automática**:
- El sistema ahora detecta y limpia automáticamente estados huérfanos
- Simplemente recarga la página y el botón cambiará a "Iniciar"

**Solución manual**:
```bash
./scripts/clean_streaming.sh
```

### Problema: No se ve video después de "Iniciar"

**Diagnóstico**:
```bash
# 1. Verificar que la tarea se inició
redis-cli -p 6378 HGETALL streaming:state

# 2. Ver logs en tiempo real
tail -f logs/server.log | grep STREAM

# 3. Verificar workers de Celery
python scripts/test_streaming.py
```

**Posibles causas**:
- Workers de Celery no tienen las tareas cargadas → Reiniciar servidor
- Permisos de captura de pantalla en macOS → System Preferences → Security & Privacy → Privacy → Screen Recording

### Problema: Error "El streaming ya está activo"

**Solución**:
```bash
# Limpiar estado
./scripts/clean_streaming.sh

# O directamente en Redis
redis-cli -p 6378 DEL streaming:state
redis-cli -p 6378 DEL streaming:stop_requested
```

## Scripts Útiles

### Reiniciar servidor
```bash
./scripts/restart_server.sh
```
Detiene el servidor actual, limpia estado, y reinicia con tareas nuevas cargadas.

### Limpiar streaming
```bash
./scripts/clean_streaming.sh
```
Limpia el estado de streaming en Redis.

### Diagnóstico completo
```bash
python scripts/test_streaming.py
```
Verifica Redis, Celery, workers, y opcionalmente prueba streaming.

## Configuración

### Parámetros de streaming
Edita en `/src/app.py` → `/stream/start`:
```python
fps=15          # Frames por segundo (10-30)
quality=75      # Calidad JPEG (1-100)
```

**Recomendaciones**:
- Red local rápida: fps=30, quality=85
- Internet estándar: fps=15, quality=75
- Conexión lenta: fps=10, quality=60

## Cambios Implementados

### 1. Detección de Estados Huérfanos ✅
- `/stream/start` verifica que la tarea de Celery exista antes de rechazar
- `/stream/status` verifica y limpia automáticamente estados inválidos

### 2. Logs Mejorados ✅
- Todos los endpoints tienen logs detallados con prefijos [STREAM-API], [STREAMING-TASK], [STREAM-FEED]
- Fácil de filtrar y debuggear

### 3. Arquitectura Simplificada ✅
- Tareas de Celery solo gestionan estado (no WebSocket complejo)
- Transmisión via SSE (compatible con proxies/túneles)
- Separación clara: Estado (Celery) vs Transmisión (SSE)

### 4. Scripts de Utilidad ✅
- `restart_server.sh`: Reinicio completo con verificación
- `clean_streaming.sh`: Limpieza rápida de estado
- `test_streaming.py`: Diagnóstico completo

## Verificación Final

```bash
# 1. Ver que el servidor está corriendo
ps aux | grep "run.py --server-only"

# 2. Ver que Redis está activo
redis-cli -p 6378 ping

# 3. Ver workers de Celery
python << 'EOF'
from src.celery_config import celery_app
inspect = celery_app.control.inspect()
stats = inspect.stats()
if stats:
    print(f"✅ Workers activos: {len(stats)}")
    registered = inspect.registered()
    for worker, tasks in registered.items():
        streaming = [t for t in tasks if 'streaming' in t]
        print(f"✅ Tareas de streaming: {len(streaming)}")
        for task in streaming:
            print(f"   - {task}")
else:
    print("❌ No hay workers activos")
EOF
```

## URL del Servidor

🌐 **Principal**: https://localhost:5001
🎬 **Streaming**: https://localhost:5001/stream-view
📊 **Estado**: https://localhost:5001/stream/status

---

**Todo está listo para usar. Simplemente navega a https://localhost:5001/stream-view y prueba!**
