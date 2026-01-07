# 🚀 Inicio Rápido - System Tray App

## Instalación

```bash
# Instalar dependencias
pip install -r requirements.txt
```

## Uso

### Iniciar la aplicación

```bash
# Opción 1: Directamente
python tray_app.py

# Opción 2: Script de ayuda
./start_tray.sh
```

### Buscar el icono

- **macOS**: Barra de menú superior derecha
- **Windows**: Bandeja del sistema (esquina inferior derecha)
- **Linux**: Área de notificación del panel

### Usar el menú

Haz **clic derecho** en el icono para ver las opciones:

- ✅ **Estado**: Ver información del servidor
- 🚀 **Iniciar Servidor**: Lanzar el servidor
- ⛔ **Detener Servidor**: Detener el servidor
- 🔄 **Reiniciar Servidor**: Reiniciar el servidor
- 🌐 **Abrir Interfaz Web**: Abrir en navegador
- 📋 **Ver Logs**: Ver archivo de logs
- 👋 **Salir**: Cerrar la aplicación

### Iconos de Estado

- 🔴 **Rojo**: Servidor detenido
- 🟢 **Verde**: Servidor corriendo
- 🟡 **Amarillo**: Servidor iniciando

## Comandos Útiles

```bash
# Verificar si está corriendo
ps aux | grep tray_app

# Detener la aplicación
pkill -f tray_app.py

# Ver logs del servidor
tail -f ~/Robot/requests.log
```

## Documentación Completa

Para más información, consulta:
- [docs/SYSTEM-TRAY-APP.md](docs/SYSTEM-TRAY-APP.md) - Documentación completa
- [docs/GUNICORN-MANAGEMENT.md](docs/GUNICORN-MANAGEMENT.md) - Gestión de Gunicorn

## Problemas Comunes

### El icono no aparece

```bash
# macOS: Reiniciar barra de menú
killall SystemUIServer
```

### "Error: pystray no está instalado"

```bash
pip install pystray pillow
```

### El servidor no inicia

```bash
# Verificar procesos existentes
python scripts/check_gunicorn.py

# Detener procesos
python scripts/kill_gunicorn.py

# Reintentar
python tray_app.py
```