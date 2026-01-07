# Robot Runner

Sistema de ejecución remota de robots de automatización con comunicación HTTPS segura.

## 🌐 Compatibilidad Multiplataforma

Robot Runner funciona de manera consistente en **Windows**, **Linux** y **macOS**. Las funciones de control de procesos (pausar, reanudar, detener) utilizan `psutil` para garantizar comportamiento uniforme en todas las plataformas.

| Plataforma | Estado | Versión Mínima |
|------------|--------|----------------|
| Windows | ✅ Totalmente soportado | Windows 10+ |
| Linux | ✅ Totalmente soportado | Kernel 3.x+ |
| macOS | ✅ Totalmente soportado | 10.14 (Mojave)+ |

Ver [Documentación de Compatibilidad](docs/CROSS-PLATFORM.md) para detalles técnicos.

## 📁 Estructura del Proyecto

```
robotrunner_windows/
├── run.py                  # Entry point principal
├── config.json             # Configuración del robot
├── app.spec                # Configuración PyInstaller
├── requirements.txt        # Dependencias Python
│
├── src/                    # Código fuente del servidor
│   ├── __init__.py         # Inicialización del paquete
│   ├── app.py              # Aplicación Flask + Gunicorn
│   ├── server.py           # Lógica del servidor
│   ├── robot.py            # Wrapper de ejecución de robots
│   ├── config.py           # Gestión de configuración
│   └── emisor.py           # Streaming de pantalla
│
├── ssl/                    # Certificados SSL/TLS
│   ├── ca-cert.pem         # Certificado raíz CA (compartir con orquestador)
│   ├── ca-key.pem          # Clave privada CA (MANTENER SEGURA)
│   ├── ca-config.cnf       # Configuración OpenSSL para CA
│   ├── cert.pem            # Certificado del robot actual
│   ├── key.pem             # Clave privada del robot actual
│   └── generated/          # Certificados generados por robot
│       └── robot-X/        # Directorio por robot
│
├── scripts/                # Scripts de utilidad
│   ├── create_ca.sh        # Crear Certificate Authority
│   ├── generate_robot_cert.sh  # Generar certificado por robot
│   ├── verify_certs.sh     # Verificar certificados
│   ├── setup_machine_tunnel.py # Configurar túnel para nueva máquina
│   ├── start_tunnel.py     # Iniciar túnel de Cloudflare
│   ├── stop_tunnel.py      # Detener túnel de Cloudflare
│   └── tunnel_status.py    # Verificar estado del túnel
│
├── docs/                   # Documentación
│   ├── TECHNICAL-DOCUMENTATION.md    # Documentación técnica
│   ├── FUNCTIONAL-DOCUMENTATION.md   # Guía de usuario
│   ├── CROSS-PLATFORM.md             # Compatibilidad multiplataforma
│   ├── CA-README.md                  # Guía completa del sistema CA
│   ├── CLOUDFLARE-TUNNEL.md          # Guía completa del túnel de Cloudflare
│   └── QUICK-START-TUNNEL.md         # Inicio rápido con túnel
│
├── templates/              # Plantillas HTML Flask
│   ├── login.html          # Login con token
│   ├── connected.html      # Pantalla principal
│   ├── settings.html       # Configuración del servidor
│   └── stream_view.html    # Vista de streaming de pantalla
│
├── static/                 # Archivos estáticos (CSS, JS, imágenes)
│
├── resources/              # Recursos de la aplicación
│   └── logo.ico            # Icono de la aplicación
│
└── Robots/                 # Directorio de scripts de robots
    └── robot.py            # Script del robot a ejecutar
```

## 🚀 Inicio Rápido

### Opción A: Con Túnel de Cloudflare (Recomendado) 🌐

**Ventajas:**
- ✅ URL única por máquina: `{machine_id}.automatehub.es`
- ✅ Sin configuración de firewall
- ✅ SSL automático
- ✅ Gratuito
- ✅ Identificación automática por machine_id

**Configurar por primera vez:**
```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar túnel automáticamente (lee machine_id del config.json, NO lo modifica)
python3 scripts/setup_machine_tunnel.py
```

