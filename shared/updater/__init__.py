"""
Auto-updater module for Robot Runner

Provides automatic update functionality for compiled binaries.
"""

from .auto_updater import AutoUpdater
from .version import Version, get_current_version
from .checksum import verify_checksum
from .backup import BackupManager

__all__ = [
    'AutoUpdater',
    'Version',
    'get_current_version',
    'verify_checksum',
    'BackupManager',
]