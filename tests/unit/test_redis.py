"""
Unit tests for shared.state Redis modules.

Tests RedisClient, RedisManager, and RedisStateManager.
"""
import time
from unittest.mock import MagicMock, Mock, patch, call

import pytest


# ============================================================================
# Tests for shared.state.redis_client
# ============================================================================

class TestRedisClient:
    """Tests for RedisClient singleton."""

    def test_singleton_pattern(self):
        """Test that RedisClient is a singleton."""
        from shared.state.redis_client import RedisClient

        instance1 = RedisClient()
        instance2 = RedisClient()

        assert instance1 is instance2

    def test_configure(self):
        """Test configuration of Redis URL."""
        from shared.state.redis_client import RedisClient

        RedisClient.reset()  # Clean state
        RedisClient.configure('redis://localhost:6379/1')

        assert RedisClient._redis_url == 'redis://localhost:6379/1'

    def test_get_client_success(self, mock_redis):
        """Test successful client connection."""
        from shared.state.redis_client import RedisClient

        RedisClient.reset()

        with patch('redis.from_url', return_value=mock_redis):
            client = RedisClient.get_client()

            assert client is not None
            assert client == mock_redis
            mock_redis.ping.assert_called()

    def test_get_client_connection_error(self):
        """Test client connection failure."""
        from shared.state.redis_client import RedisClient
        import redis as redis_module

        RedisClient.reset()

        mock_client = MagicMock()
        mock_client.ping.side_effect = redis_module.ConnectionError("Connection refused")

        with patch('redis.from_url', return_value=mock_client), \
             pytest.raises(ConnectionError) as exc_info:

            RedisClient.get_client()

        assert "No se pudo conectar a Redis" in str(exc_info.value)

    def test_is_connected_true(self, mock_redis):
        """Test is_connected when connected."""
        from shared.state.redis_client import RedisClient

        RedisClient.reset()

        with patch('redis.from_url', return_value=mock_redis):
            RedisClient.get_client()
            assert RedisClient.is_connected() is True

    def test_is_connected_false(self):
        """Test is_connected when not connected."""
        from shared.state.redis_client import RedisClient

        RedisClient.reset()
        assert RedisClient.is_connected() is False

    def test_close(self, mock_redis):
        """Test closing Redis connection."""
        from shared.state.redis_client import RedisClient

        RedisClient.reset()

        with patch('redis.from_url', return_value=mock_redis):
            RedisClient.get_client()
            RedisClient.close()

            mock_redis.close.assert_called_once()
            assert RedisClient._client is None

    def test_get_redis_client_helper(self, mock_redis):
        """Test helper function."""
        from shared.state.redis_client import get_redis_client

        with patch('redis.from_url', return_value=mock_redis):
            client = get_redis_client()

            assert client is not None
            assert client == mock_redis


# ============================================================================
# Tests for shared.state.redis_manager
# ============================================================================

