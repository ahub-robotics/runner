# Testing Guide - Robot Runner v2.0

Guía completa de testing para Robot Runner.

---

## Overview

Robot Runner cuenta con una suite completa de **171 tests**:
- **Unit Tests**: 43 tests (fast, isolated)
- **Integration Tests**: 15+ tests (slower, end-to-end)
- **Manual Tests**: 4+ scripts de debugging

**Coverage Goal**: >70% (actualmente ~75%)

---

## Ejecutar Tests

### Todos los Tests

```bash
pytest
```

### Por Categoría

```bash
# Solo unit tests
pytest tests/unit/ -m unit

# Solo integration tests
pytest tests/integration/ -m integration

# Tests lentos (>1 segundo)
pytest -m slow

# Tests rápidos (smoke tests)
pytest -m smoke
```

### Por Módulo

```bash
# Tests de API authentication
pytest tests/unit/test_api_auth.py -v

# Tests de executors
pytest tests/unit/test_executors.py -v

# Tests de REST endpoints
pytest tests/integration/test_rest_endpoints.py -v
```

### Con Coverage

```bash
# Generar reporte HTML
pytest --cov=. --cov-report=html

# Ver en browser
open htmlcov/index.html

# Reporte en terminal
pytest --cov=. --cov-report=term-missing
```

---

## Estructura de Tests

```
tests/
├── conftest.py              # Fixtures compartidas
├── pytest.ini               # Configuración pytest (en raíz)
├── unit/                    # Unit tests (43 tests)
│   ├── test_config.py       # Tests de configuración
│   ├── test_redis.py        # Tests de Redis state
│   ├── test_celery.py       # Tests de Celery tasks
│   ├── test_executors.py    # Tests de runner/server
│   ├── test_streaming.py    # Tests de streaming
│   ├── test_api_auth.py     # Tests de decoradores auth
│   ├── test_api_middleware.py  # Tests de middleware
│   └── test_utils_process.py   # Tests de process utils
├── integration/             # Integration tests (15+ tests)
│   └── test_rest_endpoints.py  # Tests de endpoints REST
└── manual/                  # Tests manuales (no pytest)
    ├── README.md
    └── test_*.py
```

---

## Fixtures Compartidas

Definidas en `tests/conftest.py`:

### test_config

```python
@pytest.fixture
def test_config():
    """Test configuration data."""
    return {
        'machine_id': 'TEST_MACHINE_ID',
        'license_key': 'TEST_LICENSE_KEY',
        'token': 'test_token_123',
        'port': 5001
    }
```

### app

```python
@pytest.fixture
def app():
    """Flask app for testing."""
    from api.app import create_app
    app = create_app({'TESTING': True})
    return app
```

### client

```python
@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()
```

### mock_server

```python
@pytest.fixture
def mock_server():
    """Mock server instance."""
    server = MagicMock()
    server.token = 'test_token_123'
    server.machine_id = 'test_machine'
    return server
```

---

## Markers

Configurados en `pytest.ini`:

```ini
[pytest]
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (slower, may require services)
    slow: Slow tests (>1 second)
    smoke: Quick validation tests
    api: API endpoint tests
    streaming: Streaming functionality tests
    executors: Robot execution tests
```

**Uso**:

```python
@pytest.mark.unit
@pytest.mark.api
def test_require_token_valid(app, client, mock_server):
    """Test @require_token with valid token."""
    # ...
```

---

## Escribir Tests

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
        expected_result = "success"

        # Act
        result = some_function()

        # Assert
        assert result == expected_result

    def test_method_failure(self):
        """Test method with failure case."""
        with pytest.raises(ValueError):
            some_function(invalid_input)
```

### Integration Test Template

```python
"""
Integration tests for feature_name.

Tests complete request/response cycles.
"""
import pytest
from unittest.mock import patch


class TestFeature:
    """Integration tests for feature."""

    def test_complete_flow(self, client):
        """Test complete feature flow."""
        # Start
        response = client.post('/start', json={'param': 'value'})
        assert response.status_code == 200

        # Check status
        response = client.get('/status')
        assert response.status_code == 200
        assert response.json['status'] == 'active'

        # Stop
        response = client.post('/stop')
        assert response.status_code == 200
```

---

## Testing Best Practices

### 1. Arrange-Act-Assert Pattern

```python
def test_function():
    # Arrange: Setup test data
    input_data = {'key': 'value'}

    # Act: Execute function under test
    result = function_under_test(input_data)

    # Assert: Verify expectations
    assert result == expected_value
```

### 2. Mock External Dependencies

```python
@patch('api.rest.execution.run_robot_task.delay')
def test_post_run_valid(mock_task, client):
    """Test POST /run with mocked Celery task."""
    mock_task.return_value = MagicMock(id='task-123')

    response = client.post('/run', json={...})

    assert response.status_code == 200
    mock_task.assert_called_once()
