# Scripts de Gestión - Robot Runner

Este directorio contiene scripts útiles para gestionar el servidor Robot Runner.

## Scripts de Gestión de Gunicorn

### 🔍 Verificar Estado (`check_gunicorn`)

Verifica si hay procesos de Gunicorn corriendo.

```bash
# Bash (Linux/macOS)
./scripts/check_gunicorn.sh

# Python (Multiplataforma)
python scripts/check_gunicorn.py
```

**Salida:**
- Lista de procesos con PIDs, CPU, memoria
- Puertos en uso
- Sugerencias de comandos

### ⛔ Detener Servidor (`kill_gunicorn`)

Detiene todos los procesos de Gunicorn de forma ordenada.

```bash
# Bash (Linux/macOS)
./scripts/kill_gunicorn.sh

# Python (Multiplataforma)
python scripts/kill_gunicorn.py
```

**Comportamiento:**
1. Intenta terminación grácil (SIGTERM)
2. Espera 3 segundos
3. Fuerza terminación si es necesario (SIGKILL)

### 🚀 Iniciar Servidor (`start_server`)

Inicia el servidor con verificación automática de procesos existentes.

```bash
# Modo normal (GUI + Servidor)
./scripts/start_server.sh

# Solo servidor (sin GUI)
./scripts/start_server.sh --server-only

# Forzar inicio matando procesos existentes
./scripts/start_server.sh --force
```

## Otros Scripts

### Túnel Cloudflare

- `setup_machine_tunnel.py` - Configura el túnel de Cloudflare
- `start_tunnel.sh` - Inicia el túnel
- `stop_tunnel.sh` - Detiene el túnel
- `tunnel_status.sh` - Verifica el estado del túnel

### Certificados SSL

- `create_ca.sh` - Crea una Autoridad Certificadora (CA)
- `generate_robot_cert.sh` - Genera certificados para robots
- `verify_certs.sh` - Verifica certificados SSL

### Testing

- `test_all_endpoints.py` - Prueba todos los endpoints de la API
- `test_authentication.py` - Prueba autenticación

## Permisos

Si los scripts no son ejecutables, dar permisos con:

```bash
chmod +x scripts/*.sh
chmod +x scripts/*.py
```

## Documentación Adicional

Para más información, consulta:
- [GUNICORN-MANAGEMENT.md](../docs/GUNICORN-MANAGEMENT.md) - Gestión detallada de Gunicorn
- [TECHNICAL-DOCUMENTATION.md](../docs/TECHNICAL-DOCUMENTATION.md) - Documentación técnica completa