class TestRedisManager:
    """Tests for RedisManager class."""

    def test_init(self):
        """Test RedisManager initialization."""
        from shared.state.redis_manager import RedisManager

        manager = RedisManager(redis_port=6379)

        assert manager.redis_port == 6379
        assert manager.redis_process is None

    def test_is_redis_installed_true(self):
        """Test Redis installed detection."""
        from shared.state.redis_manager import RedisManager

        manager = RedisManager()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='Redis server v=7.0.0\n'
            )

            result = manager.is_redis_installed()

            assert result is True
            mock_run.assert_called_once()

    def test_is_redis_installed_false(self):
        """Test Redis not installed detection."""
        from shared.state.redis_manager import RedisManager

        manager = RedisManager()

        with patch('subprocess.run', side_effect=FileNotFoundError):
            result = manager.is_redis_installed()

            assert result is False

    def test_is_redis_running_true(self, mock_redis):
        """Test Redis running detection."""
        from shared.state.redis_manager import RedisManager

        manager = RedisManager(redis_port=6378)

        with patch('redis.Redis', return_value=mock_redis):
            result = manager.is_redis_running()

            assert result is True
            mock_redis.ping.assert_called_once()

    def test_is_redis_running_false(self):
        """Test Redis not running detection."""
        from shared.state.redis_manager import RedisManager

        manager = RedisManager()

        with patch('redis.Redis', side_effect=Exception("Connection refused")):
            result = manager.is_redis_running()

            assert result is False

    def test_start_redis_already_running(self):
        """Test starting Redis when already running."""
        from shared.state.redis_manager import RedisManager

        manager = RedisManager()

        with patch.object(manager, 'is_redis_running', return_value=True):
            manager.start_redis()

            # Should not create process
            assert manager.redis_process is None

    def test_start_redis_success(self, mock_redis):
        """Test successful Redis start."""
        from shared.state.redis_manager import RedisManager

        manager = RedisManager(redis_port=6378)

        mock_process = MagicMock()
        mock_process.pid = 12345

        with patch.object(manager, 'is_redis_running', side_effect=[False, True]), \
             patch('subprocess.Popen', return_value=mock_process), \
             patch('time.sleep'):

            manager.start_redis()

            assert manager.redis_process == mock_process
            assert manager.redis_process.pid == 12345

    def test_start_redis_timeout(self):
        """Test Redis start timeout."""
        from shared.state.redis_manager import RedisManager

        manager = RedisManager()

        mock_process = MagicMock()

        with patch.object(manager, 'is_redis_running', return_value=False), \
             patch('subprocess.Popen', return_value=mock_process), \
             patch('time.sleep'), \
             pytest.raises(RuntimeError) as exc_info:

            manager.start_redis()

        assert "no inició en el tiempo esperado" in str(exc_info.value)

    def test_stop_redis_no_process(self):
        """Test stopping Redis when no process."""
        from shared.state.redis_manager import RedisManager

        manager = RedisManager()
        result = manager.stop_redis()

        assert result is False

    def test_stop_redis_success(self):
        """Test successful Redis stop."""
        from shared.state.redis_manager import RedisManager

        manager = RedisManager()
        mock_process = MagicMock()
        manager.redis_process = mock_process

        result = manager.stop_redis()

        assert result is True
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()
        assert manager.redis_process is None

    def test_stop_redis_force_kill(self):
        """Test force killing Redis on timeout."""
        from shared.state.redis_manager import RedisManager
        import subprocess

        manager = RedisManager()
        mock_process = MagicMock()
        mock_process.wait.side_effect = [subprocess.TimeoutExpired('redis-server', 5), None]
        manager.redis_process = mock_process

        result = manager.stop_redis()

        assert result is True
        mock_process.kill.assert_called_once()

    def test_get_redis_info_running(self, mock_redis):
        """Test getting Redis info when running."""
        from shared.state.redis_manager import RedisManager

        manager = RedisManager(redis_port=6378)

        mock_redis.info.return_value = {
            'redis_version': '7.0.0',
            'uptime_in_seconds': 3600,
            'connected_clients': 5,
            'used_memory_human': '1.5M'
        }

        with patch.object(manager, 'is_redis_running', return_value=True), \
             patch('redis.Redis', return_value=mock_redis):

            info = manager.get_redis_info()

            assert info is not None
            assert info['version'] == '7.0.0'
            assert info['uptime_seconds'] == 3600
            assert info['connected_clients'] == 5
            assert info['port'] == 6378

    def test_get_redis_info_not_running(self):
        """Test getting Redis info when not running."""
        from shared.state.redis_manager import RedisManager

        manager = RedisManager()

        with patch.object(manager, 'is_redis_running', return_value=False):
            info = manager.get_redis_info()

            assert info is None


# ============================================================================
# Tests for shared.state.redis_state
# ============================================================================

