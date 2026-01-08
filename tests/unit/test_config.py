"""
Unit tests for shared.config module (loader and cli).

Tests configuration loading, saving, CLI argument parsing, and tunnel commands.
"""
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, mock_open, patch, call

import pytest


# ============================================================================
# Tests for shared.config.loader
# ============================================================================

class TestConfigLoader:
    """Tests for configuration loading and persistence."""

    def test_get_resource_path_normal(self):
        """Test get_resource_path in normal (non-PyInstaller) mode."""
        from shared.config.loader import get_resource_path

        result = get_resource_path('config.json')
        expected = os.path.join(os.path.abspath("."), 'config.json')
        assert result == expected

    def test_get_resource_path_pyinstaller(self):
        """Test get_resource_path when running from PyInstaller bundle."""
        from shared.config.loader import get_resource_path

        # Mock PyInstaller's _MEIPASS by setting it as attribute
        sys._MEIPASS = '/tmp/pyinstaller'
        try:
            result = get_resource_path('config.json')
            expected = os.path.join('/tmp/pyinstaller', 'config.json')
            assert result == expected
        finally:
            # Clean up - remove the attribute
            delattr(sys, '_MEIPASS')

    def test_write_to_config_success(self, tmp_path):
        """Test successful configuration write."""
        from shared.config.loader import write_to_config, config_file

        test_config = {
            'url': 'https://test.example.com',
            'token': 'test_token',
            'machine_id': 'test_machine',
        }

        # Patch the config_file path to use temp directory
        with patch('shared.config.loader.config_file', tmp_path / 'config.json'):
            write_to_config(test_config)

            # Verify file was written correctly
            with open(tmp_path / 'config.json', 'r') as f:
                saved_data = json.load(f)

            assert saved_data == test_config

    def test_write_to_config_error(self, capsys):
        """Test error handling when config write fails."""
        from shared.config.loader import write_to_config

        # Mock open to raise an exception
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            write_to_config({'test': 'data'})

            # Check error was printed
            captured = capsys.readouterr()
            assert "Error al escribir en Config.json" in captured.out

    def test_get_config_data_existing_file(self, tmp_path):
        """Test loading config from existing file."""
        from shared.config.loader import get_config_data

        # Create test config file
        test_config = {
            'url': 'https://test.example.com',
            'token': 'test_token_123',
            'machine_id': 'test_machine_id',
            'license_key': 'test_license',
            'folder': '/tmp/robots',
            'ip': '192.168.1.100',
            'port': '5001',
            'tunnel_subdomain': 'test-robot',
            'tunnel_id': 'test-tunnel-id',
        }

        config_path = tmp_path / 'config.json'
        with open(config_path, 'w') as f:
            json.dump(test_config, f)

        # Patch config_file to use temp file
        with patch('shared.config.loader.config_file', config_path):
            result = get_config_data()

        # Verify all fields were loaded
        assert result['url'] == test_config['url']
        assert result['token'] == test_config['token']
        assert result['machine_id'] == test_config['machine_id']
        assert result['license_key'] == test_config['license_key']
        assert result['folder'] == test_config['folder']
        assert result['ip'] == test_config['ip']
        assert result['port'] == test_config['port']
        assert result['tunnel_subdomain'] == test_config['tunnel_subdomain']
        assert result['tunnel_id'] == test_config['tunnel_id']

    def test_get_config_data_missing_file(self, tmp_path):
        """Test config creation when file doesn't exist."""
        from shared.config.loader import get_config_data

        config_path = tmp_path / 'config.json'
        default_config_path = tmp_path / 'default_config.json'

        # Create default config
        default_config = {'url': 'https://default.com', 'token': None}
        with open(default_config_path, 'w') as f:
            json.dump(default_config, f)

        with patch('shared.config.loader.config_file', config_path), \
             patch('shared.config.loader.get_resource_path', return_value=str(default_config_path)):

            result = get_config_data()

            # Verify config file was created
            assert config_path.exists()
            assert 'url' in result

    def test_get_config_data_defaults(self, tmp_path):
        """Test default values when keys are missing."""
        from shared.config.loader import get_config_data, user_dir

        # Create minimal config
        minimal_config = {}
        config_path = tmp_path / 'config.json'

        with open(config_path, 'w') as f:
            json.dump(minimal_config, f)

        with patch('shared.config.loader.config_file', config_path), \
             patch('os.popen') as mock_popen:

            # Mock IP detection
            mock_popen.return_value.readline.return_value = '203.0.113.1'

            result = get_config_data()

            # Check defaults
            assert result['url'] == "https://robot-console-a73e07ff7a0d.herokuapp.com/"
            assert result['token'] is None
            assert result['machine_id'] is None
            assert result['license_key'] is None
            assert result['port'] == "8088"
            assert result['tunnel_subdomain'] == ''
            assert result['tunnel_id'] == '3d7de42c-4a8a-4447-b14f-053cc485ce6b'

    def test_save_config_data_alias(self):
        """Test that save_config_data is an alias for write_to_config."""
        from shared.config.loader import save_config_data, write_to_config

        assert save_config_data == write_to_config


