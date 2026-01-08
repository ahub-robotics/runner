"""
Unit tests for api.middleware module.

Tests request logging, server initialization, and middleware functions.
"""
import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from flask import Flask


@pytest.fixture
def app():
    """Create test Flask app."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['TESTING'] = True
    return app


@pytest.fixture
def mock_server():
    """Mock server instance."""
    server = MagicMock()
    server.machine_id = 'test_machine'
    server.token = 'test_token'
    server.status = 'free'
    return server


class TestInitServerIfNeeded:
    """Tests for init_server_if_needed function."""

    def test_init_server_creates_new_server(self, app, test_config):
        """Test server initialization when none exists."""
        from api.middleware import init_server_if_needed

        with patch('api.middleware.get_server', return_value=None):
            with patch('api.middleware.set_server') as mock_set:
                with patch('api.middleware.get_config_data', return_value=test_config):
                    with patch('api.middleware.Server') as MockServer:
                        mock_server_instance = MagicMock()
                        MockServer.return_value = mock_server_instance

                        server = init_server_if_needed(app)

                        # Verify server was created
                        MockServer.assert_called_once_with(test_config)
                        mock_set.assert_called_once_with(mock_server_instance)
                        assert server == mock_server_instance

    def test_init_server_returns_existing(self, app, mock_server):
        """Test that existing server is returned."""
        from api.middleware import init_server_if_needed

        with patch('api.middleware.get_server', return_value=mock_server):
            server = init_server_if_needed(app)
            assert server == mock_server

    @patch('api.middleware.redis_state')
    def test_init_server_configures_redis(self, mock_redis, app, test_config):
        """Test that Redis is configured during initialization."""
        from api.middleware import init_server_if_needed

        with patch('api.middleware.get_server', return_value=None):
            with patch('api.middleware.set_server'):
                with patch('api.middleware.get_config_data', return_value=test_config):
                    with patch('api.middleware.Server'):
                        init_server_if_needed(app)

                        # Verify Redis configuration
                        mock_redis.set_machine_id.assert_called_once_with('TEST_MACHINE_ID')
                        mock_redis.mark_orphaned_executions_as_failed.assert_called_once()


class TestLogRequestToFile:
    """Tests for log_request_to_file function."""

    def test_log_request_writes_to_file(self):
        """Test that requests are logged to file."""
        from api.middleware import log_request_to_file, REQUEST_LOG_FILE

        request = MagicMock()
        request.method = 'GET'
        request.path = '/test'
        request.args = {}

        m = mock_open()
        with patch('builtins.open', m):
            log_request_to_file(request)

            # Verify file was opened for append
            m.assert_called_once_with(REQUEST_LOG_FILE, 'a')

            # Verify content was written
            handle = m()
            written = ''.join(call.args[0] for call in handle.write.call_args_list)
            assert 'GET' in written
            assert '/test' in written

    def test_log_request_handles_errors_gracefully(self):
        """Test that logging errors don't crash the app."""
        from api.middleware import log_request_to_file

        request = MagicMock()
        request.method = 'GET'
        request.path = '/test'

        with patch('builtins.open', side_effect=IOError("Disk full")):
            # Should not raise exception
            try:
                log_request_to_file(request)
            except Exception as e:
                pytest.fail(f"log_request_to_file raised {e}")


class TestBeforeRequestMiddleware:
    """Tests for before_request_middleware function."""

    def test_before_request_initializes_server(self, app):
        """Test that server is initialized before first request."""
        from api.middleware import before_request_middleware

        with patch('api.middleware.init_server_if_needed') as mock_init:
            with app.test_request_context('/test'):
                before_request_middleware()
                mock_init.assert_called_once()

    def test_before_request_auto_authenticates(self, app, mock_server):
        """Test auto-authentication from URL parameters."""
        from api.middleware import before_request_middleware

        with patch('api.middleware.get_server', return_value=mock_server):
            with app.test_request_context('/test?token=test_token'):
                with app.test_client() as client:
                    with client.session_transaction() as sess:
                        # Session should be empty initially
                        assert 'authenticated' not in sess

                    before_request_middleware()

                    with client.session_transaction() as sess:
                        # Should be authenticated now
                        assert sess.get('authenticated') == True


class TestAfterRequestMiddleware:
    """Tests for after_request_middleware function."""

    def test_after_request_logs_request(self, app):
        """Test that requests are logged after processing."""
        from api.middleware import after_request_middleware

        response = MagicMock()
        response.status_code = 200

        with patch('api.middleware.log_request_to_file') as mock_log:
            with app.test_request_context('/test'):
                result = after_request_middleware(response)

                mock_log.assert_called_once()
                assert result == response

    def test_after_request_returns_response(self, app):
        """Test that response is returned unchanged."""
        from api.middleware import after_request_middleware

        response = MagicMock()
        response.status_code = 200

        with patch('api.middleware.log_request_to_file'):
            with app.test_request_context('/test'):
                result = after_request_middleware(response)
                assert result is response