class TestRedisStateManager:
    """Tests for RedisStateManager class."""

    def test_init(self):
        """Test RedisStateManager initialization."""
        from shared.state.redis_state import RedisStateManager

        manager = RedisStateManager(redis_url='redis://localhost:6379/0')

        assert manager.redis_url == 'redis://localhost:6379/0'
        assert manager._redis_client is None
        assert manager.machine_id is None

    def test_set_machine_id(self):
        """Test setting machine_id."""
        from shared.state.redis_state import RedisStateManager

        manager = RedisStateManager()
        manager.set_machine_id('test_machine')

        assert manager.machine_id == 'test_machine'

    def test_get_redis_client_success(self, mock_redis):
        """Test successful client connection."""
        from shared.state.redis_state import RedisStateManager

        manager = RedisStateManager()

        with patch('redis.from_url', return_value=mock_redis):
            client = manager._get_redis_client()

            assert client == mock_redis
            mock_redis.ping.assert_called_once()

    def test_get_redis_client_error(self):
        """Test client connection error."""
        from shared.state.redis_state import RedisStateManager
        import redis as redis_module

        manager = RedisStateManager()

        mock_client = MagicMock()
        mock_client.ping.side_effect = redis_module.ConnectionError("Connection refused")

        with patch('redis.from_url', return_value=mock_client), \
             pytest.raises(ConnectionError):

            manager._get_redis_client()

    def test_save_execution_state(self, mock_redis):
        """Test saving execution state."""
        from shared.state.redis_state import RedisStateManager

        manager = RedisStateManager()

        with patch('redis.from_url', return_value=mock_redis):
            state = {
                'status': 'running',
                'task_id': 'xyz123',
                'started_at': time.time()
            }

            manager.save_execution_state('exec123', state, ttl=3600)

            # Verify hset was called
            assert mock_redis.hset.called
            # Verify expire was called
            mock_redis.expire.assert_called_with('execution:exec123', 3600)

    def test_save_execution_state_empty_id(self, capsys):
        """Test saving state with empty execution_id."""
        from shared.state.redis_state import RedisStateManager

        manager = RedisStateManager()
        manager.save_execution_state('', {'status': 'running'})

        captured = capsys.readouterr()
        assert 'execution_id vacío' in captured.out

    def test_load_execution_state(self, mock_redis):
        """Test loading execution state."""
        from shared.state.redis_state import RedisStateManager

        manager = RedisStateManager()

        mock_redis.hgetall.return_value = {
            b'status': b'running',
            b'task_id': b'xyz123'
        }

        with patch('redis.from_url', return_value=mock_redis):
            state = manager.load_execution_state('exec123')

            assert state is not None
            assert state['status'] == 'running'
            assert state['task_id'] == 'xyz123'

    def test_load_execution_state_not_found(self, mock_redis):
        """Test loading non-existent state."""
        from shared.state.redis_state import RedisStateManager

        manager = RedisStateManager()
        mock_redis.hgetall.return_value = {}

        with patch('redis.from_url', return_value=mock_redis):
            state = manager.load_execution_state('exec123')

            assert state is None

    def test_set_server_status(self, mock_redis):
        """Test setting server status."""
        from shared.state.redis_state import RedisStateManager

        manager = RedisStateManager()
        manager.set_machine_id('test_machine')

        with patch('redis.from_url', return_value=mock_redis):
            manager.set_server_status('running')

            mock_redis.set.assert_called_with('server:test_machine:status', 'running')

    def test_get_server_status(self, mock_redis):
        """Test getting server status."""
        from shared.state.redis_state import RedisStateManager

        manager = RedisStateManager()
        manager.set_machine_id('test_machine')

        mock_redis.get.return_value = b'running'

        with patch('redis.from_url', return_value=mock_redis):
            status = manager.get_server_status()

            assert status == 'running'

    def test_get_server_status_no_machine_id(self):
        """Test getting status without machine_id."""
        from shared.state.redis_state import RedisStateManager

        manager = RedisStateManager()
        status = manager.get_server_status()

        assert status == 'free'

    def test_request_pause(self, mock_redis):
        """Test requesting pause."""
        from shared.state.redis_state import RedisStateManager

        manager = RedisStateManager()

        with patch('redis.from_url', return_value=mock_redis), \
             patch('time.time', return_value=1234567890.0):

            manager.request_pause('exec123')

            # Verify hset was called
            assert mock_redis.hset.called
            # Verify expire was called
            mock_redis.expire.assert_called_with('execution:exec123:pause_control', 3600)

    def test_request_resume(self, mock_redis):
        """Test requesting resume."""
        from shared.state.redis_state import RedisStateManager

        manager = RedisStateManager()

        with patch('redis.from_url', return_value=mock_redis), \
             patch('time.time', return_value=1234567890.0):

            manager.request_resume('exec123')

            assert mock_redis.hset.called
            mock_redis.expire.assert_called_with('execution:exec123:pause_control', 3600)

    def test_get_pause_control(self, mock_redis):
        """Test getting pause control state."""
        from shared.state.redis_state import RedisStateManager

        manager = RedisStateManager()

        mock_redis.hgetall.return_value = {
            b'pause_requested': b'true',
            b'resume_requested': b'false'
        }

        with patch('redis.from_url', return_value=mock_redis):
            control = manager.get_pause_control('exec123')

            assert control['pause_requested'] is True
            assert control['resume_requested'] is False

    def test_get_pause_control_empty(self, mock_redis):
        """Test getting pause control when no data."""
        from shared.state.redis_state import RedisStateManager

        manager = RedisStateManager()
        mock_redis.hgetall.return_value = {}

        with patch('redis.from_url', return_value=mock_redis):
            control = manager.get_pause_control('exec123')

            assert control['pause_requested'] is False
            assert control['resume_requested'] is False

    def test_clear_pause_control(self, mock_redis):
        """Test clearing pause control."""
        from shared.state.redis_state import RedisStateManager

        manager = RedisStateManager()

        with patch('redis.from_url', return_value=mock_redis):
            manager.clear_pause_control('exec123')

            mock_redis.delete.assert_called_with('execution:exec123:pause_control')

    def test_mark_orphaned_executions_as_failed(self, mock_redis):
        """Test marking orphaned executions as failed."""
        from shared.state.redis_state import RedisStateManager

        manager = RedisStateManager()

        # Mock orphaned execution
        mock_redis.keys.return_value = [b'execution:exec123']
        mock_redis.hgetall.return_value = {
            b'status': b'running',
            b'task_id': b'xyz123'
        }

        with patch('redis.from_url', return_value=mock_redis), \
             patch('time.time', return_value=1234567890.0):

            manager.mark_orphaned_executions_as_failed()

            # Verify hset was called to mark as failed
            assert mock_redis.hset.called
            # Verify delete was called to clear pause control
            assert mock_redis.delete.called