**Uso diario:**
```bash
# Terminal 1: Iniciar el túnel
python3 scripts/start_tunnel.py

# Terminal 2: Iniciar Robot Runner
python run.py
```

¡Listo! Tu robot estará en: `https://{machine_id}.automatehub.es`

Ejemplo: Machine ID `38PPU1Z6ZE5C` → `https://38ppu1z6ze5c.automatehub.es`

📖 Ver [Guía Rápida del Túnel](docs/QUICK-START-TUNNEL.md) | [Documentación Completa](docs/CLOUDFLARE-TUNNEL.md)

---

### Opción B: Conexión Directa (Tradicional)

### 1. Instalación de Dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar Certificados SSL

**Primera vez (crear CA):**
```bash
./scripts/create_ca.sh
```

**Generar certificado para este robot:**
```bash
./scripts/generate_robot_cert.sh robot-1 192.168.1.100
```

### 3. Configurar la Aplicación

Edita `config.json` o ejecuta la aplicación y configúrala desde la interfaz web:

**Para túnel de Cloudflare:**
```json
{
    "url": "http://127.0.0.1:8088/",
    "token": "tu-token-del-orquestador",
    "machine_id": "TU-MACHINE-ID",
    "license_key": "TU-LICENSE-KEY",
    "ip": "robot.automatehub.es",
    "port": "443"
}
```

**Para conexión directa:**
```json
{
    "url": "http://192.168.1.50:8088/",
    "token": "tu-token-del-orquestador",
    "machine_id": "TU-MACHINE-ID",
    "license_key": "TU-LICENSE-KEY",
    "ip": "192.168.1.100",
    "port": "5055"
}
```

### 4. Ejecutar la Aplicación

**Interfaz web (por defecto):**
```bash
python run.py
```

Accede a `https://localhost:5055` e ingresa el token configurado en `config.json`.

**Modo servidor sin interfaz web:**
```bash
python run.py --server-only
```

**Con argumentos:**
```bash
python run.py --machine_id=ABC123 --license_key=XYZ789
```

### 5. Configuración por Línea de Comandos

Robot Runner soporta configuración completa por CLI, permitiendo automatizar deployments y configurar sin editar archivos.

#### Ver configuración actual
```bash
python run.py --show-config
```

#### Configurar parámetros del servidor
```bash
# Configurar y guardar en config.json
python run.py \
  --machine_id=ABC123 \
  --license_key=XYZ789 \
  --token=mi-token-secreto \
  --url=https://console.example.com \
  --port=5055 \
  --save

# Usar configuración temporal (solo esta sesión, no guardar)
python run.py \
  --machine_id=TEST123 \
  --port=8080 \
  --no-save \
  --server-only
```

#### Gestión del túnel de Cloudflare
```bash
# Ver estado del túnel
python run.py --tunnel-status

# Configurar túnel automáticamente
python run.py --machine_id=ABC123 --setup-tunnel

# Iniciar túnel
python run.py --start-tunnel

# Detener túnel
python run.py --stop-tunnel

# Configurar subdominio personalizado
python run.py \
  --tunnel-subdomain=mi-robot \
  --machine_id=ABC123 \
  --setup-tunnel
```

#### Argumentos disponibles

**Comandos especiales:**
- `--show-config`: Muestra la configuración actual
- `--tunnel-status`: Estado del túnel de Cloudflare
- `--setup-tunnel`: Configura el túnel automáticamente
- `--start-tunnel`: Inicia el túnel
- `--stop-tunnel`: Detiene el túnel

**Configuración del servidor:**
- `--url <URL>`: URL del orquestador
- `--token <TOKEN>`: Token de autenticación
- `--machine_id <ID>`: ID único de la máquina
- `--license_key <KEY>`: License key
- `--ip <IP>`: IP pública
- `--port <PORT>`: Puerto del servidor
- `--folder <PATH>`: Directorio de robots

**Túnel Cloudflare:**
- `--tunnel-subdomain <NAME>`: Subdominio personalizado
- `--tunnel-id <ID>`: ID del túnel

