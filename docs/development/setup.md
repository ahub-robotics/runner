# Development Setup - Robot Runner v2.0

Guía para configurar el entorno de desarrollo.

---

## Requisitos Previos

### Software Requerido

- **Python 3.9+**
- **Redis 5.0+**
- **Git**
- **OpenSSL** (para certificados SSL)
- **RobotFramework** (instalado via pip)

### Sistemas Operativos Soportados

- macOS 10.15+
- Ubuntu 20.04+
- Windows 10+ (con algunas limitaciones)

---

## Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/your-org/robotrunner.git
cd robotrunner
```

### 2. Crear Entorno Virtual

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
```

### 3. Instalar Dependencias

```bash
# Producción
pip install -r requirements.txt

# Desarrollo (incluye testing)
pip install -r requirements-dev.txt
```

**requirements.txt**:
```
Flask==2.3.3
gunicorn==21.2.0
celery==5.3.4
redis==5.0.0
robotframework==6.1.1
mss==9.0.1
Pillow==10.0.0
requests==2.31.0
PyYAML==6.0.1
pystray==0.19.5
```

**requirements-dev.txt**:
```
-r requirements.txt
pytest==7.4.3
pytest-flask==1.3.0
pytest-cov==4.1.0
pytest-mock==3.12.0
black==23.11.0
flake8==6.1.0
mypy==1.7.1
```

### 4. Configurar Redis

```bash
# macOS (Homebrew)
brew install redis
brew services start redis

# Ubuntu
sudo apt-get install redis-server
sudo systemctl start redis

# Verificar
redis-cli ping  # debe responder "PONG"
```

### 5. Configurar Certificados SSL

```bash
# Generar CA y certificados
cd ssl
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout ca-key.pem -out ca-cert.pem \
  -days 365 -subj "/CN=RobotRunner CA"

openssl req -newkey rsa:4096 -nodes \
  -keyout key.pem -out cert.csr \
  -subj "/CN=localhost"

openssl x509 -req -in cert.csr -CA ca-cert.pem \
  -CAkey ca-key.pem -CAcreateserial \
  -out cert.pem -days 365

cd ..
```

### 6. Configurar config.json

```bash
cp config.json.example config.json
```

Editar `config.json`:
```json
{
  "machine_id": "DEV-MACHINE",
  "license_key": "dev-license-key",
  "token": "dev-token-123",
  "port": 5001,
  "ssl_enabled": true,
  "notify_url": ""
}
```

---

## Estructura del Proyecto

```
robotrunner/
├── api/              # Flask app y blueprints
├── executors/        # Robot execution
├── streaming/        # Video streaming
├── shared/           # Código común
├── cli/              # Entry points CLI
├── gui/              # System tray app
├── tests/            # Tests
├── templates/        # HTML templates
├── static/           # CSS, JS, images
├── ssl/              # Certificados
├── logs/             # Logs (generados)
├── run.py            # Main entry point
├── gunicorn_config.py
└── config.json
```

---

## Ejecutar en Modo Desarrollo

### Opción 1: Servidor Flask (Development)

```bash
# Modo debug (auto-reload)
python run.py

# Acceder a:
# https://localhost:5001
```

### Opción 2: Gunicorn (Production-like)

```bash
python cli/run_server.py

# O directamente:
gunicorn -c gunicorn_config.py api.wsgi:app
```

### Opción 3: System Tray App

```bash
python run.py --tray

# O directamente:
python cli/run_tray.py
```

---

## Ejecutar Tests

```bash
# Todos los tests
pytest

# Unit tests solamente
pytest tests/unit/ -m unit

# Integration tests
pytest tests/integration/ -m integration

# Con coverage
pytest --cov=. --cov-report=html
# Ver reporte en: htmlcov/index.html

# Tests específicos
pytest tests/unit/test_api_auth.py -v

# Con verbose y print output
pytest -vv -s
```

---

## Code Quality Tools

### Black (Code Formatter)

