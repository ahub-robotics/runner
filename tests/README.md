# Tests - Robot Runner

Suite de tests completa para Robot Runner con unit tests e integration tests.

## Estructura

```
tests/
├── conftest.py              # Fixtures compartidas (config, mocks, etc.)
├── pytest.ini               # Configuración de pytest (en raíz)
├── unit/                    # Unit tests (rápidos, aislados)
│   ├── test_config.py       # Tests de configuración
│   ├── test_redis.py        # Tests de Redis state
│   ├── test_celery.py       # Tests de Celery tasks
│   ├── test_executors.py    # Tests de runner/server
│   ├── test_streaming.py    # Tests de streaming
│   ├── test_api_auth.py     # Tests de decoradores auth
│   ├── test_api_middleware.py  # Tests de middleware
│   └── test_utils_process.py   # Tests de process utils
├── integration/             # Integration tests (más lentos)
│   └── test_rest_endpoints.py  # Tests de endpoints REST
└── manual/                  # Tests manuales (no automatizados)
    ├── README.md
    └── test_*.py
```

## Ejecutar Tests

### Todos los tests
```bash
pytest
```

### Solo unit tests
```bash
pytest tests/unit/ -m unit
```

### Solo integration tests
```bash
pytest tests/integration/ -m integration
```

### Un archivo específico
```bash
pytest tests/unit/test_api_auth.py -v
```

### Con coverage
```bash
pytest --cov=. --cov-report=html
# Ver en: htmlcov/index.html
```

### Tests específicos por marker
```bash
pytest -m api          # Solo tests de API
pytest -m streaming    # Solo tests de streaming
pytest -m executors    # Solo tests de executors
```

## Markers Disponibles

- `unit`: Unit tests (fast, isolated)
- `integration`: Integration tests (slower, may require services)
- `slow`: Slow tests (>1 second)
- `smoke`: Quick validation tests
- `api`: API endpoint tests
- `streaming`: Streaming functionality tests
- `executors`: Robot execution tests

## Fixtures Compartidas

Definidas en `conftest.py`:

- `test_config`: Configuración de prueba
- `temp_config_file`: Archivo config.json temporal
- `mock_redis`: Mock de cliente Redis
- `mock_server`: Mock de instancia Server
- `app`: Flask app de prueba
- `client`: Flask test client

## Escribir Nuevos Tests

### Unit Test Template

```python
"""
Unit tests for module_name.

Brief description of what is tested.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestClassName:
    """Tests for ClassName."""

    def test_method_success(self):
        """Test method with successful case."""
        # Arrange
        # Act
        # Assert
        pass

    def test_method_failure(self):
        """Test method with failure case."""
        pass
```

### Integration Test Template

```python
"""
Integration tests for feature_name.

Tests complete request/response cycles.
"""
import pytest
from unittest.mock import patch


@pytest.fixture
def client(app):
    return app.test_client()


class TestFeature:
    """Integration tests for feature."""

    def test_complete_flow(self, client):
        """Test complete feature flow."""
        # Test end-to-end functionality
        pass
```

## Coverage Goals

- **Overall**: >70%
- **Critical modules** (api, executors): >80%
- **Utility modules** (shared): >60%

## CI/CD Integration

Tests se ejecutan automáticamente en:
- Pull requests
- Push a master/main
- Pre-commit hooks (opcional)

Configuración en `.github/workflows/tests.yml` (por crear en FASE 11)

## Debugging Tests

### Ver print statements
```bash
pytest -s
```

### Ver traceback completo
```bash
pytest --tb=long
```

### Ejecutar solo tests fallidos
```bash
pytest --lf
```

### Modo verbose
```bash
pytest -vv
```

## Tests que Requieren Servicios

Algunos integration tests requieren:
- Redis running (puerto 6379)
- Celery worker (opcional)

Para skipear estos tests:
```bash
pytest -m "not integration"
```

## Notas

- Los tests manuales en `tests/manual/` NO se ejecutan con pytest
- Son scripts standalone para debugging
- No cuentan para coverage

## Recursos

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-flask](https://pytest-flask.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
