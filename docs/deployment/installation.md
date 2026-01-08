# Installation Guide - Robot Runner v2.0

Guía de instalación para usuarios finales.

---

## Requisitos del Sistema

### Mínimos

- **CPU**: 2 cores
- **RAM**: 4 GB
- **Disco**: 500 MB libres
- **SO**: macOS 10.15+ / Ubuntu 20.04+ / Windows 10+
- **Python**: 3.9+ (si instala desde código fuente)
- **Redis**: 5.0+ (incluido en instalador)

### Recomendados

- **CPU**: 4+ cores
- **RAM**: 8 GB
- **Disco**: 1 GB libres (para logs y datos temporales)
- **Conexión**: Internet estable para orquestador remoto

---

## Opciones de Instalación

### Opción 1: Instalador Binario (Recomendado)

**Para usuarios que solo quieren ejecutar Robot Runner sin desarrollo.**

1. Descargar instalador desde [Releases](https://github.com/your-org/robotrunner/releases)
2. Ejecutar instalador
3. Configurar `config.json`
4. Iniciar aplicación

**macOS**:
```bash
# Descargar
curl -LO https://github.com/your-org/robotrunner/releases/download/v2.0.0/RobotRunner-macOS.zip

# Descomprimir
unzip RobotRunner-macOS.zip

# Ejecutar
./RobotRunner/run
```

**Linux**:
```bash
# Descargar
wget https://github.com/your-org/robotrunner/releases/download/v2.0.0/RobotRunner-Linux.tar.gz

# Descomprimir
tar -xzf RobotRunner-Linux.tar.gz

# Ejecutar
./RobotRunner/run
```

**Windows**:
1. Descargar `RobotRunner-Windows.zip`
2. Descomprimir en `C:\RobotRunner\`
3. Ejecutar `run.exe`

### Opción 2: Instalación desde Código Fuente

**Para desarrolladores o usuarios avanzados.**

Ver [Development Setup](../development/setup.md)

---

## Configuración Inicial

### 1. Configurar `config.json`

Ubicación: `config.json` en directorio de instalación

```json
{
  "machine_id": "ROBOT-01",
  "license_key": "your-license-key-here",
  "token": "auto-generated-token-here",
  "port": 5001,
  "ssl_enabled": true,
  "cert_file": "ssl/cert.pem",
  "key_file": "ssl/key.pem",
  "ca_cert": "ssl/ca-cert.pem",
  "notify_url": "https://orquestador.com/api/robot-status",
  "notify_on_status_change": true,
  "log_level": "INFO"
}
```

**Parámetros**:

- `machine_id`: ID único del robot (proporcionado por orquestador)
- `license_key`: Clave de licencia (proporcionada por orquestador)
- `token`: Token de autenticación API (generado automáticamente)
- `port`: Puerto HTTPS (default: 5001)
- `ssl_enabled`: Habilitar HTTPS (recomendado: true)
- `notify_url`: URL del orquestador para notificaciones
- `notify_on_status_change`: Notificar cambios de estado

### 2. Configurar Certificados SSL

#### Opción A: Usar Certificado Existente

Si el orquestador proporciona certificados:

```bash
# Copiar certificados al directorio ssl/
cp path/to/cert.pem ssl/
cp path/to/key.pem ssl/
cp path/to/ca-cert.pem ssl/
```

#### Opción B: Generar Certificado Self-Signed

Para testing o uso local:

```bash
cd ssl

# Generar CA
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout ca-key.pem -out ca-cert.pem \
  -days 365 -subj "/CN=RobotRunner CA"

# Generar certificado de servidor
openssl req -newkey rsa:4096 -nodes \
  -keyout key.pem -out cert.csr \
  -subj "/CN=localhost"

# Firmar con CA
openssl x509 -req -in cert.csr -CA ca-cert.pem \
  -CAkey ca-key.pem -CAcreateserial \
  -out cert.pem -days 365

cd ..
```

Ver [SSL Certificates Guide](../security/ssl-certificates.md) para más detalles.

### 3. Verificar Redis

Robot Runner requiere Redis para gestión de estado.

**macOS (Homebrew)**:
```bash
brew install redis
brew services start redis
redis-cli ping  # Debe responder "PONG"
```

**Ubuntu**:
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis
redis-cli ping
```

**Windows**:

Descargar Redis desde [GitHub](https://github.com/microsoftarchive/redis/releases) o usar WSL.

---

## Iniciar Robot Runner

### Modo System Tray (Recomendado para Desktop)

```bash
python run.py --tray
```

**Features**:
- Icono en bandeja del sistema
- Menú de acceso rápido
- Iniciar/detener servidor
- Ver logs
- Acceso a configuración

### Modo Servidor (Producción)

```bash
python run.py
# O
python cli/run_server.py
```

**Features**:
- Servidor Gunicorn con múltiples workers
- Celery workers embebidos
- Auto-restart on file changes (development)
- Logging a archivo

### Modo Servicio (Background)

**systemd (Linux)**:

Crear `/etc/systemd/system/robotrunner.service`:

```ini
[Unit]
Description=Robot Runner Service
After=network.target redis.service

[Service]
Type=simple
User=robotrunner
WorkingDirectory=/opt/robotrunner
ExecStart=/opt/robotrunner/venv/bin/python cli/run_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Activar:
```bash
sudo systemctl daemon-reload
sudo systemctl enable robotrunner
sudo systemctl start robotrunner
sudo systemctl status robotrunner
```

---

## Verificar Instalación

### 1. Verificar Servidor Web

```bash
curl -k https://localhost:5001/
```

Debe redirigir a `/login` o mostrar página de login.

### 2. Verificar API

```bash
TOKEN="your-token-from-config"
MACHINE_ID="your-machine-id"
LICENSE_KEY="your-license-key"

curl -k -X GET "https://localhost:5001/status?machine_id=$MACHINE_ID&license_key=$LICENSE_KEY" \
  -H "Authorization: Bearer $TOKEN"
```

Debe responder: `"free"` (u otro estado válido).

### 3. Verificar Redis

```bash
redis-cli
> GET server:status
# Debe mostrar el estado actual
```

### 4. Verificar Logs

```bash
tail -f logs/server.log
```

Debe mostrar logs de inicio del servidor.

---

## Acceso Web

Abrir en browser:
```
https://localhost:5001
```

**Login**:
1. Introducir token (desde `config.json`)
2. Click en "Login"
3. Acceder al panel de control

---

## Primer Robot Test

### 1. Crear Robot de Test

`test_robot.robot`:
```robot
*** Settings ***
Library           SeleniumLibrary

*** Test Cases ***
Simple Test
    Log    Robot Runner está funcionando!
    Should Be Equal    1    1
```

### 2. Ejecutar via API

```bash
TOKEN="your-token"

curl -k -X POST "https://localhost:5001/run" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "robot_file": "test_robot.robot",
    "params": {},
    "execution_id": "test-001"
  }'
```

### 3. Verificar Estado

```bash
curl -k -X GET "https://localhost:5001/execution?id=test-001" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Configuración Avanzada

### Cloudflare Tunnel (Opcional)

Para acceso remoto sin abrir puertos:

1. Instalar `cloudflared`:
```bash
# macOS
brew install cloudflare/cloudflare/cloudflared

# Ubuntu
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

2. Configurar tunnel:
```bash
cloudflared tunnel login
cloudflared tunnel create robot-tunnel
```

3. Actualizar `~/.cloudflared/config.yml`:
```yaml
tunnel: robot-tunnel
credentials-file: /path/to/credentials.json

ingress:
  - hostname: robot-01.your-domain.com
    service: https://localhost:5001
  - service: http_status:404
```

4. Ejecutar tunnel:
```bash
cloudflared tunnel run robot-tunnel
```

Ver [Tunnel Guide](../api/rest-api.md#tunnel-management) para control via API.

---

## Troubleshooting

### Servidor No Inicia

**Problema**: `Address already in use`

**Solución**:
```bash
# Ver qué proceso usa el puerto 5001
lsof -i :5001  # macOS/Linux
netstat -ano | findstr :5001  # Windows

# Matar proceso
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows
```

### Redis Connection Error

**Problema**: `Connection refused`

**Solución**:
```bash
# Iniciar Redis
redis-server

# Verificar que está corriendo
redis-cli ping
```

### SSL Certificate Error

**Problema**: `SSL: CERTIFICATE_VERIFY_FAILED`

**Solución**:

1. Verificar que certificados existen en `ssl/`
2. Regenerar certificados si están expirados
3. Para testing, usar `-k` con curl (ignora verificación)

### Import Errors

**Problema**: `ModuleNotFoundError`

**Solución**:
```bash
# Verificar Python y venv
which python  # Debe apuntar a venv

# Reinstalar dependencias
pip install -r requirements.txt
```

---

## Actualización

### Desde Binario

1. Descargar nueva versión
2. Detener Robot Runner
3. Backup de `config.json`
4. Reemplazar archivos
5. Restaurar `config.json`
6. Reiniciar

### Desde Código Fuente

```bash
git pull origin master
pip install -r requirements.txt
# Revisar CHANGELOG.md para cambios breaking
```

---

## Desinstalación

### Binario

```bash
# Detener servidor
pkill -f robotrunner

# Eliminar directorio
rm -rf /path/to/RobotRunner
```

### Código Fuente

```bash
# Detener servidor
pkill -f robotrunner

# Eliminar venv y archivos
rm -rf venv
rm -rf logs
rm config.json
```

### Redis (Si no lo usas para otra cosa)

```bash
# macOS
brew services stop redis
brew uninstall redis

# Ubuntu
sudo systemctl stop redis
sudo apt-get remove redis-server
```

---

## Próximos Pasos

- Leer [Production Guide](production.md) para deployment en producción
- Consultar [API Documentation](../api/rest-api.md) para integración
- Ver [Cross-Platform Guide](cross-platform.md) para notas específicas del SO

---

**Actualizado**: 2026-01-08
**Versión**: 2.0.0
