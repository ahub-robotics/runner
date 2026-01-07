"""
Unit tests for shared.celery_app modules.

Tests Celery configuration and worker thread management.
"""
import threading
from unittest.mock import MagicMock, Mock, patch, call

import pytest


# ============================================================================
# Tests for shared.celery_app.config
# ============================================================================

class TestCeleryConfig:
    """Tests for Celery configuration."""

    def test_celery_app_created(self):
        """Test that celery_app is created."""
        from shared.celery_app.config import celery_app

        assert celery_app is not None
        assert celery_app.main == 'robotrunner'

    def test_redis_url_from_env(self):
        """Test Redis URL from environment variable."""
        with patch.dict('os.environ', {'REDIS_URL': 'redis://localhost:6379/1'}):
            # Re-import to pick up env variable
            import importlib
            import shared.celery_app.config
            importlib.reload(shared.celery_app.config)

            from shared.celery_app.config import REDIS_URL
            assert 'redis://localhost:6379/1' in REDIS_URL

    def test_redis_url_default(self):
        """Test default Redis URL."""
        with patch.dict('os.environ', {}, clear=True):
            import importlib
            import shared.celery_app.config
            importlib.reload(shared.celery_app.config)

            from shared.celery_app.config import REDIS_URL
            assert REDIS_URL == 'redis://localhost:6378/0'

    def test_celery_config_worker_pool(self):
        """Test worker pool configuration."""
        from shared.celery_app.config import celery_app

        assert celery_app.conf.worker_pool == 'solo'
        assert celery_app.conf.worker_concurrency == 1

    def test_celery_config_serializer(self):
        """Test serializer configuration."""
        from shared.celery_app.config import celery_app

        assert celery_app.conf.task_serializer == 'json'
        assert celery_app.conf.result_serializer == 'json'
        assert 'json' in celery_app.conf.accept_content

    def test_celery_config_task_execution(self):
        """Test task execution configuration."""
        from shared.celery_app.config import celery_app

        assert celery_app.conf.task_acks_late is True
        assert celery_app.conf.task_reject_on_worker_lost is True
        assert celery_app.conf.task_track_started is True

    def test_celery_config_result_backend(self):
        """Test result backend configuration."""
        from shared.celery_app.config import celery_app

        assert celery_app.conf.result_expires == 86400

    def test_celery_config_broker(self):
        """Test broker configuration."""
        from shared.celery_app.config import celery_app

        assert celery_app.conf.broker_connection_retry_on_startup is True
        assert celery_app.conf.broker_connection_retry is True
        assert celery_app.conf.broker_connection_max_retries == 10


# ============================================================================
# Tests for shared.celery_app.worker
# ============================================================================

class TestCeleryWorkerThread:
    """Tests for CeleryWorkerThread class."""

    def test_init(self):
        """Test CeleryWorkerThread initialization."""
        from shared.celery_app.worker import CeleryWorkerThread

        worker_thread = CeleryWorkerThread()

        assert worker_thread.daemon is True
        assert worker_thread.name == 'CeleryWorker'
        assert worker_thread._stop_event is not None

    def test_stop(self, mock_celery_app):
        """Test stopping worker thread."""
        from shared.celery_app.worker import CeleryWorkerThread

        worker_thread = CeleryWorkerThread()

        with patch('shared.celery_app.worker.celery_app', mock_celery_app):
            worker_thread.stop()

            # Should set stop event
            assert worker_thread._stop_event.is_set()
            # Should call control.shutdown()
            mock_celery_app.control.shutdown.assert_called_once()

    def test_run_success(self, mock_celery_app):
        """Test successful worker run."""
        from shared.celery_app.worker import CeleryWorkerThread

        worker_thread = CeleryWorkerThread()

        with patch('shared.celery_app.worker.celery_app', mock_celery_app):
            # Mock worker_main to return immediately
            mock_celery_app.worker_main.return_value = None

            worker_thread.run()

            # Should call worker_main with correct args
            mock_celery_app.worker_main.assert_called_once()
            args = mock_celery_app.worker_main.call_args[1]['argv']
            assert 'worker' in args
            assert '--pool=solo' in args
            assert '--concurrency=1' in args

    def test_run_error(self, mock_celery_app, capsys):
        """Test worker run with error."""
        from shared.celery_app.worker import CeleryWorkerThread

        worker_thread = CeleryWorkerThread()

        with patch('shared.celery_app.worker.celery_app', mock_celery_app):
            # Mock worker_main to raise exception
            mock_celery_app.worker_main.side_effect = Exception("Test error")

            worker_thread.run()

            # Should handle error gracefully
            captured = capsys.readouterr()
            assert "Error en worker de Celery" in captured.out


