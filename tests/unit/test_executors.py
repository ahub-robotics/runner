"""
Unit tests for executors module.

Tests Runner, Server, and execution tasks.
"""
import time
from unittest.mock import MagicMock, Mock, patch, call

import pytest


# ============================================================================
# Tests for executors.runner
# ============================================================================

class TestRunner:
    """Tests for Runner class."""

    def test_runner_init(self):
        """Test Runner initialization."""
        from executors.runner import Runner

        runner = Runner(
            url="https://test.example.com",
            machine_id="test_machine",
            license_key="test_license",
            folder="/tmp/robots",
            token="test_token",
            port=5001
        )

        assert runner.url == "test.example.com"  # URL is cleaned
        assert runner.machine_id == "test_machine"
        assert runner.license_key == "test_license"
        assert runner.folder == "/tmp/robots"
        assert runner.token == "test_token"
        assert runner.port == 5001
        assert runner.robot_id is None
        assert runner.execution_id is None

    def test_clean_url_https(self):
        """Test URL cleaning with HTTPS."""
        from executors.runner import Runner

        cleaned = Runner.clean_url("https://example.com/")
        assert cleaned == "example.com"

    def test_clean_url_http(self):
        """Test URL cleaning with HTTP."""
        from executors.runner import Runner

        cleaned = Runner.clean_url("http://example.com/")
        assert cleaned == "example.com"

    def test_clean_url_trailing_slash(self):
        """Test URL cleaning with trailing slash."""
        from executors.runner import Runner

        cleaned = Runner.clean_url("example.com/")
        assert cleaned == "example.com"

    def test_set_robot_folder(self):
        """Test setting robot folder."""
        from executors.runner import Runner

        runner = Runner(
            url="https://test.com",
            machine_id="test",
            folder="/tmp/robots",
            token="test"
        )
        runner.robot_id = "robot123"
        runner.set_robot_folder()

        assert runner.robot_folder == "/tmp/robots/robot123"


class TestRobot:
    """Tests for Robot class."""

    def test_robot_init_with_git(self):
        """Test Robot initialization with .git in URL."""
        from executors.runner import Robot

        robot = Robot({
            'repo_url': 'https://github.com/user/repo.git',
            'RobotId': 'robot123',
            'Name': 'Test Robot'
        })

        assert robot.repoUrl == 'https://github.com/user/repo.git'
        assert robot.RobotId == 'robot123'
        assert robot.RobotName == 'Test Robot'

    def test_robot_init_without_git(self):
        """Test Robot initialization without .git in URL."""
        from executors.runner import Robot

        robot = Robot({
            'repo_url': 'https://github.com/user/repo',
            'RobotId': 'robot123',
            'Name': 'Test Robot'
        })

        assert robot.repoUrl == 'https://github.com/user/repo.git'
        assert robot.RobotId == 'robot123'


# ============================================================================
# Tests for executors.server
# ============================================================================

class TestServer:
    """Tests for Server class."""

    def test_server_init(self, mock_redis):
        """Test Server initialization."""
        from executors.server import Server

        config = {
            'url': 'https://test.com',
            'machine_id': 'test_machine',
            'token': 'test_token',
            'folder': '/tmp/robots',
            'license_key': 'test_license',
            'port': 5001
        }

        with patch('shared.state.redis_state.redis_state') as mock_redis_state:
            server = Server(config)

            assert server.machine_id == 'test_machine'
            assert server.status == 'free'
            assert server.execution_id is None
            assert server.last_exit_code is None
            mock_redis_state.set_machine_id.assert_called_once_with('test_machine')

    def test_change_status_to_running(self, mock_redis):
        """Test changing status to running."""
        from executors.server import Server

        config = {
            'url': 'https://test.com',
            'machine_id': 'test_machine',
            'token': 'test_token',
            'folder': '/tmp/robots',
            'port': 5001
        }

        with patch('shared.state.redis_state.redis_state') as mock_redis_state, \
             patch.object(Server, 'set_machine_ip'):

            server = Server(config)
            server.change_status('running', notify_remote=False, execution_id='exec123')

            assert server.status == 'running'
            assert server.execution_id == 'exec123'
            assert server.last_exit_code is None
            mock_redis_state.set_server_status.assert_called_with('running')

    def test_change_status_to_free(self, mock_redis):
        """Test changing status to free."""
        from executors.server import Server

        config = {
            'url': 'https://test.com',
            'machine_id': 'test_machine',
            'token': 'test_token',
            'folder': '/tmp/robots',
            'port': 5001
        }

        with patch('shared.state.redis_state.redis_state') as mock_redis_state, \
             patch.object(Server, 'set_machine_ip'):

            server = Server(config)
            server.status = 'running'
            server.execution_id = 'exec123'
            server.change_status('free', notify_remote=False)

            assert server.status == 'free'
            mock_redis_state.set_server_status.assert_called_with('free')

    def test_get_status(self):
        """Test getting server status."""
        from executors.server import Server

        config = {
            'url': 'https://test.com',
            'machine_id': 'test_machine',
            'token': 'test_token',
            'folder': '/tmp/robots',
            'port': 5001
        }

        with patch('shared.state.redis_state.redis_state'):
            server = Server(config)
            server.status = 'running'

            assert server.get_status() == 'running'

    def test_set_execution_result(self):
        """Test setting execution result."""
        from executors.server import Server

        config = {
            'url': 'https://test.com',
            'machine_id': 'test_machine',
            'token': 'test_token',
            'folder': '/tmp/robots',
            'port': 5001
        }

        with patch('shared.state.redis_state.redis_state'):
            server = Server(config)
            server.set_execution_result(0)

            assert server.last_exit_code == 0


