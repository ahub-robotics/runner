"""
Backup and rollback management for updates
"""

import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
from .version import Version


class BackupManager:
    """Manages backups of executables before updates"""

    def __init__(self, backup_dir: Optional[Path] = None):
        """
        Initialize backup manager

        Args:
            backup_dir: Directory to store backups (default: ~/Robot/backups)
        """
        if backup_dir is None:
            backup_dir = Path.home() / "Robot" / "backups"

        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Metadata file
        self.metadata_file = self.backup_dir / "backups.json"

    def create_backup(
        self,
        executable_path: Path,
        version: Version
    ) -> Optional[Path]:
        """
        Create backup of current executable

        Args:
            executable_path: Path to executable to backup
            version: Version of the executable

        Returns:
            Path to backup directory, or None if backup failed
        """
        if not executable_path.exists():
            print(f"❌ Executable not found: {executable_path}")
            return None

        # Create timestamped backup directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{version}_{timestamp}"
        backup_path = self.backup_dir / backup_name

        try:
            backup_path.mkdir(parents=True, exist_ok=True)

            # Copy executable
            backup_exe = backup_path / executable_path.name
            shutil.copy2(executable_path, backup_exe)

            # Save metadata
            self._save_backup_metadata(backup_path, version, executable_path)

            print(f"✅ Backup created: {backup_path}")
            return backup_path

        except Exception as e:
            print(f"❌ Failed to create backup: {e}")
            # Clean up partial backup
            if backup_path.exists():
                shutil.rmtree(backup_path)
            return None

    def restore_backup(
        self,
        backup_path: Path,
        target_path: Path
    ) -> bool:
        """
        Restore executable from backup

        Args:
            backup_path: Path to backup directory
            target_path: Where to restore the executable

        Returns:
            True if restore successful, False otherwise
        """
        if not backup_path.exists():
            print(f"❌ Backup not found: {backup_path}")
            return False

        try:
            # Find executable in backup
            backup_files = list(backup_path.glob("RobotRunner*"))
            if not backup_files:
                print(f"❌ No executable found in backup: {backup_path}")
                return False

            backup_exe = backup_files[0]

            # Restore executable
            shutil.copy2(backup_exe, target_path)

            print(f"✅ Restored from backup: {backup_path}")
            return True

        except Exception as e:
            print(f"❌ Failed to restore backup: {e}")
            return False

    def get_latest_backup(self) -> Optional[Path]:
        """
        Get path to most recent backup

        Returns:
            Path to latest backup directory, or None if no backups exist
        """
        backups = sorted(
            self.backup_dir.glob("backup_*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        return backups[0] if backups else None

    def list_backups(self) -> List[Dict]:
        """
        List all available backups

        Returns:
            List of backup info dictionaries
        """
        backups = []

        for backup_path in sorted(self.backup_dir.glob("backup_*"), reverse=True):
            metadata_file = backup_path / "metadata.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        metadata['path'] = str(backup_path)
                        backups.append(metadata)
                except:
                    pass

        return backups

    def cleanup_old_backups(self, keep_count: int = 5):
        """
        Remove old backups, keeping only the most recent ones

        Args:
            keep_count: Number of backups to keep (default: 5)
        """
        backups = sorted(
            self.backup_dir.glob("backup_*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        # Remove old backups
        for backup_path in backups[keep_count:]:
            try:
                shutil.rmtree(backup_path)
                print(f"🗑️  Removed old backup: {backup_path.name}")
            except Exception as e:
                print(f"⚠️  Failed to remove backup {backup_path.name}: {e}")

    def _save_backup_metadata(
        self,
        backup_path: Path,
        version: Version,
        executable_path: Path
    ):
        """Save metadata about the backup"""
        metadata = {
            "version": str(version),
            "timestamp": datetime.now().isoformat(),
            "executable_name": executable_path.name,
            "executable_size": executable_path.stat().st_size,
        }

        metadata_file = backup_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)