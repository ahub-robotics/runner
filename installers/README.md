# Instaladores de Robot Runner

Scripts de instalación automatizada para todas las plataformas.

## 📁 Estructura

```
installers/
├── windows/          # Scripts para Windows
│   ├── install_all.bat           # Ejecutar como Admin (doble clic)
│   ├── install_all.ps1           # Script maestro PowerShell
│   ├── install_dependencies.ps1  # Instala Chocolatey, Python, Git, etc.
│   ├── setup_python_env.ps1      # Crea virtualenv e instala requirements
│   └── setup_rabbitmq.ps1        # Configura RabbitMQ
│
├── linux/            # Scripts para Linux
│   ├── install_all.sh            # Script maestro
│   ├── install_dependencies.sh   # Instala Python, Git, RabbitMQ, etc.
│   ├── setup_python_env.sh       # Crea virtualenv e instala requirements
│   └── setup_rabbitmq.sh         # Configura RabbitMQ
│
├── macos/            # Scripts para macOS
│   ├── install_all.sh            # Script maestro
│   ├── install_dependencies.sh   # Instala Homebrew, Python, Git, etc.
│   ├── setup_python_env.sh       # Crea virtualenv e instala requirements
│   └── setup_rabbitmq.sh         # Configura RabbitMQ
│
└── common/           # Scripts multiplataforma
    └── (archivos comunes)
```

## 🚀 Instalación rápida

### Windows

1. **Ejecutar como Administrador**:
   - Haz clic derecho en `windows/install_all.bat`
   - Selecciona "Ejecutar como administrador"

2. O desde PowerShell (como Admin):
   ```powershell
   cd installers/windows
   .\install_all.ps1
   ```

### Linux

```bash
cd installers/linux
chmod +x install_all.sh
./install_all.sh
```

### macOS

```bash
cd installers/macos
chmod +x install_all.sh
./install_all.sh
```

## 📦 Qué se instala

### Dependencias del sistema

- **Windows**:
  - Chocolatey (gestor de paquetes)
  - Python 3.11
  - Git
  - Cloudflared
  - Erlang + RabbitMQ Server

- **Linux**:
  - Python 3.11
  - Git
  - Cloudflared
  - RabbitMQ (Docker o sistema según elección)

- **macOS**:
  - Homebrew (si no está instalado)
  - Python 3.11
  - Git
  - Cloudflared
  - RabbitMQ

### Entorno Python

- Virtualenv (`venv/`)
- Todas las dependencias de `requirements.txt`:
  - Flask
  - Celery
  - Waitress (Windows) / Gunicorn (Linux/macOS)
  - Pika (RabbitMQ)
  - Pillow
  - Y todas las demás...

### Configuración de servicios

- **RabbitMQ**:
  - Servicio iniciado automáticamente
  - Plugin de management habilitado
  - Interfaz web: http://localhost:15672
  - Usuario: `guest/guest` (o personalizado)

- **Cloudflare Tunnel** (opcional):
  - Configuración interactiva
  - Instalación como servicio
  - DNS automático

## 🔧 Instalación manual por pasos

Si prefieres ejecutar cada paso por separado:

### Windows

```powershell
# Paso 1: Dependencias del sistema
cd installers/windows
.\install_dependencies.ps1

# Paso 2: Entorno Python
.\setup_python_env.ps1

# Paso 3: RabbitMQ
.\setup_rabbitmq.ps1

# Paso 4 (opcional): Cloudflare Tunnel
cd ..\..
python setup_tunnel.py
```

### Linux/macOS

```bash
# Paso 1: Dependencias del sistema
cd installers/linux  # o macos
./install_dependencies.sh

# Paso 2: Entorno Python
./setup_python_env.sh

# Paso 3: RabbitMQ
./setup_rabbitmq.sh

# Paso 4 (opcional): Cloudflare Tunnel
cd ../..
python3 setup_tunnel.py
```

## ⚠️ Requisitos previos

### Windows
- Windows 10/11
- PowerShell 5.1 o superior
- Permisos de Administrador

### Linux
- Ubuntu 20.04+, Debian 11+, Fedora 35+, o Arch Linux
- sudo disponible
- Conexión a internet

### macOS
- macOS 11 (Big Sur) o superior
- Conexión a internet
- Espacio en disco: ~2GB

## 🐛 Solución de problemas

### Windows

**Error: "No se puede ejecutar scripts"**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Error: "No tienes permisos de Administrador"**
- Haz clic derecho en PowerShell → "Ejecutar como administrador"

**Chocolatey no se instala**
- Verifica que tienes conexión a internet
- Desactiva temporalmente el antivirus

### Linux

**Error: "Permission denied"**
```bash
chmod +x *.sh
```

**Docker no funciona**
```bash
sudo usermod -aG docker $USER
# Cierra sesión y vuelve a iniciar
```

### macOS

**Error: "Command not found: brew"**
- El script instala Homebrew automáticamente
- Si falla, instala manualmente: https://brew.sh

**Python 3.11 no se encuentra**
```bash
brew install python@3.11
brew link python@3.11
```

## 📝 Después de la instalación

1. **Activar el virtualenv**:
   - Windows: `.\venv\Scripts\Activate.ps1`
   - Linux/macOS: `source venv/bin/activate`

2. **Configurar Robot Runner**:
   - Edita `config.json` o crea `.env`
   - Añade `machine_id` y `token`

3. **Iniciar el servidor**:
   ```bash
   python main.py
   ```

4. **Verificar instalación**:
   - Servidor: http://localhost:8088
   - RabbitMQ: http://localhost:15672

## 🔒 Seguridad

- Los scripts no modifican configuraciones de seguridad del sistema
- Las contraseñas de RabbitMQ son configurables
- Los servicios escuchan solo en localhost por defecto
- SSL/TLS es opcional pero recomendado para producción

## 📚 Documentación adicional

- [README principal](../README.md)
- [Guía de configuración](../docs/configuration.md)
- [Solución de problemas](../docs/troubleshooting.md)

## 🤝 Contribuir

Si encuentras un problema o tienes una mejora:
1. Abre un issue en GitHub
2. Describe el error y tu sistema operativo
3. Incluye logs relevantes

## 📄 Licencia

Estos scripts son parte de Robot Runner y están bajo la misma licencia del proyecto.