# ============================================================================
# Tests for shared.config.cli
# ============================================================================

class TestConfigCLI:
    """Tests for CLI argument parsing and commands."""

    def test_has_cli_args_with_args(self):
        """Test has_cli_args returns True when args provided."""
        from shared.config.cli import has_cli_args

        mock_args = MagicMock()
        mock_args.url = 'https://test.com'
        mock_args.token = None
        mock_args.machine_id = None

        assert has_cli_args(mock_args) is True

    def test_has_cli_args_without_args(self):
        """Test has_cli_args returns False when no args provided."""
        from shared.config.cli import has_cli_args

        mock_args = MagicMock()
        # Set all config args to None
        for arg in ['url', 'token', 'machine_id', 'license_key', 'folder', 'ip', 'port', 'tunnel_subdomain', 'tunnel_id']:
            setattr(mock_args, arg, None)

        assert has_cli_args(mock_args) is False

    def test_get_args_show_config_exits(self):
        """Test that --show-config calls show_config and exits."""
        from shared.config.cli import get_args

        mock_parser = MagicMock()
        mock_args = MagicMock()
        mock_args.show_config = True
        mock_parser.parse_args.return_value = mock_args

        config = {'url': 'https://test.com'}

        with patch('shared.config.cli.show_config') as mock_show, \
             pytest.raises(SystemExit) as exc_info:

            get_args(mock_parser, config)

            mock_show.assert_called_once_with(config)
            assert exc_info.value.code == 0

    def test_get_args_merge_cli_values(self):
        """Test that CLI arguments are merged into config."""
        from shared.config.cli import get_args

        mock_parser = MagicMock()
        mock_args = MagicMock()

        # Set special commands to False
        mock_args.show_config = False
        mock_args.tunnel_status = False
        mock_args.start_tunnel = False
        mock_args.stop_tunnel = False
        mock_args.setup_tunnel = False

        # Set CLI values
        mock_args.url = 'https://new-url.com'
        mock_args.token = 'new_token'
        mock_args.machine_id = 'new_machine'
        mock_args.license_key = None
        mock_args.folder = None
        mock_args.ip = None
        mock_args.port = 9000
        mock_args.tunnel_subdomain = None
        mock_args.tunnel_id = None

        mock_args.save = False
        mock_args.no_save = False

        mock_parser.parse_args.return_value = mock_args

        config = {
            'url': 'https://old-url.com',
            'token': 'old_token',
            'machine_id': 'old_machine',
            'license_key': 'old_license',
            'folder': '/old/folder',
            'ip': '127.0.0.1',
            'port': '8088',
            'tunnel_subdomain': '',
            'tunnel_id': 'old_tunnel_id',
        }

        result = get_args(mock_parser, config)

        # Check merged values
        assert result['url'] == 'https://new-url.com'
        assert result['token'] == 'new_token'
        assert result['machine_id'] == 'new_machine'
        assert result['port'] == '9000'
        assert result['license_key'] == 'old_license'  # Not changed
        assert result['_should_save'] is True  # Has CLI args

    def test_get_args_save_flag(self):
        """Test _should_save flag behavior."""
        from shared.config.cli import get_args

        mock_parser = MagicMock()
        mock_args = MagicMock()

        # Disable special commands
        for cmd in ['show_config', 'tunnel_status', 'start_tunnel', 'stop_tunnel', 'setup_tunnel']:
            setattr(mock_args, cmd, False)

        # Set all config args to None
        for arg in ['url', 'token', 'machine_id', 'license_key', 'folder', 'ip', 'port', 'tunnel_subdomain', 'tunnel_id']:
            setattr(mock_args, arg, None)

        mock_parser.parse_args.return_value = mock_args
        config = {'url': 'https://test.com', 'token': 'test'}

        # Test 1: --save flag
        mock_args.save = True
        mock_args.no_save = False
        result = get_args(mock_parser, config)
        assert result['_should_save'] is True

        # Test 2: --no-save flag
        mock_args.save = False
        mock_args.no_save = True
        result = get_args(mock_parser, config)
        assert result['_should_save'] is False

        # Test 3: No flags, no CLI args
        mock_args.save = False
        mock_args.no_save = False
        result = get_args(mock_parser, config)
        assert result['_should_save'] is False

    def test_show_config_display(self, capsys):
        """Test show_config displays configuration correctly."""
        from shared.config.cli import show_config

        config = {
            'url': 'https://test.example.com',
            'ip': '192.168.1.100',
            'port': '5001',
            'token': 'secret_token_123',
            'machine_id': 'test_machine',
            'license_key': 'secret_license_key',
            'folder': '/tmp/robots',
            'tunnel_subdomain': 'test-robot',
            'tunnel_id': 'test-tunnel-id',
        }

        show_config(config)

        captured = capsys.readouterr()
        output = captured.out

        # Check key information is displayed
        assert 'Configuración Actual de Robot Runner' in output
        assert 'https://test.example.com' in output
        assert '192.168.1.100' in output
        assert '5001' in output
        assert 'test_machine' in output
        assert '/tmp/robots' in output
        assert 'test-robot.automatehub.es' in output

        # Check sensitive data is masked
        assert 'secret_token_123' not in output
        assert 'secret_license_key' not in output
        assert '***' in output  # Masked tokens

    def test_check_tunnel_status_active(self, capsys):
        """Test check_tunnel_status with active tunnel."""
        from shared.config.cli import check_tunnel_status

        with patch('subprocess.run') as mock_run, \
             patch('shared.config.cli.get_config_data') as mock_get_config:

            # Mock active tunnel
            mock_run.return_value = MagicMock(
                stdout='12345\n67890\n',
                returncode=0
            )

            mock_get_config.return_value = {
                'machine_id': 'test_machine',
                'tunnel_subdomain': 'test-robot'
            }

            check_tunnel_status()

            captured = capsys.readouterr()
            output = captured.out

            assert 'Túnel ACTIVO' in output
            assert '12345' in output
            assert 'test-robot.automatehub.es' in output

    def test_check_tunnel_status_inactive(self, capsys):
        """Test check_tunnel_status with inactive tunnel."""
        from shared.config.cli import check_tunnel_status

        with patch('subprocess.run') as mock_run:
            # Mock inactive tunnel
            mock_run.return_value = MagicMock(
                stdout='',
                returncode=1
            )

            check_tunnel_status()

            captured = capsys.readouterr()
            output = captured.out

            assert 'Túnel INACTIVO' in output
            assert '--start-tunnel' in output

    def test_start_tunnel_cli_not_installed(self, capsys):
        """Test start_tunnel_cli when cloudflared not installed."""
        from shared.config.cli import start_tunnel_cli

        with patch('shutil.which', return_value=None):
            start_tunnel_cli()

            captured = capsys.readouterr()
            output = captured.out

            assert 'cloudflared no está instalado' in output
            assert 'brew install cloudflared' in output

    def test_start_tunnel_cli_no_config(self, capsys, tmp_path):
        """Test start_tunnel_cli when config doesn't exist."""
        from shared.config.cli import start_tunnel_cli

        with patch('shutil.which', return_value='/usr/bin/cloudflared'), \
             patch('pathlib.Path.home', return_value=tmp_path):

            start_tunnel_cli()

            captured = capsys.readouterr()
            output = captured.out

            assert 'Configuración de túnel no encontrada' in output
            assert '--setup-tunnel' in output

    def test_stop_tunnel_cli_no_tunnel(self, capsys):
        """Test stop_tunnel_cli when no tunnel is running."""
        from shared.config.cli import stop_tunnel_cli

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout='', returncode=1)

            stop_tunnel_cli()

            captured = capsys.readouterr()
            output = captured.out

            assert 'No hay túneles activos' in output

    def test_setup_tunnel_cli_no_cloudflared(self, capsys):
        """Test setup_tunnel_cli when cloudflared not installed."""
        from shared.config.cli import setup_tunnel_cli

        config = {'machine_id': 'test_machine'}

        with patch('shutil.which', return_value=None):
            setup_tunnel_cli(config)

            captured = capsys.readouterr()
            output = captured.out

            assert 'cloudflared no está instalado' in output

    def test_setup_tunnel_cli_no_machine_id(self, capsys):
        """Test setup_tunnel_cli when machine_id missing."""
        from shared.config.cli import setup_tunnel_cli

        config = {'machine_id': None}

        with patch('shutil.which', return_value='/usr/bin/cloudflared'):
            setup_tunnel_cli(config)

            captured = capsys.readouterr()
            output = captured.out

            assert 'machine_id no configurado' in output

    def test_setup_tunnel_cli_success(self, capsys, tmp_path):
        """Test successful tunnel setup."""
        from shared.config.cli import setup_tunnel_cli

        config = {
            'machine_id': 'test_machine',
            'tunnel_id': 'test-tunnel-id',
            'tunnel_subdomain': 'test-robot',
            'port': '5001'
        }

        with patch('shutil.which', return_value='/usr/bin/cloudflared'), \
             patch('pathlib.Path.home', return_value=tmp_path), \
             patch('subprocess.run') as mock_run:

            # Mock successful DNS setup
            mock_run.return_value = MagicMock(returncode=0, stderr='')

            setup_tunnel_cli(config)

            captured = capsys.readouterr()
            output = captured.out

            assert 'Configuración completa' in output
            assert 'test-robot.automatehub.es' in output

            # Check config file was created
            config_file = tmp_path / '.cloudflared' / 'config.yml'
            assert config_file.exists()

            # Verify config content
            config_content = config_file.read_text()
            assert 'test-tunnel-id' in config_content
            assert 'test-robot.automatehub.es' in config_content
            assert '5001' in config_content