**Opciones de ejecución:**
- `--server-only`: Solo servidor (sin GUI web)
- `--save`: Guardar configuración en config.json
- `--no-save`: No guardar (solo para esta sesión)

#### Ejemplos de uso

**Despliegue automatizado:**
```bash
#!/bin/bash
# Script de despliegue automatizado

python run.py \
  --machine_id=$MACHINE_ID \
  --license_key=$LICENSE_KEY \
  --token=$AUTH_TOKEN \
  --url=$ORCHESTRATOR_URL \
  --setup-tunnel \
  --save

python run.py --start-tunnel
python run.py --server-only
```

**Testing con configuración temporal:**
```bash
# Probar con puerto diferente sin modificar config.json
python run.py --port=9999 --no-save
```

**Configuración rápida de nueva máquina:**
```bash
# Un solo comando para configurar todo
python run.py \
  --machine_id=ROBOT001 \
  --license_key=LIC-123-456 \
  --token=my-secret-token \
  --url=https://console.mycompany.com \
  --setup-tunnel \
  --save \
  --start-tunnel
```

### 6. Empaquetar con PyInstaller

```bash
pyinstaller app.spec
```

El ejecutable estará en `dist/RobotRunner/`

## 📚 Documentación

- **[Autenticación de API](docs/API-AUTHENTICATION.md)** - Sistema de tokens
- **[Inicio Rápido con Túnel](docs/QUICK-START-TUNNEL.md)** - Configuración rápida con Cloudflare 🚀
- **[Túnel de Cloudflare](docs/CLOUDFLARE-TUNNEL.md)** - Guía completa del túnel
- **[Guía de Usuario](docs/FUNCTIONAL-DOCUMENTATION.md)** - Instalación, configuración y uso
- **[Documentación Técnica](docs/TECHNICAL-DOCUMENTATION.md)** - Arquitectura, API y componentes
- **[Compatibilidad Multiplataforma](docs/CROSS-PLATFORM.md)** - Detalles de implementación multiplataforma
- **[Sistema CA](docs/CA-README.md)** - Gestión de certificados SSL

## 🔐 Seguridad

### Autenticación por Token

Robot Runner requiere un token de autenticación para todas las peticiones API:

```python
import requests

headers = {'Authorization': 'Bearer tu-token-secreto'}
response = requests.get(
    'https://robot.example.com/status',
    headers=headers,
    params={'machine_id': 'ID', 'license_key': 'KEY'}
)
```

**Configuración del Token:**
- Desde la interfaz web: Ir a `/settings` → Campo "Token de Autenticación"
- Desde archivo: Editar `config.json` → Campo `"token"`

📖 Ver [Documentación de Autenticación](docs/API-AUTHENTICATION.md) para más detalles

### SSL/TLS

Robot Runner utiliza un sistema de Certificate Authority (CA) propio:

1. **CA Raíz** - Crea una vez, compartida entre todos los robots
2. **Certificados por Robot** - Cada robot tiene su certificado único
3. **Validación en Orquestador** - El orquestador valida todos los certificados con el CA

### Instalación del CA en el Orquestador

```bash
# Copiar el certificado CA al orquestador
scp ssl/ca-cert.pem user@orchestrator:/opt/certs/robot-ca.pem
```

```python
# En el código del orquestador
import requests

response = requests.get(
    'https://192.168.1.100:5055/status',
    params={'machine_id': 'ID', 'license_key': 'KEY'},
    verify='/opt/certs/robot-ca.pem'  # Usar CA para validar
)
```

## 🛠️ Scripts Útiles

### Túnel de Cloudflare

```bash
# Configurar por primera vez (NO modifica config.json)
python3 scripts/setup_machine_tunnel.py

# Iniciar túnel
python3 scripts/start_tunnel.py

# Ver estado del túnel
python3 scripts/tunnel_status.py

# Detener túnel
python3 scripts/stop_tunnel.py
```

### Certificados SSL

```bash
# Crear Certificate Authority (una sola vez)
./scripts/create_ca.sh

# Generar certificado para un nuevo robot
./scripts/generate_robot_cert.sh robot-2 192.168.1.101 10.0.0.50

# Verificar certificados
./scripts/verify_certs.sh
```

