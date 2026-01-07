# System Tray App - Robot Runner

## Descripción

Aplicación de bandeja del sistema (System Tray) para gestionar el servidor Robot Runner de forma visual y cómoda.

## Características

✨ **Gestión Visual del Servidor**
- Iniciar y detener el servidor desde el tray
- Ver estado en tiempo real
- Icono que cambia de color según el estado:
  - 🔴 Rojo: Servidor detenido
  - 🟢 Verde: Servidor corriendo
  - 🟡 Amarillo: Servidor iniciando

🎯 **Funciones Principales**
- **Estado**: Muestra información del servidor en consola
- **Iniciar Servidor**: Lanza el servidor en background
- **Detener Servidor**: Detiene todos los procesos de Gunicorn
- **Reiniciar Servidor**: Reinicia el servidor limpiamente
- **Abrir Interfaz Web**: Abre el navegador con la interfaz
- **Ver Logs**: Abre el archivo de logs del servidor
- **Salir**: Cierra la aplicación del tray

## Instalación

### Requisitos

```bash
pip install pystray pillow
# O desde requirements.txt
pip install -r requirements.txt
```

### Sistemas Operativos Soportados

- ✅ **macOS**: Completamente soportado
- ✅ **Linux**: Soportado (requiere libappindicator)
- ✅ **Windows**: Soportado

## Uso

### Iniciar la Aplicación

```bash
python tray_app.py
```

### Salida Esperada

```
==============================================================
  Robot Runner - System Tray App
==============================================================

📡 Puerto: 5055
🌐 URL: https://localhost:5055

Estado inicial: ⛔ Stopped

✨ Aplicación iniciada. Busca el icono en la bandeja del sistema.
   Haz clic derecho en el icono para ver las opciones.

Para salir: Haz clic en 'Salir' en el menú del tray
==============================================================
```

### Ubicación del Icono

- **macOS**: Barra de menú superior derecha
- **Windows**: Bandeja del sistema (esquina inferior derecha)
- **Linux**: Área de notificación del panel

## Menú de Opciones

### 1. Estado
Muestra información del servidor en la consola:
```
==============================================================
Estado del Servidor: ✅ Running (PIDs: 12345, 12346)
Puerto: 5055
URL: https://localhost:5055
==============================================================
```

### 2. Iniciar Servidor
- Inicia el servidor Robot Runner en background
- El icono cambia a amarillo durante el inicio
- Una vez iniciado, cambia a verde
- El servidor se ejecuta independientemente del tray

### 3. Detener Servidor
- Detiene todos los procesos de Gunicorn
- Intenta terminación grácil (SIGTERM) primero
- Si no responden, fuerza terminación (SIGKILL)
- El icono cambia a rojo

### 4. Reiniciar Servidor
- Detiene y vuelve a iniciar el servidor
- Útil después de cambios en la configuración
- Secuencia: Detener → Esperar 2s → Iniciar

### 5. Abrir Interfaz Web
- Abre el navegador con la URL del servidor
- Solo disponible cuando el servidor está corriendo
- URL por defecto: https://localhost:5055

### 6. Ver Logs
- Abre el archivo de logs del servidor
- Ruta: `~/Robot/requests.log`
- Se abre con el editor por defecto del sistema

### 7. Salir
- Cierra la aplicación del tray
- **IMPORTANTE**: El servidor continúa ejecutándose
- Para detener el servidor, usar "Detener Servidor" antes de salir

## Actualización Automática del Estado

La aplicación verifica el estado del servidor cada 5 segundos y actualiza el icono automáticamente. Esto permite detectar:
- Si el servidor se detuvo externamente
- Si se inició el servidor desde otro terminal
- Cambios en el estado del sistema

## Atajos de Teclado

No hay atajos de teclado específicos. Todas las acciones se realizan desde el menú del tray.

## Ejecución en Segundo Plano

### macOS/Linux

Para ejecutar la aplicación en background:

```bash
# Opción 1: Usando nohup
nohup python tray_app.py > /tmp/tray_app.log 2>&1 &

# Opción 2: Usando screen
screen -dmS tray_app python tray_app.py

# Opción 3: Usando systemd (Linux)
# Ver sección de systemd más abajo
```

### Windows

Para ejecutar en background:

