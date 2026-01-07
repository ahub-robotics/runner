# Nuevas Funcionalidades - Robot Runner

Este documento describe las nuevas funcionalidades implementadas para la gestión de túneles Cloudflare y el reinicio del servidor desde la interfaz web de Flask.

## Tabla de Contenidos

- [Gestión de Túneles Cloudflare](#gestión-de-túneles-cloudflare)
- [Reinicio del Servidor](#reinicio-del-servidor)
- [Endpoints de API](#endpoints-de-api)
- [Interfaz de Usuario](#interfaz-de-usuario)
- [Uso](#uso)

---

## Gestión de Túneles Cloudflare

### Descripción

Ahora puedes gestionar el túnel de Cloudflare directamente desde la interfaz web del Robot Runner. Esto incluye:

- **Iniciar el túnel**: Inicia el túnel de Cloudflare en background
- **Detener el túnel**: Detiene el túnel activo
- **Ver estado**: Muestra si el túnel está activo o inactivo
- **Ver URL pública**: Cuando el túnel está activo, muestra la URL pública accesible

### Requisitos Previos

1. **Cloudflared instalado**: Debes tener `cloudflared` instalado en tu sistema
   ```bash
   # macOS
   brew install cloudflared

   # Linux
   wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
   sudo dpkg -i cloudflared-linux-amd64.deb

   # Windows
   # Descargar desde: https://github.com/cloudflare/cloudflared/releases
   ```

2. **Configuración del túnel**: Ejecuta el script de configuración inicial
   ```bash
   python scripts/setup_machine_tunnel.py
   ```

### Características

- **Inicio automático en background**: El túnel se ejecuta como proceso independiente
- **Estado en tiempo real**: La interfaz muestra el estado actual del túnel cada 5 segundos
- **URL pública dinámica**: Basada en el `machine_id` configurado (ej: `https://i3wfqvs5fdhs.automatehub.es`)
- **Logs integrados**: Todas las acciones se registran en los logs del dashboard

---

## Reinicio del Servidor

### Descripción

Puedes reiniciar el servidor Flask/Gunicorn directamente desde la interfaz web. Esto es útil cuando:

- Has modificado la configuración y necesitas recargarla
- Quieres aplicar cambios sin detener manualmente el servidor
- Necesitas resolver problemas de estado del servidor

### Características

- **Reinicio seguro**: Envía señal SIGHUP a Gunicorn para reiniciar los workers
- **Confirmación**: Solicita confirmación antes de reiniciar
- **Recarga automática**: La página se recarga automáticamente después de 3 segundos
- **Sin pérdida de datos**: El reinicio es graceful, permitiendo que las conexiones activas se completen

### Advertencia

⚠️ **Importante**: El reinicio puede interrumpir tareas en ejecución. Asegúrate de que no haya robots ejecutándose antes de reiniciar el servidor.

---

## Endpoints de API

### Gestión de Túneles

#### `POST /tunnel/start`
Inicia el túnel de Cloudflare en background.

**Autenticación**: Requiere sesión activa o token de autenticación

**Respuesta exitosa** (200):
```json
{
    "success": true,
    "message": "Túnel iniciado correctamente",
    "subdomain": "i3wfqvs5fdhs.automatehub.es",
    "url": "https://i3wfqvs5fdhs.automatehub.es"
}
```

**Errores posibles**:
- `400`: cloudflared no instalado, configuración no encontrada, o túnel ya activo
- `500`: Error al iniciar el túnel

---

#### `POST /tunnel/stop`
Detiene el túnel de Cloudflare activo.

**Autenticación**: Requiere sesión activa o token de autenticación

**Respuesta exitosa** (200):
```json
{
    "success": true,
    "message": "Túnel detenido correctamente"
}
```

**Errores posibles**:
- `400`: No hay túneles activos
- `500`: Error al detener el túnel

---

#### `GET /tunnel/status`
Obtiene el estado actual del túnel.

**Autenticación**: Requiere sesión activa o token de autenticación

**Respuesta** (200):
```json
{
    "success": true,
    "active": true,
    "subdomain": "i3wfqvs5fdhs.automatehub.es",
    "url": "https://i3wfqvs5fdhs.automatehub.es",
    "machine_id": "I3WFQVS5FDHS",
    "pids": ["12345"]
}
```

---

### Gestión del Servidor

#### `POST /server/restart`
Reinicia el servidor Flask/Gunicorn.

**Autenticación**: Requiere sesión activa o token de autenticación

**Respuesta** (200):
```json
{
    "success": true,
    "message": "Servidor reiniciándose..."
}
```

**Nota**: Después de enviar esta petición, el servidor se reiniciará en 1 segundo.

---

## Interfaz de Usuario

### Dashboard Principal (`/connected`)

El dashboard ahora incluye dos nuevas tarjetas:

#### 1. Cloudflare Tunnel Card

```
┌─────────────────────────────────────┐
│ 🌩️ Cloudflare Tunnel               │
├─────────────────────────────────────┤
│ Status: ● Activo/Inactivo           │
│ Public URL: https://...             │
│                                     │
│ [Iniciar Túnel] [Detener Túnel]    │
└─────────────────────────────────────┘
```

**Características**:
- Indicador visual de estado (verde = activo, rojo = inactivo)
- URL pública clickeable cuando el túnel está activo
- Botones habilitados/deshabilitados según el estado
- Actualización automática cada 5 segundos

#### 2. Server Control Card

```
┌─────────────────────────────────────┐
│ 🔄 Server Control                   │
├─────────────────────────────────────┤
│ Actions:                            │
│                                     │
│ [Reiniciar Servidor]                │
│                                     │
│ ℹ️ El servidor se reiniciará y      │
│   recargará la configuración        │
└─────────────────────────────────────┘
```

**Características**:
- Botón de reinicio con confirmación
- Mensaje informativo sobre el efecto del reinicio
- Logs en tiempo real del proceso de reinicio

---

## Uso

### Desde la Interfaz Web

1. **Accede al dashboard**: Navega a `https://localhost:5055/connected`

2. **Gestionar el túnel**:
   - Revisa el estado actual en la tarjeta "Cloudflare Tunnel"
   - Click en "Iniciar Túnel" para activar el túnel
   - Click en "Detener Túnel" para desactivarlo
   - La URL pública aparecerá cuando el túnel esté activo

3. **Reiniciar el servidor**:
   - En la tarjeta "Server Control", click en "Reiniciar Servidor"
   - Confirma la acción en el diálogo
   - Espera 3 segundos para que la página se recargue automáticamente

### Desde la API

#### Ejemplo con curl

**Iniciar túnel**:
```bash
curl -X POST https://localhost:5055/tunnel/start \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -k
```

**Ver estado del túnel**:
```bash
curl https://localhost:5055/tunnel/status \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -k
```

**Detener túnel**:
```bash
curl -X POST https://localhost:5055/tunnel/stop \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -k
```

**Reiniciar servidor**:
```bash
curl -X POST https://localhost:5055/server/restart \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -k
```

#### Ejemplo con Python

```python
import requests

# Configuración
BASE_URL = "https://localhost:5055"
TOKEN = "eff7df3018dc2b2271165865c0f78aa17ce5df27"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# Iniciar túnel
response = requests.post(
    f"{BASE_URL}/tunnel/start",
    headers=HEADERS,
    verify=False
)
print(response.json())

# Ver estado
response = requests.get(
    f"{BASE_URL}/tunnel/status",
    headers=HEADERS,
    verify=False
)
print(response.json())

# Reiniciar servidor (¡cuidado!)
response = requests.post(
    f"{BASE_URL}/server/restart",
    headers=HEADERS,
    verify=False
)
print(response.json())
```

---

## Solución de Problemas

### El túnel no inicia

**Problema**: Error "cloudflared no está instalado"

**Solución**:
```bash
# macOS
brew install cloudflared

# Verificar instalación
which cloudflared
```

---

**Problema**: Error "Configuración de túnel no encontrada"

**Solución**:
```bash
# Ejecutar script de configuración
python scripts/setup_machine_tunnel.py

# Verificar que existe el archivo
ls ~/.cloudflared/config.yml
```

---

### El servidor no reinicia

**Problema**: El servidor no responde después de solicitar reinicio

**Solución**:
1. Espera 5-10 segundos
2. Recarga manualmente la página
3. Si persiste, reinicia manualmente:
   ```bash
   # Encontrar proceso
   ps aux | grep gunicorn

   # Matar proceso
   kill -HUP <PID>
   ```

---

### El estado del túnel no se actualiza

**Problema**: La interfaz muestra "Verificando..." indefinidamente

**Solución**:
1. Abre la consola del navegador (F12)
2. Revisa si hay errores de red
3. Verifica que la sesión siga activa
4. Recarga la página

---

## Logs y Debugging

### Ver logs del túnel

Los logs del túnel aparecen en el dashboard en tiempo real. También puedes ver los logs del sistema:

```bash
# Ver procesos de cloudflared
ps aux | grep cloudflared

# Ver logs del sistema (macOS)
log show --predicate 'process == "cloudflared"' --last 5m
```

### Ver logs del servidor

```bash
# Logs en tiempo real en el dashboard
# O ver el archivo de log compartido
tail -f ~/Robot/requests.log
```

---

## Notas Técnicas

### Implementación del túnel

- El túnel se ejecuta como proceso independiente usando `subprocess.Popen`
- Se utiliza `start_new_session=True` para desacoplar del proceso padre
- La salida se redirige a `/dev/null` para evitar bloqueos
- El estado se verifica usando `pgrep -f 'cloudflared tunnel run'`

### Implementación del reinicio

- Se utiliza `signal.SIGHUP` para reiniciar Gunicorn de forma graceful
- El reinicio se programa con `ThreadPoolExecutor` para no bloquear la respuesta
- Se espera 1 segundo antes de enviar la señal para asegurar que la respuesta se envíe

### Seguridad

- Todos los endpoints requieren autenticación (sesión o token)
- Las credenciales se validan antes de ejecutar acciones
- Los comandos del sistema se ejecutan con parámetros fijos (no hay inyección posible)

---

## Próximas Mejoras

Funcionalidades planificadas para futuras versiones:

- [ ] Configuración de túnel desde la interfaz (sin ejecutar scripts)
- [ ] Múltiples túneles simultáneos
- [ ] Logs del túnel en tiempo real en el dashboard
- [ ] Notificaciones cuando el túnel se desconecta
- [ ] Programación de reinicio del servidor
- [ ] Estadísticas de uso del túnel

---

## Contacto y Soporte

Para reportar problemas o sugerencias, contacta al equipo de Robot Runner.

**Versión**: 2.0
**Última actualización**: 2025-12-22