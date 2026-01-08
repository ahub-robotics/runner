"""
Unit tests for shared.utils.process module.

Tests process management utilities for finding and killing Gunicorn processes.
"""
import pytest
import platform
from unittest.mock import MagicMock, patch, call
import subprocess


class TestFindGunicornProcesses:
    """Tests for find_gunicorn_processes function."""

    @pytest.mark.skipif(platform.system() == 'Windows', reason="Unix-specific test")
    def test_find_gunicorn_processes_linux(self):
        """Test finding Gunicorn processes on Linux/macOS."""
        from shared.utils.process import find_gunicorn_processes

        # Mock pgrep returning PIDs
        mock_result = MagicMock()
        mock_result.stdout = "12345\n67890\n"

        with patch('subprocess.run', return_value=mock_result):
            pids = find_gunicorn_processes()

            assert len(pids) > 0
            assert all(isinstance(pid, int) for pid in pids)

    @pytest.mark.skipif(platform.system() == 'Windows', reason="Unix-specific test")
    def test_find_gunicorn_processes_empty(self):
        """Test when no Gunicorn processes are found."""
        from shared.utils.process import find_gunicorn_processes

        mock_result = MagicMock()
        mock_result.stdout = ""

        with patch('subprocess.run', return_value=mock_result):
            pids = find_gunicorn_processes()
            assert pids == []

    @pytest.mark.skipif(platform.system() == 'Windows', reason="Unix-specific test")
    def test_find_gunicorn_processes_by_port(self):
        """Test finding processes by listening port."""
        from shared.utils.process import find_gunicorn_processes

        # Mock lsof returning PIDs
        mock_result = MagicMock()
        mock_result.stdout = "12345\n"

        with patch('subprocess.run') as mock_run:
            # First call (pgrep) returns empty
            # Second call (lsof for port 5001) returns PID
            mock_run.side_effect = [
                MagicMock(stdout=""),  # pgrep gunicorn
                MagicMock(stdout=""),  # pgrep run.py
                MagicMock(stdout=""),  # pgrep cli.run_server
                MagicMock(stdout=""),  # pgrep api.wsgi
                MagicMock(stdout="12345\n"),  # lsof port 5001
                MagicMock(stdout=""),  # lsof port 5055
            ]

            pids = find_gunicorn_processes()
            assert 12345 in pids

    def test_find_gunicorn_processes_handles_timeout(self):
        """Test graceful handling of subprocess timeout."""
        from shared.utils.process import find_gunicorn_processes

        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('cmd', 10)):
            pids = find_gunicorn_processes()
            assert pids == []

    def test_find_gunicorn_processes_handles_errors(self):
        """Test graceful handling of other exceptions."""
        from shared.utils.process import find_gunicorn_processes

        with patch('subprocess.run', side_effect=Exception("Unknown error")):
            pids = find_gunicorn_processes()
            assert pids == []


class TestKillProcess:
    """Tests for kill_process function."""

    @pytest.mark.skipif(platform.system() == 'Windows', reason="Unix-specific test")
    def test_kill_process_sigterm(self):
        """Test killing process with SIGTERM."""
        from shared.utils.process import kill_process
        import signal

        with patch('os.kill') as mock_kill:
            result = kill_process(12345, force=False)

            mock_kill.assert_called_once_with(12345, signal.SIGTERM)
            assert result is True

    @pytest.mark.skipif(platform.system() == 'Windows', reason="Unix-specific test")
    def test_kill_process_sigkill(self):
        """Test killing process with SIGKILL."""
        from shared.utils.process import kill_process
        import signal

        with patch('os.kill') as mock_kill:
            result = kill_process(12345, force=True)

            mock_kill.assert_called_once_with(12345, signal.SIGKILL)
            assert result is True

    @pytest.mark.skipif(platform.system() == 'Windows', reason="Unix-specific test")
    def test_kill_process_already_dead(self):
        """Test killing process that doesn't exist."""
        from shared.utils.process import kill_process

        with patch('os.kill', side_effect=ProcessLookupError()):
            result = kill_process(99999, force=False)
            # Should return True (process is gone, which is the goal)
            assert result is True

    @pytest.mark.skipif(platform.system() == 'Windows', reason="Unix-specific test")
    def test_kill_process_permission_denied(self):
        """Test killing process without permissions."""
        from shared.utils.process import kill_process

        with patch('os.kill', side_effect=PermissionError()):
            result = kill_process(1, force=False)  # PID 1 usually requires root
            # Should return True (can't kill, but that's expected)
            assert result is True

    @pytest.mark.skipif(platform.system() != 'Windows', reason="Windows-specific test")
    def test_kill_process_windows(self):
        """Test killing process on Windows."""
        from shared.utils.process import kill_process

        mock_result = MagicMock()
        with patch('subprocess.run', return_value=mock_result) as mock_run:
            result = kill_process(12345, force=False)

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert 'taskkill' in call_args
            assert '12345' in call_args
            assert result is True

    @pytest.mark.skipif(platform.system() != 'Windows', reason="Windows-specific test")
    def test_kill_process_windows_force(self):
        """Test force killing process on Windows."""
        from shared.utils.process import kill_process

        mock_result = MagicMock()
        with patch('subprocess.run', return_value=mock_result) as mock_run:
            result = kill_process(12345, force=True)

            call_args = mock_run.call_args[0][0]
            assert '/F' in call_args  # Force flag
            assert result is True

    def test_kill_process_timeout(self):
        """Test handling of subprocess timeout."""
        from shared.utils.process import kill_process

        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('cmd', 5)):
            result = kill_process(12345, force=False)
            assert result is False