# ============================================================================
# Tests for executors.tasks
# ============================================================================

class TestExecutorTasks:
    """Tests for Celery tasks."""

    def test_run_robot_task_success(self, mock_redis):
        """Test successful robot execution task."""
        from executors.tasks import run_robot_task

        data = {
            'execution_id': 'exec123',
            'robot': {'RobotId': 'robot1', 'Name': 'Test'},
            'params': {}
        }

        with patch('shared.state.redis_state.redis_state') as mock_redis_state, \
             patch('executors.tasks.get_config_data') as mock_config, \
             patch('executors.tasks.Server') as MockServer:

            mock_config.return_value = {
                'url': 'https://test.com',
                'machine_id': 'test',
                'token': 'test'
            }

            mock_server = MagicMock()
            mock_server.last_exit_code = 0
            MockServer.return_value = mock_server

            mock_redis_state.load_execution_state.return_value = {}

            # Call the task's run method directly (bypassing Celery decorator)
            result = run_robot_task.run(data)

            assert result['execution_id'] == 'exec123'
            assert result['exit_code'] == 0
            assert result['status'] == 'completed'
            mock_server.run.assert_called_once_with(data)

    def test_run_robot_task_failure(self, mock_redis):
        """Test failed robot execution task."""
        from executors.tasks import run_robot_task

        data = {
            'execution_id': 'exec123',
            'robot': {'RobotId': 'robot1', 'Name': 'Test'},
            'params': {}
        }

        with patch('shared.state.redis_state.redis_state') as mock_redis_state, \
             patch('executors.tasks.get_config_data') as mock_config, \
             patch('executors.tasks.Server') as MockServer:

            mock_config.return_value = {'url': 'https://test.com', 'machine_id': 'test', 'token': 'test'}
            mock_server = MagicMock()
            mock_server.last_exit_code = 1
            MockServer.return_value = mock_server
            mock_redis_state.load_execution_state.return_value = {}

            # Call the task's run method directly (bypassing Celery decorator)
            result = run_robot_task.run(data)

            assert result['exit_code'] == 1
            assert result['status'] == 'failed'

    def test_cleanup_old_executions(self, mock_redis):
        """Test cleanup of old executions."""
        from executors.tasks import cleanup_old_executions

        with patch('shared.state.redis_state.redis_state') as mock_redis_state:
            mock_client = MagicMock()
            mock_client.keys.return_value = [
                b'execution:old_exec1',
                b'execution:old_exec2'
            ]

            # Mock old execution
            mock_client.hgetall.return_value = {
                b'status': b'completed',
                b'finished_at': b'1000000.0'  # Very old timestamp
            }

            mock_redis_state._get_redis_client.return_value = mock_client

            with patch('time.time', return_value=2000000000.0):  # Much later
                result = cleanup_old_executions(max_age_hours=24)

            assert result['deleted_count'] == 2
            assert result['checked_count'] == 2
            assert mock_client.delete.call_count == 4  # 2 executions + 2 pause_control


# ============================================================================
# Integration Tests
# ============================================================================

class TestExecutorsIntegration:
    """Integration tests for executors."""

    def test_server_inherits_from_runner(self):
        """Test that Server inherits from Runner."""
        from executors.server import Server
        from executors.runner import Runner

        config = {
            'url': 'https://test.com',
            'machine_id': 'test',
            'token': 'test',
            'folder': '/tmp'
        }

        with patch('shared.state.redis_state.redis_state'):
            server = Server(config)
            assert isinstance(server, Runner)

    def test_imports_work(self):
        """Test that all imports work correctly."""
        from executors import Robot, Runner, Server
        from executors import tasks

        assert Robot is not None
        assert Runner is not None
        assert Server is not None
        assert tasks is not None
