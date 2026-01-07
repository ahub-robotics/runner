# Solución Rápida para Streaming en macOS

## Problema
El worker de Gunicorn crashea con `SIGSEGV` cuando intenta capturar pantalla después de fork() en macOS.

```
The process has forked and you cannot use this CoreFoundation functionality safely. YOU MUST exec().
Worker (pid:XXXX) was sent SIGSEGV!
```

## Causa Raíz
- macOS usa CoreFoundation para captura de pantalla (via `mss` o `PIL`)
- Gunicorn usa `fork()` para crear workers
- macOS **prohíbe** usar CoreFoundation después de fork

## Solución Implementada

### Opción 1: Usar Flask Development Server (Más Rápido)
```bash
# Detener Gunicorn
pkill -f "run.py --server-only"

# Iniciar Flask directamente (sin fork)
FLASK_APP=src/app.py flask run --host=0.0.0.0 --port=5001 --cert=ssl/cert.pem --key=ssl/key.pem
```

**Ventajas**:
- ✅ No usa fork
- ✅ Funciona inmediatamente
- ✅ Perfecto para desarrollo/pruebas

**Desventajas**:
- ❌ No apto para producción (single-threaded)
- ❌ Sin workers paralelos

### Opción 2: Refactorizar para Usar Waitress
```python
# En lugar de Gunicorn, usar Waitress (no hace fork en macOS)
from waitress import serve
serve(app, host='0.0.0.0', port=5001, threads=4)
```

### Opción 3: Captura en Proceso Separado (Producción)

Crear un daemon que captura pantalla y guarda frames en memoria compartida:

```python
# screen_capture_daemon.py
import mss
import time
from multiprocessing import shared_memory

def capture_loop():
    with mss.mss() as sct:
        while True:
            screenshot = sct.grab(sct.monitors[0])
            # Guardar en shared memory
            shm.buf[:] = screenshot.rgb
            time.sleep(1/15)  # 15 FPS

# Iniciar daemon ANTES de Gunicorn
python screen_capture_daemon.py &
python run.py --server-only
```

El endpoint Flask lee desde shared memory en lugar de capturar directamente.

## Aplicar Solución

Para testing inmediato, usa Flask development server:

```bash
cd /Users/enriquecrespodebenito/robotrunner_windows

# Detener Gunicorn
pkill -9 -f "run.py"

# Iniciar Flask dev server
python3 -c "from src.app import app; app.run(host='0.0.0.0', port=5001, ssl_context=('ssl/cert.pem', 'ssl/key.pem'), threaded=True)"
```

Luego accede a: https://localhost:5001/stream-view

## Fix Permanente

Para producción, necesitas:
1. Worker de Celery captura pantalla → guarda en Redis
2. Endpoint Flask lee frames desde Redis
3. NO captura directamente en worker de Gunicorn

O alternativamente:
1. Cambiar a Waitress que no hace fork
2. Funciona en macOS sin problemas