"""
Unit tests for shared.state StateManager (backend-agnostic).

Tests StateManager con backends abstractos (SQLite y mocks).
"""
import time
from unittest.mock import MagicMock, patch

import pytest


# ============================================================================
# Tests for StateManager
# ============================================================================

class TestStateManager:
    """Tests for backend-agnostic StateManager."""

    def test_init_with_backend(self, mock_state_backend):
        """Test StateManager initialization with custom backend."""
        from shared.state.state import StateManager

        manager = StateManager(backend=mock_state_backend)

        assert manager.backend == mock_state_backend
        assert manager.machine_id is None
        mock_state_backend.ping.assert_called_once()

    def test_init_auto_backend(self):
        """Test StateManager auto-detects backend."""
        from shared.state.state import StateManager

        with patch('shared.state.state.get_state_backend') as mock_get_backend:
            mock_backend = MagicMock()
            mock_backend.ping.return_value = True
            mock_get_backend.return_value = mock_backend

            manager = StateManager()

            assert manager.backend == mock_backend
            mock_get_backend.assert_called_once()

    def test_init_connection_error(self):
        """Test StateManager raises ConnectionError if backend unavailable."""
        from shared.state.state import StateManager

        mock_backend = MagicMock()
        mock_backend.ping.return_value = False

        with pytest.raises(ConnectionError, match="No se pudo conectar"):
            StateManager(backend=mock_backend)

    def test_set_machine_id(self, mock_state_manager):
        """Test setting machine_id."""
        mock_state_manager.set_machine_id('test_machine_123')

        assert mock_state_manager.machine_id == 'test_machine_123'

    # ------------------------------------------------------------------------
    # Execution State Tests
    # ------------------------------------------------------------------------

    def test_save_execution_state(self, mock_state_manager):
        """Test saving execution state."""
        state = {
            'status': 'running',
            'task_id': 'xyz123',
            'started_at': time.time()
        }

        mock_state_manager.save_execution_state('exec123', state)

        # Verify backend was called
        mock_state_manager.backend.hset.assert_called_once()
        call_args = mock_state_manager.backend.hset.call_args
        assert call_args[0][0] == 'execution:exec123'
        assert 'status' in call_args[0][1]

    def test_save_execution_state_empty_id(self, mock_state_manager, capsys):
        """Test saving state with empty execution_id."""
        mock_state_manager.save_execution_state('', {'status': 'running'})

        captured = capsys.readouterr()
        assert 'execution_id vacío' in captured.out
        mock_state_manager.backend.hset.assert_not_called()

    def test_get_execution_state(self, mock_state_manager):
        """Test getting execution state."""
        mock_state_manager.backend.hgetall.return_value = {
            'status': 'running',
            'task_id': 'xyz123'
        }

        state = mock_state_manager.get_execution_state('exec123')

        assert state is not None
        assert state['status'] == 'running'
        assert state['task_id'] == 'xyz123'

    def test_get_execution_state_not_found(self, mock_state_manager):
        """Test getting non-existent state."""
        mock_state_manager.backend.hgetall.return_value = {}

        state = mock_state_manager.get_execution_state('exec123')

        assert state == {}

    def test_get_execution_state_with_bytes(self, mock_state_manager):
        """Test getting state with byte values."""
        mock_state_manager.backend.hgetall.return_value = {
            b'status': b'running',
            b'task_id': b'xyz123'
        }

        state = mock_state_manager.get_execution_state('exec123')

        assert state['status'] == 'running'
        assert state['task_id'] == 'xyz123'

    # ------------------------------------------------------------------------
    # Server Status Tests
    # ------------------------------------------------------------------------

    def test_set_server_status(self, mock_state_manager):
        """Test setting server status."""
        mock_state_manager.set_server_status('running')

        mock_state_manager.backend.set.assert_called_with(
            'server:TEST_MACHINE:status',
            'running'
        )

    def test_set_server_status_no_machine_id(self, mock_state_backend, capsys):
        """Test setting status without machine_id."""
        from shared.state.state import StateManager

        manager = StateManager(backend=mock_state_backend)
        manager.set_server_status('running')

        captured = capsys.readouterr()
        assert 'machine_id no configurado' in captured.out
        mock_state_backend.set.assert_not_called()

    def test_get_server_status(self, mock_state_manager):
        """Test getting server status."""
        mock_state_manager.backend.get.return_value = 'running'

        status = mock_state_manager.get_server_status()

        assert status == 'running'
        mock_state_manager.backend.get.assert_called_with('server:TEST_MACHINE:status')

    def test_get_server_status_no_machine_id(self, mock_state_backend):
        """Test getting status without machine_id."""
        from shared.state.state import StateManager

        manager = StateManager(backend=mock_state_backend)
        status = manager.get_server_status()

        assert status == 'unknown'

    # ------------------------------------------------------------------------
    # Pause Control Tests
    # ------------------------------------------------------------------------

    def test_set_pause_control(self, mock_state_manager):
        """Test setting pause control."""
        with patch('time.time', return_value=1234567890.0):
            mock_state_manager.set_pause_control('exec123', pause_requested=True)

        mock_state_manager.backend.hset.assert_called_once()
        call_args = mock_state_manager.backend.hset.call_args
        assert call_args[0][0] == 'execution:exec123:pause_control'
        assert call_args[0][1]['pause_requested'] == 'true'

    def test_request_pause(self, mock_state_manager):
        """Test requesting pause."""
        with patch('time.time', return_value=1234567890.0):
            mock_state_manager.request_pause('exec123')

        mock_state_manager.backend.hset.assert_called_once()

    def test_request_resume(self, mock_state_manager):
        """Test requesting resume."""
        with patch('time.time', return_value=1234567890.0):
            mock_state_manager.request_resume('exec123')

        mock_state_manager.backend.hset.assert_called_once()

    def test_get_pause_control(self, mock_state_manager):
        """Test getting pause control state."""
        mock_state_manager.backend.hgetall.return_value = {
            'pause_requested': 'true',
            'resume_requested': 'false'
        }

        control = mock_state_manager.get_pause_control('exec123')

        assert control['pause_requested'] is True
        assert control['resume_requested'] is False

    def test_get_pause_control_empty(self, mock_state_manager):
        """Test getting pause control when no data."""
        mock_state_manager.backend.hgetall.return_value = {}

        control = mock_state_manager.get_pause_control('exec123')

        assert control['pause_requested'] is False
        assert control['resume_requested'] is False

    def test_clear_pause_control(self, mock_state_manager):
        """Test clearing pause control."""
        mock_state_manager.clear_pause_control('exec123')

        mock_state_manager.backend.delete.assert_called_with('execution:exec123:pause_control')

    # ------------------------------------------------------------------------
    # Orphaned Executions Tests
    # ------------------------------------------------------------------------

    def test_mark_orphaned_executions_as_failed(self, mock_state_manager):
        """Test marking orphaned executions as failed."""
        # Mock orphaned execution
        mock_state_manager.backend.keys.return_value = ['execution:exec123']
        mock_state_manager.backend.hgetall.return_value = {
            'status': 'running',
            'task_id': 'xyz123'
        }

        with patch('time.time', return_value=1234567890.0):
            mock_state_manager.mark_orphaned_executions_as_failed()

        # Verify backend operations
        assert mock_state_manager.backend.hset.called
        assert mock_state_manager.backend.delete.called

    # ------------------------------------------------------------------------
    # Generic Backend Methods Tests
    # ------------------------------------------------------------------------

    def test_hset(self, mock_state_manager):
        """Test generic hset method."""
        mock_state_manager.hset('test:key', {'field': 'value'})

        mock_state_manager.backend.hset.assert_called_with('test:key', {'field': 'value'})

    def test_hgetall(self, mock_state_manager):
        """Test generic hgetall method."""
        mock_state_manager.backend.hgetall.return_value = {'field': 'value'}

        result = mock_state_manager.hgetall('test:key')

        assert result == {'field': 'value'}
        mock_state_manager.backend.hgetall.assert_called_with('test:key')

    def test_set(self, mock_state_manager):
        """Test generic set method."""
        mock_state_manager.set('test:key', 'value')

        mock_state_manager.backend.set.assert_called_with('test:key', 'value')

    def test_get(self, mock_state_manager):
        """Test generic get method."""
        mock_state_manager.backend.get.return_value = 'value'

        result = mock_state_manager.get('test:key')

        assert result == 'value'
        mock_state_manager.backend.get.assert_called_with('test:key')

    def test_delete(self, mock_state_manager):
        """Test generic delete method."""
        mock_state_manager.delete('key1', 'key2')

        # Verify delete was called twice (once per key)
        assert mock_state_manager.backend.delete.call_count == 2

    def test_keys(self, mock_state_manager):
        """Test generic keys method."""
        mock_state_manager.backend.keys.return_value = ['key1', 'key2']

        result = mock_state_manager.keys('pattern:*')

        assert result == ['key1', 'key2']
        mock_state_manager.backend.keys.assert_called_with('pattern:*')

    def test_ping(self, mock_state_manager):
        """Test generic ping method."""
        mock_state_manager.backend.ping.return_value = True

        result = mock_state_manager.ping()

        assert result is True
        # Note: ping is called in __init__, so call_count >= 1
        assert mock_state_manager.backend.ping.call_count >= 1


