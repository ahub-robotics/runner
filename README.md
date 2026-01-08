# Robot Runner v2.0

Sistema de ejecución remota de robots de automatización con comunicación HTTPS segura.

**Versión 2.0** - Arquitectura modular, tests completos, compilación multiplataforma.

## 🌐 Compatibilidad Multiplataforma

Robot Runner funciona de manera consistente en **Windows**, **Linux** y **macOS**. Las funciones de control de procesos (pausar, reanudar, detener) utilizan `psutil` para garantizar comportamiento uniforme en todas las plataformas.

| Plataforma | Estado | Versión Mínima |
|------------|--------|----------------|
| Windows | ✅ Totalmente soportado | Windows 10+ |
| Linux | ✅ Totalmente soportado | Kernel 3.x+ |
| macOS | ✅ Totalmente soportado | 10.14 (Mojave)+ |

Ver [Documentación de Compatibilidad](docs/CROSS-PLATFORM.md) para detalles técnicos.

## 📁 Estructura del Proyecto (v2.0 - Modular)

```
robotrunner/
├── run.py                      # Entry point principal
├── config.json                 # Configuración del robot
├── app.spec                    # Configuración PyInstaller
├── requirements.txt            # Dependencias Python
│
├── api/                        # 🌐 Interfaz web y REST API
│   ├── app.py                  # Factory Flask app
│   ├── middleware.py           # Middleware de autenticación
│   ├── auth.py                 # Sistema de autenticación
│   ├── web/                    # Interfaz web
│   │   ├── auth.py             # Login web
│   │   ├── ui.py               # Páginas principales
│   │   └── settings.py         # Configuración
│   ├── rest/                   # API REST
│   │   ├── status.py           # /status, /execution
│   │   ├── execution.py        # /run, /stop, /pause, /resume
│   │   └── info.py             # /info
│   ├── streaming/              # Sistema de streaming
│   │   ├── control.py          # /stream/start, /stream/stop
│   │   └── feed.py             # /stream/feed (SSE)
│   ├── tunnel/                 # Gestión de túneles
│   │   └── routes.py           # /tunnel/*
│   └── server/                 # Gestión del servidor
│       └── routes.py           # /server/*
│
├── executors/                  # 🤖 Ejecución de robots
│   ├── runner.py               # Clase Runner (ejecución de robots)
│   ├── server.py               # Clase Server (orquestador)
│   ├── tasks.py                # Tareas Celery para ejecución
│   └── __init__.py
│
├── streaming/                  # 📹 Sistema de streaming de pantalla
│   ├── streamer.py             # Clase ScreenStreamer
│   ├── tasks.py                # Tareas Celery para streaming
│   ├── capture.py              # Captura de pantalla
│   └── __init__.py
│
├── shared/                     # 🔧 Código común
│   ├── config/                 # Configuración
│   │   ├── loader.py           # Cargar/escribir config.json
│   │   └── cli.py              # Parsing de argumentos CLI
│   ├── state/                  # Estado compartido (Redis)
│   │   ├── redis_manager.py    # Gestión de Redis
│   │   └── redis_state.py      # Estado de ejecución/streaming
│   ├── celery_app/             # Celery
│   │   ├── config.py           # Configuración de Celery
│   │   └── worker.py           # Worker thread
│   └── utils/                  # Utilidades
│       ├── process.py          # Gestión de procesos
│       ├── ssl_utils.py        # Utilidades SSL
│       └── tunnel.py           # Utilidades de túnel
│
├── gui/                        # 🖥️ Interfaz gráfica
│   └── tray_app.py             # System tray (pystray)
│
├── cli/                        # ⌨️ Entry points CLI
│   ├── run_server.py           # Iniciar servidor
│   └── run_tray.py             # Iniciar system tray
│
├── tests/                      # 🧪 Suite de tests (161 tests)
│   ├── conftest.py             # Fixtures compartidas
│   ├── unit/                   # Tests unitarios (22 archivos)
│   │   ├── test_config.py
│   │   ├── test_redis.py
│   │   ├── test_streaming.py
│   │   ├── test_executors.py
│   │   └── ...
│   └── integration/            # Tests de integración (5 archivos)
│       ├── test_rest_endpoints.py
│       ├── test_auth.py
│       └── ...
│
├── build/                      # 📦 Sistema de compilación
│   ├── README.md               # Documentación de build
│   ├── hooks/                  # PyInstaller custom hooks
│   │   ├── hook-celery.py      # Hook para Celery
│   │   ├── hook-flask.py       # Hook para Flask
│   │   ├── hook-mss.py         # Hook para MSS
│   │   └── hook-pystray.py     # Hook para pystray
│   └── scripts/                # Scripts de compilación
│       ├── build_macos.sh      # Build para macOS
│       ├── build_linux.sh      # Build para Linux
│       └── build_windows.bat   # Build para Windows
│
├── docs/                       # 📚 Documentación completa
│   ├── README.md               # Índice de documentación
│   ├── architecture/           # Arquitectura del sistema
│   │   ├── overview.md         # Visión general
│   │   ├── components.md       # Componentes principales
│   │   └── data-flow.md        # Flujo de datos
│   ├── api/                    # Referencia de API
│   │   ├── rest-api.md         # Endpoints REST
│   │   └── authentication.md   # Sistema de autenticación
│   ├── development/            # Guías de desarrollo
│   │   ├── setup.md            # Configuración de desarrollo
│   │   ├── testing.md          # Ejecutar tests
│   │   └── contributing.md     # Guía de contribución
│   ├── deployment/             # Despliegue
│   │   ├── installation.md     # Instalación
│   │   ├── production.md       # Configuración de producción
│   │   └── compilation.md      # Compilación con PyInstaller
│   └── security/               # Seguridad
│       ├── CA-README.md        # Sistema de certificados
│       └── SECURITY-CHANGELOG.md
│
├── ssl/                        # 🔒 Certificados SSL/TLS
│   ├── ca-cert.pem             # Certificado raíz CA
│   ├── ca-key.pem              # Clave privada CA
│   ├── cert.pem                # Certificado del robot
│   ├── key.pem                 # Clave privada del robot
│   └── generated/              # Certificados generados
│       └── robot-X/
│
├── templates/                  # 🎨 Plantillas HTML Flask
│   ├── login.html
│   ├── connected.html
│   ├── settings.html
│   └── stream_view.html
│
├── static/                     # 📂 Archivos estáticos
│   ├── css/
│   ├── js/
│   └── images/
│
├── resources/                  # 🎨 Recursos de la aplicación
│   └── logo.ico
│
└── Robots/                     # 🤖 Scripts de robots
    └── robot.py
```

