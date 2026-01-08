"""
Configuración compartida para pytest.

Este módulo contiene fixtures reutilizables para todos los tests.
"""
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# ============================================================================
# FIXTURES DE CONFIGURACIÓN
# ============================================================================

@pytest.fixture
def test_config():
    """Configuración de prueba."""
    return {
        'machine_id': 'TEST_MACHINE_ID',
        'license_key': 'TEST_LICENSE_KEY',
        'token': 'test_token_123',
        'url': 'https://test.example.com',
        'ip': '127.0.0.1',
        'port': 5001,
        'folder': '/tmp/test_robots',
        'tunnel_subdomain': 'test-robot',
        'tunnel_id': 'test-tunnel-id-123',
    }


@pytest.fixture
def temp_config_file(test_config, tmp_path):
    """Crea un archivo de configuración temporal."""
    import json

    config_file = tmp_path / 'config.json'
    with open(config_file, 'w') as f:
        json.dump(test_config, f)

    return config_file


# ============================================================================
# FIXTURES DE REDIS
# ============================================================================

@pytest.fixture
def mock_redis():
    """Mock de cliente Redis."""
    mock = MagicMock()

    # Simular operaciones básicas
    mock.get.return_value = None
    mock.set.return_value = True
    mock.hgetall.return_value = {}
    mock.hset.return_value = True
    mock.delete.return_value = True
    mock.exists.return_value = False
    mock.keys.return_value = []

    return mock


@pytest.fixture
def redis_client_mock(mock_redis):
    """Patch del cliente Redis global."""
    with patch('redis.Redis', return_value=mock_redis):
        yield mock_redis


# ============================================================================
# FIXTURES DE FLASK
# ============================================================================

@pytest.fixture
def app():
    """Instancia de Flask app para testing."""
    # Nota: Este fixture se implementará cuando migremos la API
    # Por ahora, retorna None ya que la app aún está en src/app.py
    return None


@pytest.fixture
def client(app):
    """Cliente de prueba de Flask."""
    if app is None:
        pytest.skip("Flask app not migrated yet")

    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        yield client


@pytest.fixture
def authenticated_client(client, test_config):
    """Cliente de Flask con autenticación."""
    with client.session_transaction() as sess:
        sess['authenticated'] = True
        sess['machine_id'] = test_config['machine_id']

    yield client


# ============================================================================
# FIXTURES DE CELERY
# ============================================================================

@pytest.fixture
def mock_celery_app():
    """Mock de aplicación Celery."""
    mock = MagicMock()
    mock.control = MagicMock()
    mock.control.shutdown.return_value = None

    return mock


@pytest.fixture
def celery_task_mock():
    """Mock de tarea Celery."""
    mock = MagicMock()
    mock.delay.return_value = MagicMock(id='test_task_id_123')
    mock.apply_async.return_value = MagicMock(id='test_task_id_123')

    return mock


# ============================================================================
# FIXTURES DE PROCESOS
# ============================================================================

@pytest.fixture
def mock_subprocess():
    """Mock de subprocess para tests."""
    with patch('subprocess.run') as mock_run, \
         patch('subprocess.Popen') as mock_popen:

        # Configurar comportamiento por defecto
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='',
            stderr=''
        )

        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.pid = 12345
        mock_process.returncode = None
        mock_popen.return_value = mock_process

        yield {
            'run': mock_run,
            'popen': mock_popen,
            'process': mock_process
        }


# ============================================================================
# FIXTURES DE ARCHIVOS Y DIRECTORIOS
# ============================================================================

@pytest.fixture
def temp_robot_folder(tmp_path):
    """Carpeta temporal para robots de prueba."""
    robot_folder = tmp_path / 'robots'
    robot_folder.mkdir()

    # Crear estructura básica de robot
    (robot_folder / 'requirements.txt').write_text('requests==2.32.2\n')
    (robot_folder / 'main.py').write_text('print("Test robot")\n')

    return robot_folder


@pytest.fixture
def temp_ssl_folder(tmp_path):
    """Carpeta temporal con certificados SSL de prueba."""
    ssl_folder = tmp_path / 'ssl'
    ssl_folder.mkdir()

    # Crear certificados dummy
    (ssl_folder / 'cert.pem').write_text('DUMMY CERT')
    (ssl_folder / 'key.pem').write_text('DUMMY KEY')
    (ssl_folder / 'ca-cert.pem').write_text('DUMMY CA CERT')

    return ssl_folder


# ============================================================================
# FIXTURES DE MOCKING GLOBAL
# ============================================================================

@pytest.fixture
def mock_psutil():
    """Mock de psutil para control de procesos."""
    with patch('psutil.Process') as mock_process_class:
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.status.return_value = 'running'
        mock_process.is_running.return_value = True
        mock_process.children.return_value = []

        mock_process_class.return_value = mock_process

        yield mock_process


@pytest.fixture
def mock_git():
    """Mock de GitPython."""
    with patch('git.Repo') as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.clone_from.return_value = mock_repo
        mock_repo.remotes.origin.pull.return_value = None

        mock_repo_class.return_value = mock_repo

        yield mock_repo


# ============================================================================
# FIXTURES DE VARIABLES DE ENTORNO
# ============================================================================

@pytest.fixture
def clean_env(monkeypatch):
    """Limpia variables de entorno para tests."""
    # Guardar entorno actual
    env_vars = ['FLASK_APP', 'FLASK_ENV', 'REDIS_HOST', 'REDIS_PORT']

    for var in env_vars:
        monkeypatch.delenv(var, raising=False)

    yield

    # El monkeypatch automáticamente restaura el entorno


@pytest.fixture
def test_env(monkeypatch):
    """Configura variables de entorno de prueba."""
    monkeypatch.setenv('FLASK_ENV', 'testing')
    monkeypatch.setenv('REDIS_HOST', 'localhost')
    monkeypatch.setenv('REDIS_PORT', '6378')
    monkeypatch.setenv('CELERY_BROKER_URL', 'redis://localhost:6378/0')

    yield


# ============================================================================
# HOOKS DE PYTEST
# ============================================================================

def pytest_configure(config):
    """Configuración inicial de pytest."""
    # Registrar markers personalizados
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow"
    )


def pytest_collection_modifyitems(config, items):
    """Modifica items de la colección de tests."""
    # Añadir marker 'unit' a todos los tests en tests/unit/
    # Añadir marker 'integration' a todos los tests en tests/integration/

    for item in items:
        if 'tests/unit' in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif 'tests/integration' in str(item.fspath):
            item.add_marker(pytest.mark.integration)
