"""
Configuration loader and persistence module.

This module handles loading and saving application configuration from/to disk.
Configuration is stored in ~/Robot/config.json and includes all robot connection
and authentication settings.
"""
import json
import os
import shutil
import sys
from pathlib import Path

# Global configuration paths
user_dir = Path.home() / 'Robot'
user_dir.mkdir(exist_ok=True)
config_file = user_dir / 'config.json'


def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for PyInstaller bundled apps.

    When running from PyInstaller bundle, uses _MEIPASS temporary folder.
    Otherwise uses current working directory.

    Args:
        relative_path: Path relative to application root

    Returns:
        str: Absolute path to resource
    """
    # Check if we're running from PyInstaller bundle
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def write_to_config(config_data):
    """
    Write configuration data to config file.

    Saves configuration dictionary to ~/Robot/config.json with proper formatting.

    Args:
        config_data: Dictionary with configuration keys/values

    Raises:
        Exception: If file write fails
    """
    try:
        with open(config_file, "w") as file:
            json.dump(config_data, file, indent=4)
    except Exception as e:
        print("Error al escribir en Config.json:", e)


def get_config_data():
    """
    Load configuration data from config file.

    If config file doesn't exist, copies default config.json from application
    resources. Returns dictionary with all configuration values.

    Default values:
        - url: https://robot-console-a73e07ff7a0d.herokuapp.com/
        - token: None
        - machine_id: None
        - license_key: None
        - folder: ~/Robot/Robots
        - ip: Auto-detected via ifconfig.me
        - port: 8088
        - tunnel_subdomain: Empty string
        - tunnel_id: 3d7de42c-4a8a-4447-b14f-053cc485ce6b

    Returns:
        dict: Configuration dictionary with all settings
    """
    kwargs = {}

    # Create config file from template if it doesn't exist
    if not os.path.isfile(config_file):
        shutil.copyfile(get_resource_path('config.json'), config_file)

    file = open(config_file, 'r')
    data = file.read()

    if data:
        json_data = json.loads(data)
        kwargs['url'] = json_data.get('url', "https://robot-console-a73e07ff7a0d.herokuapp.com/")
        kwargs['token'] = json_data.get('token', None)
        kwargs['machine_id'] = json_data.get('machine_id', None)
        kwargs['license_key'] = json_data.get('license_key', None)
        kwargs['folder'] = json_data.get('folder', f"{user_dir}/Robots")
        kwargs['ip'] = json_data.get('ip', os.popen('curl -s ifconfig.me').readline())
        kwargs['port'] = json_data.get('port', "8088")
        kwargs['tunnel_subdomain'] = json_data.get('tunnel_subdomain', '')
        kwargs['tunnel_id'] = json_data.get('tunnel_id', '3d7de42c-4a8a-4447-b14f-053cc485ce6b')

    return kwargs


# Alias for backward compatibility with existing code
save_config_data = write_to_config
