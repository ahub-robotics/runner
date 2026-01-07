# Gestión de Procesos Gunicorn

## Descripción

Este documento describe cómo gestionar los procesos de Gunicorn del servidor Robot Runner de forma cómoda y segura.

## Scripts Disponibles

### 1. Verificar Estado del Servidor

Verifica si hay procesos de Gunicorn corriendo y muestra información detallada.

**Bash (Linux/macOS):**
```bash
./scripts/check_gunicorn.sh
```

**Python (Multiplataforma):**
```bash
python scripts/check_gunicorn.py
```

**Salida esperada:**
- ✅ No hay procesos corriendo (exit code 0)
- 📋 Lista de procesos con PIDs, CPU, memoria y puertos (exit code 1)

### 2. Detener Servidor

Detiene todos los procesos de Gunicorn de forma ordenada:
1. Intenta terminación grácil (SIGTERM)
2. Espera 3 segundos
3. Si quedan procesos, fuerza terminación (SIGKILL)

**Bash (Linux/macOS):**
```bash
./scripts/kill_gunicorn.sh
```

**Python (Multiplataforma):**
```bash
python scripts/kill_gunicorn.py
```

### 3. Iniciar Servidor con Verificación

Inicia el servidor verificando primero si hay procesos corriendo.

**Bash (Linux/macOS):**
```bash
# Modo normal (GUI + Servidor)
./scripts/start_server.sh

# Solo servidor (sin GUI)
./scripts/start_server.sh --server-only

# Forzar inicio matando procesos existentes
./scripts/start_server.sh --force
```

## Flujo de Trabajo Recomendado

### Inicio Normal
```bash
# 1. Verificar si hay procesos corriendo
./scripts/check_gunicorn.sh

# 2. Si hay procesos y quieres detenerlos
./scripts/kill_gunicorn.sh

# 3. Iniciar servidor
python run.py
# O con verificación automática:
./scripts/start_server.sh
```

### Inicio Rápido (Forzado)
```bash
# Mata procesos existentes e inicia automáticamente
./scripts/start_server.sh --force
```

### Solo Detener
```bash
# Detener todos los procesos de Gunicorn
./scripts/kill_gunicorn.sh
```

## Comandos Manuales

### Linux/macOS

**Buscar procesos:**
```bash
ps aux | grep gunicorn | grep -v grep
```

**Detener grácilmente:**
```bash
pkill -TERM gunicorn
```

**Forzar detención:**
```bash
pkill -9 gunicorn
```

**Ver puertos en uso:**
```bash
lsof -p <PID> | grep LISTEN
```

### Windows

**Buscar procesos:**
```powershell
tasklist | findstr python
```

**Detener proceso:**
```powershell
taskkill /PID <PID>
```

**Forzar detención:**
```powershell
taskkill /F /PID <PID>
```

**Ver puertos en uso:**
```powershell
netstat -ano | findstr <PID>
```

## Problemas Comunes

### El servidor no inicia - Puerto en uso

**Síntoma:**
```
Error: Address already in use
```

**Solución:**
```bash
# 1. Verificar qué proceso está usando el puerto
lsof -i :5055  # Cambiar 5055 por tu puerto

# 2. Detener procesos de Gunicorn
./scripts/kill_gunicorn.sh

# 3. Reintentar
python run.py
```

### Procesos zombies que no se detienen

**Síntoma:**
Los procesos aparecen en `ps` pero no responden a señales.

**Solución:**
```bash
# Forzar terminación con SIGKILL
./scripts/kill_gunicorn.sh

# O manualmente
kill -9 <PID>

# Si persiste, reiniciar sistema
```

### Múltiples instancias corriendo

**Síntoma:**
```
🔍 Procesos de Gunicorn encontrados: 8
```

**Solución:**
```bash
# Detener todos
./scripts/kill_gunicorn.sh

# Verificar que se detuvieron
./scripts/check_gunicorn.sh

# Iniciar una sola instancia
python run.py
```

## Integración con systemd (Linux)

Para gestionar el servidor como servicio de sistema:

**Crear archivo `/etc/systemd/system/robotrunner.service`:**
```ini
[Unit]
Description=Robot Runner Server
After=network.target

[Service]
Type=forking
User=robot
WorkingDirectory=/home/robot/robotrunner_windows
Environment="PATH=/home/robot/robotrunner_windows/venv/bin"
ExecStartPre=/home/robot/robotrunner_windows/scripts/kill_gunicorn.sh
ExecStart=/home/robot/robotrunner_windows/venv/bin/python run.py --server-only
ExecStop=/home/robot/robotrunner_windows/scripts/kill_gunicorn.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Comandos:**
```bash
# Habilitar servicio
sudo systemctl enable robotrunner

# Iniciar servicio
sudo systemctl start robotrunner

# Ver estado
sudo systemctl status robotrunner

# Detener servicio
sudo systemctl stop robotrunner

# Ver logs
journalctl -u robotrunner -f
```

## Buenas Prácticas

1. **Siempre verifica antes de iniciar:**
   ```bash
   ./scripts/check_gunicorn.sh && python run.py
   ```

2. **Usa el script de inicio con verificación:**
   ```bash
   ./scripts/start_server.sh
   ```

3. **En producción, usa systemd o supervisor** en lugar de ejecutar manualmente.

4. **Monitorea los procesos regularmente:**
   ```bash
   watch -n 5 './scripts/check_gunicorn.sh'
   ```

5. **Configura logs apropiados** para poder diagnosticar problemas:
   ```python
   # En config.json o variables de entorno
   {
     "log_level": "INFO",
     "log_file": "/var/log/robotrunner/server.log"
   }
   ```

## Ver también

- [TECHNICAL-DOCUMENTATION.md](TECHNICAL-DOCUMENTATION.md) - Documentación técnica completa
- [QUICK-START-TUNNEL.md](QUICK-START-TUNNEL.md) - Configuración de túnel Cloudflare
- [FUNCTIONAL-DOCUMENTATION.md](FUNCTIONAL-DOCUMENTATION.md) - Documentación funcional

## Soporte

Si tienes problemas con la gestión de procesos:

1. Revisa los logs del servidor
2. Verifica los puertos en uso
3. Asegúrate de tener permisos suficientes
4. Consulta la sección de problemas comunes arriba