## 📡 API Endpoints

**⚠️ Autenticación Requerida**: Todos los endpoints de API requieren un token de autenticación.

| Endpoint | Método | Descripción | Autenticación |
|----------|--------|-------------|---------------|
| `/status` | GET | Consultar estado del robot | 🔒 Token + Machine ID + License Key |
| `/execution` | GET | Estado de ejecución actual | 🔒 Token |
| `/run` | POST | Iniciar ejecución de robot | 🔒 Token |
| `/stop` | GET | Detener ejecución actual | 🔒 Token |
| `/pause` | GET | Pausar ejecución | 🔒 Token |
| `/resume` | GET | Reanudar ejecución pausada | 🔒 Token |
| `/block` | GET | Bloquear robot manualmente | 🔒 Token |

**Ejemplo de uso con token:**
```python
import requests

headers = {'Authorization': 'Bearer TU_TOKEN_AQUI'}
response = requests.get('https://robot.example.com/status', headers=headers)
```

Ver [Documentación de Autenticación](docs/API-AUTHENTICATION.md) para detalles completos.

## 🔧 Tecnologías

- **Flask** - Framework web
- **Gunicorn** - Servidor WSGI con SSL
- **OpenSSL** - Gestión de certificados
- **PyInstaller** - Empaquetado de la aplicación
- **Cloudflare Tunnel** - Túnel seguro con subdominios únicos

## ⚙️ Configuración Avanzada

### Cambiar Puerto

Edita `config.json`:
```json
{
    "port": "8443"
}
```

### Ejecutar como Servicio

**Linux (systemd):**
```bash
sudo cp robotrunner.service /etc/systemd/system/
sudo systemctl enable robotrunner
sudo systemctl start robotrunner
```

**Windows (Task Scheduler):**
- Crear tarea programada
- Ejecutar al inicio del sistema
- Programa: `RobotRunner.exe --server-only`

## 🐛 Resolución de Problemas

### Error de certificado SSL
```bash
# Regenerar certificados
./scripts/generate_robot_cert.sh robot-1 $(curl -s ifconfig.me)
```

### Puerto en uso
```bash
# Linux/macOS
lsof -ti:5055 | xargs kill -9

# Windows (PowerShell como Admin)
Get-Process -Id (Get-NetTCPConnection -LocalPort 5055).OwningProcess | Stop-Process
```

### Ver logs del servidor
```bash
# macOS/Linux
tail -f /tmp/server.log

# Windows
type %TEMP%\server.log
```

## 📝 Licencia

[Especificar licencia]

## 👥 Contribuir

[Instrucciones para contribuir]

## 📧 Soporte

Para problemas o preguntas, consulta la [Documentación Funcional](docs/FUNCTIONAL-DOCUMENTATION.md) o abre un issue.

---

## 🌐 Configuración del Túnel de Cloudflare

Robot Runner utiliza túneles de Cloudflare con subdominios únicos por máquina:

- **URL Pública:** `https://{machine_id}.automatehub.es` (único por máquina)
- **Formato:** Machine ID en lowercase + `.automatehub.es`
- **Ejemplo:** Machine ID `38PPU1Z6ZE5C` → `https://38ppu1z6ze5c.automatehub.es`
- **Tunnel ID:** `3d7de42c-4a8a-4447-b14f-053cc485ce6b` (compartido)
- **Puerto Local:** `5055` (HTTPS)

### Configurar nueva máquina:
```bash
python3 scripts/setup_machine_tunnel.py  # Lee machine_id (NO modifica config.json)
```

### Uso diario:
```bash
python3 scripts/start_tunnel.py  # Inicia el túnel
python run.py                    # Inicia Robot Runner
```

Cada máquina tendrá automáticamente su propio subdominio único basado en su `machine_id`.

Ver [documentación completa del túnel](docs/CLOUDFLARE-TUNNEL.md) para más detalles.

---

**Última actualización:** 2025-12-23
**Versión:** 2.0.0 (Interfaz web + soporte Cloudflare Tunnel)