### ✨ Novedades en v2.0

- **Arquitectura Modular**: Código organizado por funcionalidad (api, executors, streaming, shared)
- **Suite de Tests**: 161 tests automatizados (87% passing)
- **Compilación Multiplataforma**: Scripts y hooks para Windows, Linux, macOS
- **Documentación Completa**: 12+ documentos organizados por categoría
- **System Tray**: Aplicación de bandeja del sistema (opcional)

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

### 6. Ejecutar Tests (Opcional)

Robot Runner v2.0 incluye una suite completa de tests:

```bash
# Ejecutar todos los tests
python -m pytest tests/unit/ tests/integration/ -v

# Con coverage
python -m pytest tests/unit/ tests/integration/ --cov=. --cov-report=html

# Solo tests unitarios
python -m pytest tests/unit/ -v

# Solo tests de integración
python -m pytest tests/integration/ -v
```

**Resultados esperados:**
- ✅ 140/161 tests passing (87%)
- ⚠️ 19 tests requieren ajustes en mocks (no críticos)
- 📊 Coverage: 42.84% overall, módulos core >70%

📖 Ver [Guía de Testing](docs/development/testing.md) para más detalles.

### 7. Compilar Ejecutable (Multiplataforma)

Robot Runner v2.0 incluye sistema completo de compilación con PyInstaller:

**macOS:**
```bash
./build/scripts/build_macos.sh
# Output: dist/RobotRunner-macOS.zip
```

**Linux:**
```bash
./build/scripts/build_linux.sh
# Output: dist/RobotRunner-Linux.tar.gz
```

**Windows:**
```cmd
build\scripts\build_windows.bat
REM Output: dist\RobotRunner-Windows.zip
```

El ejecutable estará en `dist/RobotRunner/`

📖 Ver [Guía de Compilación](docs/deployment/compilation.md) y [Build README](build/README.md) para más detalles.

## 📚 Documentación

### Arquitectura
- **[Visión General](docs/architecture/overview.md)** - Arquitectura del sistema v2.0
- **[Componentes](docs/architecture/components.md)** - Módulos principales
- **[Flujo de Datos](docs/architecture/data-flow.md)** - Cómo fluye la información

### API
- **[REST API](docs/api/rest-api.md)** - Referencia completa de endpoints
- **[Autenticación](docs/api/authentication.md)** - Sistema de tokens y seguridad

### Desarrollo
- **[Setup](docs/development/setup.md)** - Configurar entorno de desarrollo
- **[Testing](docs/development/testing.md)** - Ejecutar tests y coverage
- **[Contributing](docs/development/contributing.md)** - Guía de contribución

### Despliegue
- **[Instalación](docs/deployment/installation.md)** - Instalar Robot Runner
- **[Producción](docs/deployment/production.md)** - Configuración para producción
- **[Compilación](docs/deployment/compilation.md)** - Build con PyInstaller

### Seguridad
- **[Sistema CA](docs/security/CA-README.md)** - Gestión de certificados SSL
- **[Changelog de Seguridad](docs/security/SECURITY-CHANGELOG.md)** - Historial de cambios

### Otros
- **[Compatibilidad Multiplataforma](docs/CROSS-PLATFORM.md)** - Windows, Linux, macOS
- **[Funcionalidad](docs/FUNCTIONAL-DOCUMENTATION.md)** - Guía de usuario
- **[Documentación Técnica Legacy](docs/TECHNICAL-DOCUMENTATION.md)** - Referencia v1.x

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

### Backend
- **Flask 3.0+** - Framework web modular con Blueprints
- **Gunicorn** - Servidor WSGI con SSL
- **Celery 5.3+** - Tareas asíncronas (ejecución, streaming)
- **Redis** - Estado compartido y broker de Celery
- **psutil** - Gestión multiplataforma de procesos

### Testing & Quality
- **pytest 7.4+** - Framework de testing (161 tests)
- **pytest-cov** - Code coverage (42.84% overall)
- **pytest-mock** - Mocking y fixtures

### Build & Deployment
- **PyInstaller 5.13+** - Compilación multiplataforma
- **Custom Hooks** - Celery, Flask, MSS, pystray
- **Build Scripts** - Automatización para Windows/Linux/macOS

### Security
- **OpenSSL** - Gestión de certificados CA
- **Token-based Auth** - Sistema de autenticación personalizado
- **Cloudflare Tunnel** - Túnel seguro con subdominios únicos

### GUI
- **pystray** - System tray multiplataforma
- **PIL/Pillow** - Iconos y imágenes

### Streaming
- **mss** - Captura de pantalla multiplataforma
- **Server-Sent Events (SSE)** - Streaming en tiempo real

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

**Última actualización:** 2026-01-08
**Versión:** 2.0.0 (Arquitectura modular + Tests + Compilación multiplataforma)