class TestCeleryWorkerManagement:
    """Tests for worker management functions."""

    def test_start_celery_worker_thread(self, mock_celery_app):
        """Test starting worker thread."""
        from shared.celery_app import worker

        # Reset global state
        worker._celery_worker_thread = None

        with patch('shared.celery_app.worker.celery_app', mock_celery_app), \
             patch('shared.celery_app.worker.CeleryWorkerThread') as MockWorkerThread:

            mock_thread = MagicMock()
            mock_thread.is_alive.return_value = False
            MockWorkerThread.return_value = mock_thread

            result = worker.start_celery_worker_thread()

            # Should create and start thread
            MockWorkerThread.assert_called_once()
            mock_thread.start.assert_called_once()
            assert result == mock_thread

    def test_start_celery_worker_thread_already_running(self, mock_celery_app):
        """Test starting worker when already running."""
        from shared.celery_app import worker

        # Mock already running thread
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        worker._celery_worker_thread = mock_thread

        with patch('shared.celery_app.worker.celery_app', mock_celery_app):
            result = worker.start_celery_worker_thread()

            # Should return existing thread without creating new one
            assert result == mock_thread
            mock_thread.start.assert_not_called()

    def test_start_celery_worker_thread_error(self, mock_celery_app):
        """Test error starting worker thread."""
        from shared.celery_app import worker

        # Reset global state
        worker._celery_worker_thread = None

        with patch('shared.celery_app.worker.celery_app', mock_celery_app), \
             patch('shared.celery_app.worker.CeleryWorkerThread', side_effect=Exception("Test error")), \
             pytest.raises(Exception) as exc_info:

            worker.start_celery_worker_thread()

        assert "Test error" in str(exc_info.value)

    def test_stop_celery_worker_thread(self, mock_celery_app):
        """Test stopping worker thread."""
        from shared.celery_app import worker

        # Mock running thread - True initially, False after join
        mock_thread = MagicMock()
        mock_thread.is_alive.side_effect = [True, False]  # True on first check, False after join
        worker._celery_worker_thread = mock_thread

        with patch('shared.celery_app.worker.celery_app', mock_celery_app):
            result = worker.stop_celery_worker_thread()

            # Should stop and join thread
            mock_thread.stop.assert_called_once()
            mock_thread.join.assert_called_once_with(timeout=5)
            assert result is True
            assert worker._celery_worker_thread is None

    def test_stop_celery_worker_thread_not_running(self):
        """Test stopping worker when not running."""
        from shared.celery_app import worker

        # No thread
        worker._celery_worker_thread = None

        result = worker.stop_celery_worker_thread()

        assert result is False

    def test_stop_celery_worker_thread_timeout(self, mock_celery_app):
        """Test stopping worker with timeout."""
        from shared.celery_app import worker

        # Mock running thread that doesn't stop
        mock_thread = MagicMock()
        mock_thread.is_alive.side_effect = [True, True]  # Still alive after join
        worker._celery_worker_thread = mock_thread

        with patch('shared.celery_app.worker.celery_app', mock_celery_app):
            result = worker.stop_celery_worker_thread()

            # Should attempt to stop even with timeout
            mock_thread.stop.assert_called_once()
            assert result is True

    def test_stop_celery_worker_thread_error(self, mock_celery_app):
        """Test error stopping worker thread."""
        from shared.celery_app import worker

        # Mock thread that raises error on stop
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        mock_thread.stop.side_effect = Exception("Test error")
        worker._celery_worker_thread = mock_thread

        with patch('shared.celery_app.worker.celery_app', mock_celery_app):
            result = worker.stop_celery_worker_thread()

            # Should handle error and return False
            assert result is False

    def test_is_worker_running_true(self):
        """Test checking if worker is running (True)."""
        from shared.celery_app import worker

        # Mock running thread
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        worker._celery_worker_thread = mock_thread

        assert worker.is_worker_running() is True

    def test_is_worker_running_false_no_thread(self):
        """Test checking if worker is running (False - no thread)."""
        from shared.celery_app import worker

        worker._celery_worker_thread = None

        assert worker.is_worker_running() is False

    def test_is_worker_running_false_not_alive(self):
        """Test checking if worker is running (False - not alive)."""
        from shared.celery_app import worker

        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = False
        worker._celery_worker_thread = mock_thread

        assert worker.is_worker_running() is False


# ============================================================================
# Integration Tests
# ============================================================================

class TestCeleryIntegration:
    """Integration tests for Celery modules."""

    def test_worker_thread_lifecycle(self, mock_celery_app):
        """Test complete worker thread lifecycle."""
        from shared.celery_app import worker

        # Clean state
        worker._celery_worker_thread = None

        with patch('shared.celery_app.worker.celery_app', mock_celery_app), \
             patch('shared.celery_app.worker.CeleryWorkerThread') as MockWorkerThread:

            mock_thread = MagicMock()
            # Setup is_alive() to return appropriate values during lifecycle:
            # Note: is_worker_running() checks "is not None AND is_alive()"
            # Before start: _celery_worker_thread is None, no is_alive() call
            # 1. is_worker_running() after start -> True (1st call)
            # 2. stop_celery_worker_thread() initial check -> True (2nd call)
            # 3. stop_celery_worker_thread() after join check -> False (3rd call)
            # 4. is_worker_running() after stop -> False (4th call)
            mock_thread.is_alive.side_effect = [True, True, False, False]
            MockWorkerThread.return_value = mock_thread

            # Start worker
            assert worker.is_worker_running() is False

            started_thread = worker.start_celery_worker_thread()
            assert started_thread is not None
            assert worker.is_worker_running() is True

            # Stop worker
            result = worker.stop_celery_worker_thread()
            assert result is True
            assert worker.is_worker_running() is False