```bash
# Format all code
black .

# Check without modifying
black --check .
```

### Flake8 (Linter)

```bash
# Lint all code
flake8 .

# Specific directories
flake8 api/ executors/ streaming/
```

### MyPy (Type Checker)

```bash
# Type check all code
mypy .

# Specific module
mypy api/
```

---

## Debugging

### VS Code Launch Configuration

`.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Flask",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/run.py",
      "console": "integratedTerminal",
      "justMyCode": false
    },
    {
      "name": "Python: Pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["-vv", "-s"],
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
```

### PyCharm Run Configuration

1. **Run/Debug Configurations**
2. **Add New Configuration** → Python
3. **Script path**: `run.py`
4. **Working directory**: `$ProjectFileDir$`

---

## Git Workflow

### Branch Strategy

- `master`: Código estable en producción
- `develop`: Desarrollo activo
- `feature/*`: Nuevas features
- `bugfix/*`: Bug fixes
- `hotfix/*`: Hotfixes urgentes

### Crear una Feature Branch

```bash
git checkout develop
git pull origin develop
git checkout -b feature/my-new-feature
```

### Commit Guidelines

Usamos Conventional Commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: Nueva feature
- `fix`: Bug fix
- `docs`: Cambios en documentación
- `style`: Formateo de código
- `refactor`: Refactoring
- `test`: Tests
- `chore`: Tareas de mantenimiento

**Example**:
```
feat(api): Add pause/resume endpoints for robot execution

Implemented /pause and /resume endpoints that use SIGSTOP/SIGCONT
signals to pause and resume robot processes.

Closes #123
```

---

## Common Development Tasks

### Agregar un Nuevo Endpoint

1. Crear/editar blueprint en `api/rest/` o `api/web/`
2. Implementar función del endpoint con decorador de auth
3. Actualizar `api/app.py` si es un nuevo blueprint
4. Escribir tests en `tests/unit/` o `tests/integration/`
5. Documentar en `docs/api/rest-api.md`

### Agregar una Nueva Feature a Executors

1. Implementar en `executors/runner.py` o `executors/server.py`
2. Si es async, agregar task en `executors/tasks.py`
3. Actualizar estado en Redis via `shared/state/redis_state.py`
4. Escribir tests unitarios en `tests/unit/test_executors.py`
5. Documentar en `docs/architecture/components.md`

### Modificar Configuración

1. Actualizar `config.json` (ejemplo en `config.json.example`)
2. Modificar `shared/config/loader.py` si cambias estructura
3. Validar en `shared/config/loader.py::validate_config()`
4. Documentar cambios en `docs/deployment/installation.md`

---

## Troubleshooting

### Redis Connection Errors

```bash
# Verificar que Redis está corriendo
redis-cli ping

# Ver logs de Redis
# macOS
tail -f /usr/local/var/log/redis.log

# Ubuntu
sudo journalctl -u redis -f
```

### SSL Certificate Errors

```bash
# Regenerar certificados
cd ssl
./generate_certs.sh  # Si tienes el script

# O manual (ver sección Configurar Certificados SSL)
```

### Import Errors

```bash
# Asegúrate de que el venv está activado
which python  # Debe apuntar a venv/bin/python

# Reinstalar dependencias
pip install -r requirements-dev.txt
```

### Celery Worker Not Starting

```bash
# Verificar que Redis está corriendo
redis-cli ping

# Ver logs de Celery
# En gunicorn_config.py están configurados los hooks
# Revisar logs/server.log
```

---

## Recursos Adicionales

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [pytest Documentation](https://docs.pytest.org/)
- [RobotFramework Documentation](https://robotframework.org/robotframework/)

---

## Próximos Pasos

- Leer [Testing Guide](testing.md) para escribir tests
- Revisar [Contributing Guide](contributing.md) para contribuir
- Consultar [Architecture Docs](../architecture/overview.md)

---

**Actualizado**: 2026-01-08
**Versión**: 2.0.0
