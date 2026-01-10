# 🪟 Robot Runner - Guía de Instalación para Windows

Esta guía cubre la instalación y configuración de Robot Runner en Windows, incluyendo RabbitMQ y las diferencias con Linux/macOS.

---

## 📋 Tabla de Contenidos

1. [Requisitos del Sistema](#requisitos-del-sistema)
2. [Instalación de Dependencias](#instalación-de-dependencias)
3. [Configuración de RabbitMQ](#configuración-de-rabbitmq)
4. [Instalación del Proyecto](#instalación-del-proyecto)
5. [Ejecutar el Servidor](#ejecutar-el-servidor)
6. [Diferencias con Linux/macOS](#diferencias-con-linuxmacos)
7. [Solución de Problemas](#solución-de-problemas)

---

## 🖥️ Requisitos del Sistema

### Mínimos
- **SO**: Windows 10 (64-bit) o superior
- **Python**: 3.8 o superior
- **RAM**: 4GB mínimo (8GB recomendado)
- **Disco**: 1GB espacio libre

### Recomendados
- **SO**: Windows 11
- **Python**: 3.10 o 3.11
- **RAM**: 8GB o más
- **Disco**: 2GB+ espacio libre

---

## 📦 Instalación de Dependencias

### 1. Python

Descarga e instala Python desde [python.org](https://www.python.org/downloads/):

```powershell
# Verificar instalación
python --version
# Debe mostrar: Python 3.x.x

# Verificar pip
pip --version
```

**Importante**: Durante la instalación, marca la opción "Add Python to PATH"

### 2. Git (Opcional)

Descarga desde [git-scm.com](https://git-scm.com/download/win) si vas a clonar el repositorio.

### 3. Visual C++ Redistributable

Necesario para algunas dependencias. Descarga desde:
[Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)

---

## 🐰 Configuración de RabbitMQ

RabbitMQ es el message broker usado en Windows (en lugar de Redis).

### Instalación

#### Opción A: Usando Chocolatey (Recomendado)

```powershell
# Instalar Chocolatey primero (si no lo tienes)
# Abrir PowerShell como Administrador
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Instalar Erlang (dependencia de RabbitMQ)
choco install erlang -y

# Instalar RabbitMQ
choco install rabbitmq -y
```

#### Opción B: Instalación Manual

1. **Descargar e instalar Erlang**:
   - Visita: https://www.erlang.org/downloads
   - Descarga el instalador de Windows
   - Ejecuta e instala con opciones por defecto

2. **Descargar e instalar RabbitMQ**:
   - Visita: https://www.rabbitmq.com/download.html
   - Descarga el instalador de Windows
   - Ejecuta e instala con opciones por defecto

### Iniciar RabbitMQ

```powershell
# Opción 1: Como servicio (Recomendado)
net start RabbitMQ

# Opción 2: Desde Services
# 1. Win + R
# 2. Escribir: services.msc
# 3. Buscar "RabbitMQ"
# 4. Clic derecho → Iniciar

# Opción 3: Desde RabbitMQ Command Prompt
rabbitmq-server start
```

### Habilitar Management Plugin

```powershell
# Abrir RabbitMQ Command Prompt como Administrador
cd "C:\Program Files\RabbitMQ Server\rabbitmq_server-3.x.x\sbin"
rabbitmq-plugins enable rabbitmq_management
```

### Verificar Instalación

```powershell
# Ver estado
rabbitmqctl status

# Acceder a Management UI
# Abrir navegador en: http://localhost:15672
# Usuario: guest
# Contraseña: guest
```

**Puertos utilizados**:
- **5672**: Puerto AMQP (conexiones de aplicación)
- **15672**: Puerto Management UI (interfaz web)

---

## 🚀 Instalación del Proyecto

### 1. Obtener el código

```powershell
# Opción A: Clonar con Git
git clone https://github.com/tu-usuario/robotrunner_windows.git
cd robotrunner_windows

# Opción B: Descargar ZIP
# Descargar y extraer el archivo ZIP
# Navegar a la carpeta extraída
```

### 2. Crear entorno virtual

```powershell
# Crear venv
python -m venv venv

# Activar venv
.\venv\Scripts\activate

# Deberías ver (venv) en el prompt
```

### 3. Instalar dependencias

```powershell
# Instalar todas las dependencias
pip install -r requirements.txt

# Verificar instalaciones clave
pip show waitress celery flask
```

### 4. Crear estructura de carpetas

```powershell
# Crear carpeta Robot en el home del usuario
mkdir $env:USERPROFILE\Robot
mkdir $env:USERPROFILE\Robot\logs
mkdir $env:USERPROFILE\Robot\ssl

# Verificar
dir $env:USERPROFILE\Robot
```

### 5. Crear archivo de configuración

```powershell
# Crear config.json
$configPath = "$env:USERPROFILE\Robot\config.json"
$configContent = @"
{
  "machine_id": "windows-robot-001",
  "token": "your-secure-token-here",
  "port": 5055,
  "folder": "$env:USERPROFILE\\Robot\\robots",
  "url": "http://localhost:5055",
  "ip": "127.0.0.1"
}
"@

$configContent | Out-File -FilePath $configPath -Encoding UTF8

# Verificar
type $configPath
```

---

## ▶️ Ejecutar el Servidor

### Verificar configuración

```powershell
# Verificar que todo esté listo
python check_broker.py
```

Deberías ver:
```
✅ Broker:        OK (RabbitMQ en localhost:5672)
✅ Celery:        OK
✅ State Backend: OK (SQLite)
```

### Iniciar el servidor

```powershell
# Método 1: Script principal (detecta Windows automáticamente)
python run.py

# Método 2: Script específico de Windows
python cli/run_server_windows.py

# Método 3: Usando módulo
python -m cli.run_server_windows
```

El servidor mostrará:
```
======================================================================
🚀 Iniciando Robot Runner Server (Windows)...
======================================================================
📍 Port: 5055
🔑 Machine ID: windows-robot-001
🌐 URL: http://0.0.0.0:5055
🖥️  Servidor: Waitress (compatible Windows)
======================================================================
```

### Detener el servidor

```powershell
# Presionar Ctrl+C en la terminal donde está corriendo
```

---

## 🔄 Diferencias con Linux/macOS

| Componente | Windows | Linux/macOS |
|------------|---------|-------------|
| **Servidor WSGI** | Waitress | Gunicorn |
| **Message Broker** | RabbitMQ | Redis |
| **State Backend** | SQLite | Redis |
| **Puerto Broker** | 5672 (AMQP) | 6378 (Redis) |
| **Management UI** | http://localhost:15672 | N/A |
| **Comando Inicio** | `net start RabbitMQ` | `brew services start redis` |

### ¿Por qué estas diferencias?

1. **Gunicorn → Waitress**: Gunicorn usa `fork()` que no existe en Windows
2. **Redis → RabbitMQ**: Redis tiene problemas de rendimiento en Windows
3. **Redis → SQLite**: SQLite es más eficiente en Windows para estado local

---

## 🛠️ Solución de Problemas

### RabbitMQ no inicia

**Síntoma**: Error al iniciar RabbitMQ

**Soluciones**:
```powershell
# 1. Verificar que Erlang esté instalado
erl -version

# 2. Verificar servicios
services.msc
# Buscar "RabbitMQ" y verificar estado

# 3. Revisar logs de RabbitMQ
type "C:\Users\%USERNAME%\AppData\Roaming\RabbitMQ\log\*"

# 4. Reinstalar RabbitMQ
# Desinstalar desde Panel de Control
# Reinstalar siguiendo pasos anteriores
```

### Puerto 5672 ya en uso

**Síntoma**: `Error: Address already in use`

**Soluciones**:
```powershell
# 1. Ver qué proceso usa el puerto
netstat -ano | findstr ":5672"

# 2. Terminar proceso (reemplazar PID)
taskkill /PID <PID> /F

# 3. O cambiar puerto en configuración
# Editar: C:\Program Files\RabbitMQ Server\rabbitmq_server-3.x.x\etc\rabbitmq.conf
```

### Errores de importación de Python

**Síntoma**: `ModuleNotFoundError: No module named 'xxx'`

**Soluciones**:
```powershell
# 1. Verificar que venv está activado
# Deberías ver (venv) en el prompt

# 2. Reinstalar dependencias
pip install -r requirements.txt

# 3. Verificar módulo específico
pip show <nombre-modulo>

# 4. Actualizar pip
python -m pip install --upgrade pip
```

### Waitress no inicia

**Síntoma**: Error al ejecutar `run_server_windows.py`

**Soluciones**:
```powershell
# 1. Verificar instalación de Waitress
pip show waitress

# 2. Reinstalar Waitress
pip uninstall waitress
pip install waitress==2.1.2

# 3. Verificar puerto disponible
netstat -ano | findstr ":5055"
```

### Management UI no accesible

**Síntoma**: No se puede acceder a http://localhost:15672

**Soluciones**:
```powershell
# 1. Verificar que el plugin está habilitado
rabbitmq-plugins list
# Debe aparecer: [E*] rabbitmq_management

# 2. Habilitar plugin
rabbitmq-plugins enable rabbitmq_management

# 3. Reiniciar RabbitMQ
net stop RabbitMQ
net start RabbitMQ

# 4. Verificar firewall
# Windows Firewall → Permitir aplicación
# Buscar "RabbitMQ" y permitir
```

---

## 📚 Recursos Adicionales

### Documentación

- [RabbitMQ Windows Guide](https://www.rabbitmq.com/install-windows.html)
- [Waitress Documentation](https://docs.pylonsproject.org/projects/waitress/)
- [Python on Windows](https://docs.python.org/3/using/windows.html)

### Comandos Útiles

```powershell
# Ver todos los servicios de RabbitMQ
Get-Service | Where-Object {$_.Name -like "*rabbit*"}

# Logs del proyecto
type $env:USERPROFILE\Robot\logs\robot_runner.log

# Ver configuración de RabbitMQ
type "C:\Program Files\RabbitMQ Server\rabbitmq_server-3.x.x\etc\rabbitmq.conf"

# Limpiar colas de RabbitMQ
python cli/clear_redis_queue.py
```

### Monitoreo

```powershell
# Abrir Management UI
start http://localhost:15672

# Ver estado en tiempo real
rabbitmqctl list_queues
rabbitmqctl list_connections
rabbitmqctl list_channels

# Ver estadísticas
rabbitmqctl status
```

---

## 🎯 Checklist de Instalación

Usa este checklist para verificar que todo esté instalado correctamente:

- [ ] Python 3.8+ instalado
- [ ] Pip actualizado (`python -m pip install --upgrade pip`)
- [ ] Git instalado (opcional)
- [ ] Visual C++ Redistributable instalado
- [ ] Erlang instalado
- [ ] RabbitMQ instalado y corriendo
- [ ] Management plugin habilitado
- [ ] Entorno virtual creado y activado
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Carpeta `~/Robot` creada
- [ ] Archivo `config.json` creado
- [ ] `check_broker.py` ejecutado exitosamente
- [ ] Servidor inicia sin errores

---

## 🆘 Soporte

Si tienes problemas:

1. Ejecuta `python check_broker.py` para diagnóstico
2. Revisa los logs en `%USERPROFILE%\Robot\logs\`
3. Verifica RabbitMQ Management UI: http://localhost:15672
4. Consulta la sección "Solución de Problemas" arriba

---

**¡Feliz automatización! 🤖**