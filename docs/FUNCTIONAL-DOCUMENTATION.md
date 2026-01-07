# Robot Runner - Guía de Usuario

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Requisitos del Sistema](#requisitos-del-sistema)
3. [Instalación](#instalación)
4. [Configuración Inicial](#configuración-inicial)
5. [Uso de la Aplicación](#uso-de-la-aplicación)
6. [Gestión de Certificados SSL](#gestión-de-certificados-ssl)
7. [Resolución de Problemas](#resolución-de-problemas)
8. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## Introducción

### ¿Qué es Robot Runner?

Robot Runner es una aplicación que permite ejecutar robots de automatización de forma remota desde un orquestador central. La aplicación actúa como un agente en la máquina local que recibe instrucciones del orquestador y ejecuta los procesos de automatización correspondientes.

### Características Principales

- **Ejecución Remota**: Ejecuta robots desde un orquestador central
- **Interfaz Gráfica**: Interfaz web integrada para configuración y monitoreo
- **Comunicación Segura**: Conexiones HTTPS con certificados SSL
- **Gestión de Estado**: Monitoreo en tiempo real del estado del robot
- **Control de Ejecución**: Capacidad de pausar, reanudar y detener ejecuciones

---

## Requisitos del Sistema

### Sistema Operativo

- Windows 10/11
- macOS 10.14 o superior
- Linux (Ubuntu 18.04+, Debian 10+, o distribuciones equivalentes)

### Hardware Mínimo

- **CPU**: Procesador dual-core de 2 GHz o superior
- **RAM**: 4 GB (8 GB recomendado)
- **Espacio en Disco**: 500 MB libres
- **Red**: Conexión a internet activa

### Software Requerido

- Python 3.8 o superior (si se ejecuta desde código fuente)
- Permisos de administrador para instalación

---

## Instalación

### Opción 1: Ejecutable Empaquetado (Recomendado)

1. **Descargar el Ejecutable**
   - Descarga el archivo `RobotRunner.exe` (Windows) o `RobotRunner` (macOS/Linux)
   - Guárdalo en una ubicación permanente (ej: `C:\Program Files\RobotRunner`)

2. **Instalar Certificados SSL**
   - El ejecutable incluye los certificados necesarios
   - No se requiere configuración adicional de SSL

3. **Ejecutar la Aplicación**
   - Windows: Doble clic en `RobotRunner.exe`
   - macOS/Linux: Abrir terminal y ejecutar `./RobotRunner`
   - En macOS, si aparece advertencia de seguridad: Sistema → Seguridad → "Abrir de todas formas"

### Opción 2: Desde Código Fuente

1. **Clonar el Repositorio**
   ```bash
   git clone <repository-url>
   cd robotrunner_windows
   ```

2. **Instalar Dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar Certificados SSL**
   ```bash
   # Crear CA (solo la primera vez)
   ./create_ca.sh

   # Generar certificado para este robot
   ./generate_robot_cert.sh robot-1 127.0.0.1 <IP-PÚBLICA>

   # Copiar certificados al directorio raíz
   cp certs/robot-1/robot-1-cert.pem cert.pem
   cp certs/robot-1/robot-1-key.pem key.pem
   ```

4. **Ejecutar la Aplicación**
   ```bash
   python app.py
   ```

---

## Configuración Inicial

### Primera Ejecución

Al ejecutar Robot Runner por primera vez, se abrirá automáticamente la interfaz de configuración en tu navegador.

### Pantalla de Configuración

La pantalla de configuración solicita los siguientes datos:

#### 1. URL del Orquestador
- **Campo**: Console URL
- **Descripción**: La dirección del servidor orquestador
- **Ejemplo**: `http://192.168.1.50:8088/`
- **Nota**: Incluye el protocolo (http:// o https://) y el puerto

#### 2. Token de Carpeta
- **Campo**: Folder Token
- **Descripción**: Token de autenticación para la carpeta de robots
- **Formato**: Cadena alfanumérica de 40 caracteres
- **Ejemplo**: `b82ababd99cb8c0fba61d8325ee4138c08b13745`
- **Dónde Obtenerlo**: En la consola del orquestador → Configuración de Carpeta

#### 3. ID de Máquina
- **Campo**: Machine ID
- **Descripción**: Identificador único de esta máquina en el orquestador
- **Formato**: Código alfanumérico de 12 caracteres
- **Ejemplo**: `38PPU1Z6ZE5C`
- **Dónde Obtenerlo**: En la consola del orquestador → Máquinas → Agregar Máquina

#### 4. Clave de Licencia
- **Campo**: License Key
- **Descripción**: Clave de licencia para esta máquina
- **Formato**: Cadena alfanumérica de 36 caracteres
- **Ejemplo**: `8ET9TIRBDADZ1QIFBNOTVQW5JYBTI4P0ER4N`
- **Dónde Obtenerlo**: En la consola del orquestador → Máquinas → Detalles de Máquina

#### 5. IP Pública
- **Campo**: IP Address
- **Descripción**: Dirección IP pública o local de esta máquina
- **Ejemplo**: `192.168.1.100` (LAN) o `203.0.113.10` (WAN)
- **Nota**: Se detecta automáticamente, pero puede modificarse

#### 6. Puerto
- **Campo**: Port
- **Descripción**: Puerto en el que escucha el servidor HTTPS
- **Valor Predeterminado**: `5055`
- **Nota**: Asegúrate de que este puerto esté disponible y no bloqueado por firewall

### Guardar Configuración

1. Completa todos los campos requeridos
2. Haz clic en el botón **"Connect"** o **"Conectar"**
3. Si los datos son correctos, serás redirigido a la pantalla principal
4. Si hay un error, aparecerá un mensaje en rojo indicando el problema

### Modificar Configuración Existente

Para cambiar la configuración después de la instalación inicial:

1. **Desde la Interfaz**:
   - Haz clic en el botón de desconexión en la pantalla principal
   - Esto te llevará a la pantalla de configuración

2. **Editando el Archivo**:
   - Cierra la aplicación
   - Edita el archivo `config.json` en el directorio de instalación
   - Guarda los cambios y reinicia la aplicación

---

## Uso de la Aplicación

### Pantalla Principal

Una vez configurado, la pantalla principal muestra:

- **Estado del Robot**: Indica si el robot está libre, ocupado, pausado o cerrado
- **Información de Conexión**: IP, puerto, y estado de conexión con el orquestador
- **Botón de Desconexión**: Para volver a la pantalla de configuración

### Estados del Robot

El robot puede estar en los siguientes estados:

| Estado | Descripción | Color Indicador |
|--------|-------------|----------------|
| **free** | Libre y listo para ejecutar tareas | Verde |
| **running** | Ejecutando un robot actualmente | Azul |
| **paused** | Ejecución pausada temporalmente | Amarillo |
| **blocked** | Bloqueado manualmente | Naranja |
| **closed** | Desconectado del orquestador | Rojo |

### Flujo de Trabajo Normal

1. **Robot en Espera**: El robot está en estado "free", esperando instrucciones
2. **Recepción de Tarea**: El orquestador envía una solicitud de ejecución
3. **Ejecución**: El robot cambia a estado "running" y ejecuta el proceso
4. **Finalización**: Al completar, el robot vuelve a estado "free"

### Control Manual

Aunque el control principal se realiza desde el orquestador, la aplicación responde a comandos remotos:

- **Detener Ejecución**: El orquestador puede detener la ejecución actual
- **Pausar**: Suspende temporalmente la ejecución
- **Reanudar**: Continúa una ejecución pausada
- **Bloquear**: Impide nuevas ejecuciones temporalmente

---

## Gestión de Certificados SSL

### ¿Por Qué Se Necesitan Certificados?

Los certificados SSL garantizan que:
- La comunicación entre el orquestador y el robot está encriptada
- El orquestador puede verificar la identidad del robot
- Los datos sensibles (credenciales, resultados) están protegidos

### Sistema de Certificados

Robot Runner utiliza un sistema de **Certificate Authority (CA)** propio:

```
CA Raíz (ca-cert.pem)
└── Certificado Robot 1 (cert.pem)
└── Certificado Robot 2 (cert.pem)
└── Certificado Robot N (cert.pem)
```

### Instalación del Certificado CA en el Orquestador

**IMPORTANTE**: El orquestador debe tener el certificado CA instalado para validar los robots.

1. **Localizar el Certificado CA**
   - Ubicación: `ca-cert.pem` en el directorio de instalación del primer robot
   - Este archivo debe generarse solo UNA VEZ

2. **Copiar al Orquestador**
   ```bash
   # En el servidor orquestador
   mkdir -p /opt/certs
   # Copiar ca-cert.pem desde el robot al orquestador
   cp ca-cert.pem /opt/certs/robot-ca.pem
   ```

3. **Configurar el Orquestador**
   - El código del orquestador debe usar `verify='/opt/certs/robot-ca.pem'`
   - Ver `orchestrator-example.py` para ejemplo de implementación

### Agregar un Nuevo Robot

Cuando instalas Robot Runner en una nueva máquina:

1. **Usa el Mismo CA**: No crees un nuevo CA, usa el existente
   ```bash
   # Copia ca-cert.pem y ca-key.pem del primer robot
   ```

2. **Genera Certificado para el Nuevo Robot**
   ```bash
   ./generate_robot_cert.sh robot-2 192.168.1.101
   cp certs/robot-2/robot-2-cert.pem cert.pem
   cp certs/robot-2/robot-2-key.pem key.pem
   ```

3. **No Actualices el Orquestador**: El orquestador ya tiene el CA y validará automáticamente el nuevo certificado

### Cambio de IP de un Robot

Si la IP de un robot cambia:

1. **Regenerar Certificado**
   ```bash
   ./generate_robot_cert.sh robot-1 <NUEVA-IP> 127.0.0.1
   ```

2. **Reemplazar Certificados**
   ```bash
   cp certs/robot-1/robot-1-cert.pem cert.pem
   cp certs/robot-1/robot-1-key.pem key.pem
   ```

3. **Reiniciar Robot Runner**

4. **No Requiere Cambios en el Orquestador**

### Verificar Certificados

Puedes verificar la validez de los certificados con:

```bash
./verify_certs.sh
```

Esto mostrará:
- Validez de la CA
- Validez de certificados de robots
- Fechas de expiración
- IPs autorizadas en cada certificado

---

## Resolución de Problemas

### El Robot No Se Conecta al Orquestador

**Síntoma**: La pantalla muestra estado "closed" o error de conexión.

**Soluciones**:

1. **Verificar Conectividad de Red**
   ```bash
   ping <IP-ORQUESTADOR>
   ```

2. **Verificar Configuración**
   - Revisa que la URL del orquestador sea correcta
   - Verifica que Machine ID y License Key sean correctos
   - Comprueba que no haya espacios adicionales en los campos

3. **Verificar Firewall**
   - Asegúrate de que el puerto 5055 esté abierto
   - Windows: Panel de Control → Firewall → Permitir aplicación
   - Linux: `sudo ufw allow 5055`
   - macOS: Preferencias del Sistema → Seguridad → Firewall

4. **Revisar Certificados**
   - Ejecuta `./verify_certs.sh` para verificar validez
   - Asegúrate de que `cert.pem` y `key.pem` existan

### Error de Certificado SSL

**Síntoma**: "SSL Certificate Verify Failed" o "hostname doesn't match"

**Soluciones**:

1. **Verificar CA en Orquestador**
   ```bash
   # En el servidor orquestador
   ls -l /opt/certs/robot-ca.pem
   ```

2. **Regenerar Certificado con IPs Correctas**
   ```bash
   ./generate_robot_cert.sh robot-1 <IP-ACTUAL> 127.0.0.1
   ```

3. **Verificar Fecha del Sistema**
   - Los certificados tienen fechas de validez
   - Asegúrate de que la fecha/hora del sistema sea correcta

### El Robot No Ejecuta Tareas

**Síntoma**: El orquestador envía tareas pero el robot permanece en "free"

**Soluciones**:

1. **Verificar Logs**
   - Busca archivos de log en el directorio de instalación
   - Revisa `/tmp/server.log` (Linux/macOS) o `%TEMP%\server.log` (Windows)

2. **Verificar Permisos**
   - El robot necesita permisos para ejecutar scripts
   - Verifica que el directorio `Robots/` exista y tenga los scripts necesarios

3. **Verificar Carpeta de Robots**
   - Asegúrate de que `robot.py` esté en el directorio `Robots/`
   - Verifica que las dependencias del robot estén instaladas

### El Puerto 5055 Ya Está en Uso

**Síntoma**: "Address already in use" o "Port 5055 is already in use"

**Soluciones**:

1. **Cerrar Instancia Anterior**
   - Windows: Administrador de Tareas → Procesar → RobotRunner.exe
   - Linux/macOS: `ps aux | grep python` y `kill <PID>`

2. **Cambiar Puerto**
   - Edita `config.json` y cambia el valor de "port"
   - Reinicia la aplicación
   - **IMPORTANTE**: Actualiza la configuración en el orquestador con el nuevo puerto

3. **Liberar Puerto**
   ```bash
   # Linux/macOS
   lsof -ti:5055 | xargs kill -9

   # Windows (PowerShell como Administrador)
   Get-Process -Id (Get-NetTCPConnection -LocalPort 5055).OwningProcess | Stop-Process
   ```

### Python Se Cierra Inesperadamente (macOS)

**Síntoma**: La aplicación se cierra sin mensaje de error en macOS

**Soluciones**:

1. **Verificar Variable de Entorno**
   - Esta solución ya está implementada en el código
   - Si compilaste desde fuente, asegúrate de tener la última versión de `app.py`

2. **Revisar Logs del Sistema**
   ```bash
   # Ver logs de crash
   cat ~/Library/Logs/DiagnosticReports/python*.crash
   ```

3. **Ejecutar desde Terminal**
   ```bash
   # Ver errores en tiempo real
   python app.py
   ```

### La Interfaz No Se Abre en el Navegador

**Síntoma**: La aplicación inicia pero no aparece ventana ni navegador

**Soluciones**:

1. **Abrir Manualmente**
   - Abre tu navegador
   - Ve a `https://127.0.0.1:5055/`
   - Acepta la advertencia de certificado (es normal para certificados auto-firmados)

2. **Verificar que el Servidor Esté Corriendo**
   ```bash
   # Debería responder con estado del robot
   curl -k https://127.0.0.1:5055/status?machine_id=<TU-ID>&license_key=<TU-KEY>
   ```

3. **Reinstalar pywebview**
   ```bash
   pip uninstall pywebview
   pip install pywebview
   ```

---

## Preguntas Frecuentes

### ¿Es seguro usar certificados auto-firmados?

**Sí**, en el contexto de una red interna corporativa. Los certificados auto-firmados proporcionan encriptación completa. La única diferencia con certificados comerciales es que no están validados por una autoridad externa. Para redes internas, el sistema de CA propio es más que suficiente.

### ¿Puedo usar múltiples robots en la misma máquina?

**No recomendado**. Cada instancia de Robot Runner necesita su propio puerto y certificado. Si necesitas ejecutar múltiples robots simultáneamente, considera:
- Usar máquinas virtuales separadas
- Configurar instancias con puertos diferentes (5055, 5056, 5057, etc.)

### ¿Cómo actualizo Robot Runner?

**Desde Ejecutable**:
1. Cierra la aplicación actual
2. Reemplaza el ejecutable con la nueva versión
3. Los certificados y `config.json` se mantienen

**Desde Código Fuente**:
```bash
git pull origin master
pip install -r requirements.txt --upgrade
```

### ¿Dónde se almacenan los logs?

- **Logs de Servidor**: `/tmp/server.log` (Linux/macOS) o `%TEMP%\server.log` (Windows)
- **Logs de Ejecución**: Directorio de trabajo del robot
- **Logs del Orquestador**: En el servidor del orquestador

### ¿Qué hago si pierdo los certificados?

1. **Si perdiste ca-key.pem**: Debes regenerar TODO el sistema de certificados y actualizar TODOS los robots y el orquestador
2. **Si perdiste solo cert.pem/key.pem de un robot**: Regenera solo ese certificado con `generate_robot_cert.sh`

### ¿Puedo ejecutar Robot Runner sin interfaz gráfica?

**Sí**, usa el modo server-only:

```bash
python app.py --server-only
```

Esto ejecuta solo el servidor sin abrir la ventana de webview. Útil para:
- Servidores sin interfaz gráfica
- Ejecución como servicio del sistema
- Entornos headless

### ¿Cómo configuro Robot Runner como servicio?

**Linux (systemd)**:

1. Crear archivo de servicio `/etc/systemd/system/robotrunner.service`:
   ```ini
   [Unit]
   Description=Robot Runner Service
   After=network.target

   [Service]
   Type=simple
   User=robotuser
   WorkingDirectory=/opt/robotrunner
   ExecStart=/usr/bin/python3 /opt/robotrunner/app.py --server-only
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

2. Activar servicio:
   ```bash
   sudo systemctl enable robotrunner
   sudo systemctl start robotrunner
   ```

**Windows (Task Scheduler)**:

1. Abrir Task Scheduler
2. Crear Tarea Básica
3. Trigger: Al iniciar sistema
4. Acción: Iniciar programa → `C:\RobotRunner\RobotRunner.exe --server-only`
5. Configurar para ejecutar con privilegios elevados

### ¿Cómo veo el estado del robot en tiempo real?

Puedes monitorear el endpoint `/status`:

```bash
# Desde terminal
watch -n 1 'curl -k "https://127.0.0.1:5055/status?machine_id=<ID>&license_key=<KEY>"'

# O con Python
import requests
import time

while True:
    response = requests.get(
        'https://127.0.0.1:5055/status',
        params={'machine_id': '<ID>', 'license_key': '<KEY>'},
        verify='ca-cert.pem'
    )
    print(f"Estado: {response.json()}")
    time.sleep(5)
```

### ¿El robot puede ejecutar cualquier tipo de script?

El robot ejecuta scripts Python localizados en el directorio `Robots/`. El script principal debe ser `robot.py` y puede importar otros módulos. Asegúrate de que:
- Todas las dependencias estén instaladas
- Los permisos de ejecución sean correctos
- Los paths relativos sean correctos

### ¿Qué pasa si se interrumpe la conexión durante la ejecución?

- El robot **continúa ejecutando** la tarea actual
- La pérdida de conexión no detiene la ejecución
- Cuando la conexión se restablece, el orquestador puede consultar el estado
- Si necesitas detener una ejecución durante una interrupción, debes hacerlo manualmente en la máquina

### ¿Cómo reporto un bug o solicito una función?

1. Revisa primero esta documentación y la sección de resolución de problemas
2. Verifica los logs para obtener mensajes de error específicos
3. Contacta al equipo de desarrollo con:
   - Descripción del problema
   - Pasos para reproducir
   - Logs relevantes
   - Versión de Robot Runner
   - Sistema operativo y versión

---

## Apéndices

### A. Estructura de Archivos

```
robotrunner_windows/
├── app.py                      # Aplicación principal
├── server.py                   # Lógica del servidor
├── config.py                   # Gestión de configuración
├── robot.py                    # Wrapper de ejecución
├── config.json                 # Configuración del robot
├── cert.pem                    # Certificado SSL del robot
├── key.pem                     # Clave privada SSL
├── ca-cert.pem                 # Certificado CA (compartido)
├── ca-key.pem                  # Clave privada CA (confidencial)
├── requirements.txt            # Dependencias Python
├── app.spec                    # Configuración PyInstaller
├── create_ca.sh               # Script creación CA
├── generate_robot_cert.sh     # Script generación certificados
├── verify_certs.sh            # Script verificación
├── templates/                  # Plantillas HTML
│   ├── form.html              # Formulario de configuración
│   └── connected.html         # Pantalla principal
├── static/                     # Archivos estáticos (CSS, JS, imágenes)
├── Robots/                     # Directorio de scripts de robots
├── certs/                      # Certificados generados por robot
└── docs/                       # Documentación
    ├── TECHNICAL-DOCUMENTATION.md
    └── FUNCTIONAL-DOCUMENTATION.md
```

### B. Formato de config.json

```json
{
    "url": "http://127.0.0.1:8088/",
    "token": "b82ababd99cb8c0fba61d8325ee4138c08b13745",
    "machine_id": "38PPU1Z6ZE5C",
    "license_key": "8ET9TIRBDADZ1QIFBNOTVQW5JYBTI4P0ER4N",
    "ip": "192.168.1.100",
    "port": "5055"
}
```

### C. Ejemplo de Integración con Orquestador

Ver archivo `orchestrator-example.py` en el directorio raíz para ejemplos completos de:
- Consultar estado del robot
- Enviar tareas de ejecución
- Pausar/reanudar/detener ejecuciones
- Manejo de errores y reintentos

### D. Endpoints API Disponibles

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/status` | GET | Consultar estado del robot |
| `/execution` | GET | Estado de ejecución actual |
| `/run` | POST | Iniciar ejecución de robot |
| `/stop` | GET | Detener ejecución actual |
| `/pause` | GET | Pausar ejecución |
| `/resume` | GET | Reanudar ejecución pausada |
| `/block` | GET | Bloquear robot |

Consulta `docs/TECHNICAL-DOCUMENTATION.md` para detalles completos de la API.

---

## Soporte

Para asistencia adicional:
- Consulta la documentación técnica en `docs/TECHNICAL-DOCUMENTATION.md`
- Revisa los scripts de ejemplo en `orchestrator-example.py`
- Consulta la guía de SSL en `CA-README.md` y `QUICK-START-SSL.md`

---

**Última Actualización**: 2025-11-17
**Versión del Documento**: 1.0