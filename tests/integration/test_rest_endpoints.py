"""
Integration tests for REST API endpoints.

Tests complete request/response cycles for robot control endpoints.
"""
import pytest
import json
from unittest.mock import MagicMock, patch
from flask import Flask


@pytest.fixture
def app():
    """Create test Flask app with REST blueprints."""
    from api.app import create_app
    app = create_app({'TESTING': True})
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def auth_headers():
    """Valid authentication headers."""
    return {'Authorization': 'Bearer test_token_123'}


@pytest.fixture
def mock_server():
    """Mock server instance."""
    server = MagicMock()
    server.token = 'test_token_123'
    server.machine_id = 'test_machine'
    server.license_key = 'test_license'
    server.status = 'free'
    server.run_robot_process = None
    server.execution_id = None
    return server


class TestStatusEndpoints:
    """Integration tests for status endpoints."""

    def test_get_status_authenticated(self, client, mock_server):
        """Test GET /status with valid authentication."""
        with patch('api.rest.status.get_server', return_value=mock_server):
            response = client.get(
                '/status',
                query_string={
                    'machine_id': 'test_machine',
                    'license_key': 'test_license'
                },
                headers={'Authorization': 'Bearer test_token_123'}
            )

            assert response.status_code == 200
            data = response.json
            assert data in ['free', 'running', 'blocked', 'closed']

    def test_get_status_invalid_credentials(self, client, mock_server):
        """Test GET /status with invalid credentials."""
        with patch('api.rest.status.get_server', return_value=mock_server):
            response = client.get(
                '/status',
                query_string={
                    'machine_id': 'wrong_id',
                    'license_key': 'wrong_key'
                },
                headers={'Authorization': 'Bearer test_token_123'}
            )

            assert response.status_code == 200
            assert response.json == 'closed'

    def test_get_execution_status(self, client, mock_server):
        """Test GET /execution with valid execution_id."""
        mock_state = {
            'execution_id': 'test_exec_123',
            'status': 'running',
            'task_id': 'celery_task_123'
        }

        with patch('api.rest.status.get_server', return_value=mock_server):
            with patch('api.rest.status.redis_state.load_execution_state', return_value=mock_state):
                response = client.get(
                    '/execution',
                    query_string={'id': 'test_exec_123'},
                    headers={'Authorization': 'Bearer test_token_123'}
                )

                assert response.status_code == 200
                data = response.json
                assert data['status'] == 'working'  # 'running' maps to 'working'

    def test_get_execution_status_not_found(self, client, mock_server):
        """Test GET /execution with non-existent execution."""
        with patch('api.rest.status.get_server', return_value=mock_server):
            with patch('api.rest.status.redis_state.load_execution_state', return_value=None):
                response = client.get(
                    '/execution',
                    query_string={'id': 'nonexistent'},
                    headers={'Authorization': 'Bearer test_token_123'}
                )

                assert response.status_code == 200
                data = response.json
                assert data['status'] == 'fail'


class TestExecutionEndpoints:
    """Integration tests for execution control endpoints."""

    def test_post_run_valid(self, client, mock_server):
        """Test POST /run with valid robot data."""
        robot_data = {
            'robot_file': 'test_robot.robot',
            'params': {'env': 'test'},
            'execution_id': 'test_exec_456'
        }

        mock_task = MagicMock()
        mock_task.id = 'celery_task_456'

        with patch('api.rest.execution.get_server', return_value=mock_server):
            with patch('api.rest.execution.run_robot_task.delay', return_value=mock_task):
                with patch('api.rest.execution.redis_state.save_execution_state'):
                    response = client.post(
                        '/run',
                        data=json.dumps(robot_data),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token_123'}
                    )

                    assert response.status_code == 200
                    data = response.json
                    assert data['message'] == 'running'
                    assert data['execution_id'] == 'test_exec_456'
                    assert 'task_id' in data

    def test_post_run_no_json(self, client, mock_server):
        """Test POST /run without JSON data."""
        with patch('api.rest.execution.get_server', return_value=mock_server):
            response = client.post(
                '/run',
                headers={'Authorization': 'Bearer test_token_123'}
            )

            assert response.status_code == 400
            data = response.json
            assert 'No JSON data' in data['message']

    def test_get_stop_valid(self, client, mock_server):
        """Test GET /stop with valid execution_id."""
        mock_state = {
            'execution_id': 'test_exec_789',
            'status': 'running',
            'task_id': 'celery_task_789'
        }

        with patch('api.rest.execution.get_server', return_value=mock_server):
            with patch('api.rest.execution.redis_state.load_execution_state', return_value=mock_state):
                with patch('api.rest.execution.celery_app.control.revoke'):
                    with patch('api.rest.execution.redis_state.save_execution_state'):
                        response = client.get(
                            '/stop',
                            query_string={'execution_id': 'test_exec_789'},
                            headers={'Authorization': 'Bearer test_token_123'}
                        )

                        assert response.status_code == 200
                        data = response.json
                        assert data['message'] == 'OK'

    def test_get_stop_not_found(self, client, mock_server):
        """Test GET /stop with non-existent execution."""
        with patch('api.rest.execution.get_server', return_value=mock_server):
            with patch('api.rest.execution.redis_state.load_execution_state', return_value=None):
                response = client.get(
                    '/stop',
                    query_string={'execution_id': 'nonexistent'},
                    headers={'Authorization': 'Bearer test_token_123'}
                )

                assert response.status_code == 400
                data = response.json
                assert 'mismatch' in data['message']


class TestInfoEndpoints:
    """Integration tests for server info endpoints."""

    def test_get_server_info(self, client, mock_server):
        """Test GET /api/server-info."""
        with patch('api.rest.info.get_server', return_value=mock_server):
            with patch('api.rest.info.redis_state.get_server_status', return_value='free'):
                with client.session_transaction() as sess:
                    sess['authenticated'] = True

                response = client.get('/api/server-info')

                assert response.status_code == 200
                data = response.json
                assert data['status'] == 'free'
                assert data['machine_id'] == 'test_machine'
                assert 'port' in data

    def test_get_logs(self, client):
        """Test GET /api/logs."""
        mock_logs = [
            "[2024-01-01 10:00:00] Server started\n",
            "[2024-01-01 10:01:00] Task executed\n"
        ]

        with client.session_transaction() as sess:
            sess['authenticated'] = True

        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.readlines.return_value = mock_logs
            mock_file.__enter__.return_value = mock_file
            mock_open.return_value = mock_file

            response = client.get('/api/logs?lines=100')

            assert response.status_code == 200
            data = response.json
            assert data['success'] is True
            assert 'logs' in data
            assert data['total'] >= 0
