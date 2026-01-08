"""
Unit tests for api.auth module.

Tests authentication decorators and token validation.
"""
import pytest
from unittest.mock import MagicMock, patch
from flask import Flask, session


@pytest.fixture
def app():
    """Create test Flask app."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def mock_server():
    """Mock server instance."""
    server = MagicMock()
    server.token = 'test_token_123'
    server.machine_id = 'test_machine'
    server.license_key = 'test_license'
    return server


class TestRequireToken:
    """Tests for @require_token decorator."""

    def test_require_token_valid(self, app, client, mock_server):
        """Test @require_token with valid token."""
        from api.auth import require_token

        @app.route('/test')
        @require_token
        def test_endpoint():
            return {'status': 'ok'}

        with patch('api.auth.get_server', return_value=mock_server):
            response = client.get(
                '/test',
                headers={'Authorization': 'Bearer test_token_123'}
            )
            assert response.status_code == 200
            assert response.json['status'] == 'ok'

    def test_require_token_missing(self, app, client, mock_server):
        """Test @require_token without token."""
        from api.auth import require_token

        @app.route('/test')
        @require_token
        def test_endpoint():
            return {'status': 'ok'}

        with patch('api.auth.get_server', return_value=mock_server):
            response = client.get('/test')
            assert response.status_code == 401
            assert 'error' in response.json

    def test_require_token_invalid(self, app, client, mock_server):
        """Test @require_token with invalid token."""
        from api.auth import require_token

        @app.route('/test')
        @require_token
        def test_endpoint():
            return {'status': 'ok'}

        with patch('api.auth.get_server', return_value=mock_server):
            response = client.get(
                '/test',
                headers={'Authorization': 'Bearer wrong_token'}
            )
            assert response.status_code == 403
            assert 'error' in response.json

    def test_require_token_bearer_prefix(self, app, client, mock_server):
        """Test @require_token handles Bearer prefix."""
        from api.auth import require_token

        @app.route('/test')
        @require_token
        def test_endpoint():
            return {'status': 'ok'}

        with patch('api.auth.get_server', return_value=mock_server):
            # Without Bearer prefix
            response = client.get(
                '/test',
                headers={'Authorization': 'test_token_123'}
            )
            assert response.status_code == 200


class TestRequireAuth:
    """Tests for @require_auth decorator."""

    def test_require_auth_with_session(self, app, client, mock_server):
        """Test @require_auth with valid session."""
        from api.auth import require_auth

        @app.route('/test')
        @require_auth
        def test_endpoint():
            return {'status': 'ok'}

        with patch('api.auth.get_server', return_value=mock_server):
            with client.session_transaction() as sess:
                sess['authenticated'] = True

            response = client.get('/test')
            assert response.status_code == 200

    def test_require_auth_with_token(self, app, client, mock_server):
        """Test @require_auth with valid token (API mode)."""
        from api.auth import require_auth

        @app.route('/test')
        @require_auth
        def test_endpoint():
            return {'status': 'ok'}

        with patch('api.auth.get_server', return_value=mock_server):
            response = client.get(
                '/test',
                headers={'Authorization': 'Bearer test_token_123'}
            )
            assert response.status_code == 200

    def test_require_auth_unauthorized_web(self, app, client, mock_server):
        """Test @require_auth redirects to login for web requests."""
        from api.auth import require_auth

        @app.route('/test')
        @require_auth
        def test_endpoint():
            return {'status': 'ok'}

        with patch('api.auth.get_server', return_value=mock_server):
            response = client.get('/test')
            # Should redirect to login for web requests
            assert response.status_code in [302, 401]


class TestRequireAuthSSE:
    """Tests for @require_auth_sse decorator."""

    def test_require_auth_sse_with_session(self, app, client, mock_server):
        """Test @require_auth_sse with valid session."""
        from api.auth import require_auth_sse

        @app.route('/test')
        @require_auth_sse
        def test_endpoint():
            return {'status': 'ok'}

        with patch('api.auth.get_server', return_value=mock_server):
            with client.session_transaction() as sess:
                sess['authenticated'] = True

            response = client.get('/test')
            assert response.status_code == 200

    def test_require_auth_sse_with_token(self, app, client, mock_server):
        """Test @require_auth_sse with valid token."""
        from api.auth import require_auth_sse

        @app.route('/test')
        @require_auth_sse
        def test_endpoint():
            return {'status': 'ok'}

        with patch('api.auth.get_server', return_value=mock_server):
            response = client.get(
                '/test',
                headers={'Authorization': 'Bearer test_token_123'}
            )
            assert response.status_code == 200

    def test_require_auth_sse_unauthorized(self, app, client, mock_server):
        """Test @require_auth_sse sends error via SSE."""
        from api.auth import require_auth_sse

        @app.route('/test')
        @require_auth_sse
        def test_endpoint():
            def generate():
                yield "data: test\n\n"
            from flask import Response
            return Response(generate(), mimetype='text/event-stream')

        with patch('api.auth.get_server', return_value=mock_server):
            response = client.get('/test')
            # Should return SSE error, not redirect
            assert response.mimetype == 'text/event-stream'
            assert b'error_unauthorized' in response.data