```powershell
# Crear archivo .vbs para ejecución silenciosa
# Archivo: start_tray.vbs
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "python tray_app.py", 0, False

# Ejecutar
cscript start_tray.vbs
```

## Integración con systemd (Linux)

Crear archivo `/etc/systemd/system/robotrunner-tray.service`:

```ini
[Unit]
Description=Robot Runner System Tray
After=graphical.target

[Service]
Type=simple
User=robot
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/home/robot/.Xauthority"
WorkingDirectory=/home/robot/robotrunner_windows
ExecStart=/home/robot/robotrunner_windows/venv/bin/python tray_app.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=graphical.target
```

Comandos:

```bash
# Habilitar
sudo systemctl enable robotrunner-tray

# Iniciar
sudo systemctl start robotrunner-tray

# Ver estado
sudo systemctl status robotrunner-tray

# Ver logs
journalctl -u robotrunner-tray -f
```

## Inicio Automático en macOS

### Opción 1: Launch Agent

Crear archivo `~/Library/LaunchAgents/com.robotrunner.tray.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.robotrunner.tray</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/TU_USUARIO/robotrunner_windows/venv/bin/python</string>
        <string>/Users/TU_USUARIO/robotrunner_windows/tray_app.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/robotrunner-tray.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/robotrunner-tray.error.log</string>
</dict>
</plist>
```

Comandos:

```bash
# Cargar (iniciar)
launchctl load ~/Library/LaunchAgents/com.robotrunner.tray.plist

# Descargar (detener)
launchctl unload ~/Library/LaunchAgents/com.robotrunner.tray.plist
```

### Opción 2: Login Items (más simple)

1. Abrir **System Preferences** → **Users & Groups**
2. Seleccionar tu usuario
3. Ir a **Login Items**
4. Hacer clic en **+** y agregar `tray_app.py`

## Solución de Problemas

### El icono no aparece

**macOS:**
```bash
# Reiniciar Finder y la barra de menú
killall Finder
killall SystemUIServer
```

**Linux:**
```bash
# Verificar que libappindicator esté instalado
sudo apt-get install libappindicator3-1
# o
sudo dnf install libappindicator-gtk3
```

**Windows:**
- Verificar que la aplicación no esté bloqueada por el firewall

### El servidor no inicia

1. Verificar logs en consola donde se ejecutó `tray_app.py`
2. Verificar que no haya procesos de Gunicorn corriendo:
   ```bash
   python scripts/check_gunicorn.py
   ```
3. Intentar iniciar el servidor manualmente:
   ```bash
   python run.py --server-only
   ```

### "Error: pystray no está instalado"

```bash
pip install pystray pillow
```

### El icono no se actualiza

La actualización es cada 5 segundos. Si no se actualiza:
1. Cerrar y volver a abrir la aplicación
2. Verificar logs en consola

## Integración con Otros Comandos

La aplicación del tray es compatible con:

```bash
# Detener desde línea de comandos
python scripts/kill_gunicorn.py

# Verificar estado
python scripts/check_gunicorn.py

# Iniciar manualmente
python run.py --server-only
```

El tray detectará estos cambios automáticamente.

## Seguridad

- La aplicación NO requiere permisos de administrador
- Los logs se guardan en el directorio del usuario
- No se exponen credenciales en el menú del tray
- Las operaciones sensibles requieren acceso al archivo de configuración

## Limitaciones

1. **Un solo servidor**: La aplicación asume un solo servidor corriendo
2. **Puerto fijo**: El puerto se lee del config.json al iniciar
3. **Sin múltiples instancias**: No se recomienda ejecutar múltiples instancias del tray
4. **Dependencia de entorno gráfico**: Requiere sesión de usuario con GUI

## Ver también

- [GUNICORN-MANAGEMENT.md](GUNICORN-MANAGEMENT.md) - Gestión de procesos Gunicorn
- [TECHNICAL-DOCUMENTATION.md](TECHNICAL-DOCUMENTATION.md) - Documentación técnica
- [FUNCTIONAL-DOCUMENTATION.md](FUNCTIONAL-DOCUMENTATION.md) - Documentación funcional

## Soporte

Si tienes problemas con la aplicación del tray:

1. Revisa los logs en consola
2. Verifica que pystray esté instalado correctamente
3. Prueba iniciar/detener el servidor manualmente
4. Consulta la sección de solución de problemas