# ============================================================================
# Integration Tests with SQLite Backend
# ============================================================================

class TestStateManagerWithSQLite:
    """Integration tests using real SQLite backend."""

    def test_save_and_get_execution_state(self, state_manager_with_sqlite):
        """Test saving and retrieving execution state with SQLite."""
        state = {
            'status': 'running',
            'task_id': 'xyz123',
            'started_at': str(time.time())
        }

        state_manager_with_sqlite.save_execution_state('exec123', state)
        retrieved = state_manager_with_sqlite.get_execution_state('exec123')

        assert retrieved['status'] == 'running'
        assert retrieved['task_id'] == 'xyz123'

    def test_server_status_roundtrip(self, state_manager_with_sqlite):
        """Test setting and getting server status with SQLite."""
        state_manager_with_sqlite.set_server_status('running')
        status = state_manager_with_sqlite.get_server_status()

        assert status == 'running'

    def test_pause_control_roundtrip(self, state_manager_with_sqlite):
        """Test pause control with SQLite."""
        state_manager_with_sqlite.request_pause('exec123')
        control = state_manager_with_sqlite.get_pause_control('exec123')

        assert control['pause_requested'] is True
        assert control['resume_requested'] is False

        state_manager_with_sqlite.request_resume('exec123')
        control = state_manager_with_sqlite.get_pause_control('exec123')

        assert control['pause_requested'] is False
        assert control['resume_requested'] is True

    def test_generic_methods_with_sqlite(self, state_manager_with_sqlite):
        """Test generic backend methods with SQLite."""
        # Test hset/hgetall
        state_manager_with_sqlite.hset('test:hash', {'field1': 'value1', 'field2': 'value2'})
        result = state_manager_with_sqlite.hgetall('test:hash')
        assert result['field1'] == 'value1'
        assert result['field2'] == 'value2'

        # Test set/get
        state_manager_with_sqlite.set('test:string', 'test_value')
        result = state_manager_with_sqlite.get('test:string')
        assert result == 'test_value'

        # Test keys
        keys = state_manager_with_sqlite.keys('test:*')
        assert len(keys) >= 2

        # Test delete
        state_manager_with_sqlite.delete('test:hash', 'test:string')
        assert state_manager_with_sqlite.get('test:string') is None


# ============================================================================
# Tests for Singleton get_state_manager()
# ============================================================================

class TestGetStateManager:
    """Tests for get_state_manager() singleton function."""

    def test_singleton_pattern(self):
        """Test that get_state_manager returns same instance."""
        from shared.state.state import get_state_manager, _state_manager

        # Reset singleton
        import shared.state.state as state_module
        state_module._state_manager = None

        with patch('shared.state.state.get_state_backend') as mock_get_backend:
            mock_backend = MagicMock()
            mock_backend.ping.return_value = True
            mock_get_backend.return_value = mock_backend

            instance1 = get_state_manager()
            instance2 = get_state_manager()

            assert instance1 is instance2
            # Should only create backend once
            mock_get_backend.assert_called_once()

    def test_redis_state_compatibility(self):
        """Test that redis_state is alias to StateManager."""
        from shared.state.state import redis_state, get_state_manager

        # They should reference the same object
        assert type(redis_state).__name__ == 'StateManager'