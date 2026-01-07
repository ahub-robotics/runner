# Diagnóstico del Problema de Streaming

## ✅ Cambios Implementados

1. **Nuevo decorador `@require_auth_sse`**:
   - No redirecciona, envía error via SSE
   - Permite debugging de autenticación

2. **Logs en el frontend**:
   - Consola del navegador muestra todos los eventos
   - Fácil de ver qué está pasando

3. **Conexión automática**:
   - Si detecta streaming activo, conecta automáticamente

## 🔍 Cómo Diagnosticar

### Paso 1: Abrir Consola del Navegador

1. Abre **Chrome** o **Firefox**
2. Presiona **F12** (o clic derecho → Inspeccionar)
3. Ve a la pestaña **"Console"**

### Paso 2: Navegar a la Página de Streaming

```
https://localhost:5001/stream-view
```

⚠️ **IMPORTANTE**: Es puerto **5001**, NO 5055

### Paso 3: Ver Logs en la Consola

Busca mensajes que empiecen con `[STREAM-FRONTEND]`:

#### ✅ Conexión Exitosa:
```
[STREAM-FRONTEND] Conectando a: https://localhost:5001/stream/feed
[STREAM-FRONTEND] Conexión SSE establecida
[STREAM-FRONTEND] Mensaje recibido, tamaño: 50000
```

#### ❌ Error de Autenticación:
```
[STREAM-FRONTEND] Conectando a: https://localhost:5001/stream/feed
[STREAM-FRONTEND] Error en SSE: ...
[STREAM-FRONTEND] ReadyState: 2
```

#### ❌ Sin Mensajes:
Si NO ves mensajes, significa que el JavaScript no se está ejecutando.

### Paso 4: Verificar en el Servidor

En otra terminal, ejecuta:

```bash
tail -f logs/server.log | grep -E "\[STREAM"
```

#### ✅ Deberías ver:
```
[STREAM-FEED] ✅ Autenticado via sesión
[STREAM-FEED] Nueva conexión SSE establecida
[STREAM-FEED] Creando streamer (fps=15, quality=75)
```

#### ❌ Si ves:
```
[STREAM-FEED] ❌ Acceso no autenticado
```

Significa que la sesión no se está enviando correctamente.

## 🛠️ Soluciones Según el Problema

### Problema A: "Error de autenticación" en consola

**Causa**: La sesión no se está enviando

**Solución 1**: Verifica que iniciaste sesión
1. Ve a `https://localhost:5001/login`
2. Ingresa tus credenciales
3. Vuelve a `https://localhost:5001/stream-view`

**Solución 2**: Limpia cookies y vuelve a iniciar sesión
```javascript
// En la consola del navegador:
document.cookie.split(";").forEach(c => {
  document.cookie = c.trim().split("=")[0] + "=;expires=Thu, 01 Jan 1970 00:00:00 UTC";
});
```

Luego recarga la página e inicia sesión.

### Problema B: No aparecen mensajes en la consola

**Causa**: El JavaScript no se está cargando

**Solución**: Verifica que la página cargó correctamente
1. Presiona **Ctrl+U** (ver código fuente)
2. Busca: `function connectToStream()`
3. Si NO está, significa que la página no cargó correctamente

### Problema C: Aparece "Detener" pero no hay video

**Causa**: Hay estado huérfano en Redis

**Solución**:
```bash
./scripts/clean_streaming.sh
```

Luego recarga la página.

### Problema D: "El streaming ya está activo"

**Causa**: La tarea de Celery realmente está corriendo

**Diagnóstico**:
```bash
# Ver si hay tarea activa
redis-cli -p 6378 HGETALL streaming:state

# Ver estado de la tarea en Celery
python << 'EOF'
from src.celery_config import celery_app
from celery.result import AsyncResult

# Reemplaza con el task_id de Redis
task_id = "tu-task-id-aqui"
result = AsyncResult(task_id, app=celery_app)
print(f"Estado: {result.state}")
EOF
```

**Solución**:
```bash
# Limpiar estado
./scripts/clean_streaming.sh
```

## 📊 Comando de Diagnóstico Completo

Ejecuta esto para ver todo:

```bash
echo "=== VERIFICANDO SERVIDOR ==="
ps aux | grep "run.py" | grep -v grep

echo ""
echo "=== VERIFICANDO PUERTO ==="
lsof -i :5001 | grep LISTEN

echo ""
echo "=== VERIFICANDO REDIS ==="
redis-cli -p 6378 ping

echo ""
echo "=== ESTADO DE STREAMING ==="
redis-cli -p 6378 HGETALL streaming:state

echo ""
echo "=== LOGS RECIENTES ==="
tail -20 logs/server.log | grep -E "\[STREAM"
```

## 🎬 Secuencia de Prueba Paso a Paso

1. **Limpiar todo**:
   ```bash
   ./scripts/clean_streaming.sh
   ```

2. **Abrir navegador con consola** (F12)

3. **Navegar a**:
   ```
   https://localhost:5001/stream-view
   ```

4. **Verificar en consola**:
   - ¿Aparece `[STREAM-FRONTEND] Conectando`?
   - ¿Hay algún error?

5. **Click en "Iniciar"**

6. **Verificar en consola**:
   - ¿Aparece `[STREAM-FRONTEND] Conexión SSE establecida`?
   - ¿Aparece `[STREAM-FRONTEND] Mensaje recibido`?

7. **Si NO aparecen mensajes**, verificar logs del servidor:
   ```bash
   tail -f logs/server.log | grep -E "\[STREAM"
   ```

## 🆘 Si Nada Funciona

1. **Captura screenshot de la consola del navegador**
2. **Ejecuta el comando de diagnóstico completo** (arriba)
3. **Comparte**:
   - Screenshot de la consola
   - Output del comando de diagnóstico
   - Últimas 50 líneas de `logs/server.log`

## ✅ Verificación Final Antes de Probar

```bash
# 1. Servidor corriendo en 5001
curl -k https://localhost:5001 -I 2>&1 | grep "HTTP"
# Debería mostrar: HTTP/1.1 302 FOUND

# 2. Workers de Celery activos
python scripts/test_streaming.py 2>&1 | grep "Workers activos"
# Debería mostrar: ✅ Workers activos: 1

# 3. Estado limpio
redis-cli -p 6378 HGETALL streaming:state
# Debería estar vacío: (empty array)
```

**Si todos estos checks pasan, el sistema está listo para probar.**

## 🌐 URL Correcta

⚠️ **IMPORTANTE**:

```
✅ CORRECTO: https://localhost:5001/stream-view
❌ INCORRECTO: https://localhost:5055/stream-view
```

El servidor está en puerto **5001**.