```

### 3. Test Both Success and Failure Cases

```python
def test_auth_success(client):
    """Test authentication with valid token."""
    response = client.get('/endpoint',
        headers={'Authorization': 'Bearer valid-token'})
    assert response.status_code == 200

def test_auth_failure(client):
    """Test authentication with invalid token."""
    response = client.get('/endpoint',
        headers={'Authorization': 'Bearer invalid-token'})
    assert response.status_code == 403
```

### 4. Use Descriptive Test Names

```python
# Good
def test_require_token_returns_401_when_token_missing():
    pass

# Bad
def test_token():
    pass
```

### 5. One Assertion Per Test (Guideline)

```python
# Good
def test_response_status_code():
    assert response.status_code == 200

def test_response_contains_execution_id():
    assert 'execution_id' in response.json

# Acceptable (related assertions)
def test_response_structure():
    assert response.status_code == 200
    assert 'execution_id' in response.json
    assert response.json['status'] == 'running'
```

---

## Testing Specific Components

### Testing API Endpoints

```python
def test_endpoint_requires_authentication(client):
    """Test endpoint rejects unauthenticated requests."""
    response = client.get('/protected-endpoint')
    assert response.status_code == 401

def test_endpoint_validates_input(client, auth_headers):
    """Test endpoint validates JSON input."""
    response = client.post('/endpoint',
        json={'invalid': 'data'},
        headers=auth_headers)
    assert response.status_code == 400
```

### Testing Celery Tasks

```python
@patch('executors.tasks.Runner')
def test_run_robot_task(mock_runner):
    """Test run_robot_task Celery task."""
    mock_runner_instance = MagicMock()
    mock_runner.return_value = mock_runner_instance

    from executors.tasks import run_robot_task
    result = run_robot_task('test.robot', {}, 'exec-123')

    mock_runner.assert_called_once_with('test.robot', {})
    mock_runner_instance.run.assert_called_once()
```

### Testing Redis State

```python
@patch('shared.state.redis_state.redis_client')
def test_save_execution_state(mock_redis):
    """Test saving execution state to Redis."""
    from shared.state.redis_state import save_execution_state

    execution_data = {
        'execution_id': 'exec-123',
        'status': 'running'
    }

    save_execution_state(execution_data)

    mock_redis.hset.assert_called_once_with(
        'execution:exec-123',
        mapping=execution_data
    )
```

### Testing Authentication Decorators

```python
def test_require_token_decorator(app):
    """Test @require_token decorator."""
    from api.auth import require_token

    @app.route('/test')
    @require_token
    def test_endpoint():
        return {'status': 'ok'}

    with app.test_client() as client:
        # Without token
        response = client.get('/test')
        assert response.status_code == 401

        # With valid token
        response = client.get('/test',
            headers={'Authorization': 'Bearer test_token_123'})
        assert response.status_code == 200
```

---

## Continuous Integration

### GitHub Actions Workflow

`.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      redis:
        image: redis:5
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install -r requirements-dev.txt

    - name: Run tests with coverage
      run: |
        pytest --cov=. --cov-report=xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
```

---

## Debugging Tests

### Show Print Statements

```bash
pytest -s
```

### Verbose Output

```bash
pytest -vv
```

### Stop on First Failure

```bash
pytest -x
```

### Run Last Failed Tests

```bash
pytest --lf
```

### Full Traceback

```bash
pytest --tb=long
```

### PDB Debugger

```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger at start of test
pytest --trace
```

---

## Performance Testing

### Measure Test Duration

```bash
pytest --durations=10  # Show 10 slowest tests
```

### Parallel Execution

```bash
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest -n 4
```

---

## Coverage Goals

| Module | Current | Goal |
|--------|---------|------|
| **Overall** | 75% | >70% ✓ |
| **api/** | 82% | >80% ✓ |
| **executors/** | 78% | >80% ✗ |
| **streaming/** | 71% | >70% ✓ |
| **shared/** | 68% | >60% ✓ |

---

## Manual Tests

Ubicados en `tests/manual/`:

```bash
# Test screen capture
python tests/manual/test_screen_capture.py

# Test streaming complete flow
python tests/manual/test_streaming_complete.py
```

**Nota**: Estos NO se ejecutan con pytest, son scripts standalone para debugging.

---

## Próximos Pasos

- Leer [Contributing Guide](contributing.md) para contribuir
- Revisar [Setup Guide](setup.md) para configurar entorno
- Consultar [Architecture Docs](../architecture/overview.md)

---

**Actualizado**: 2026-01-08
**Versión**: 2.0.0
