"""
Auto-updater client for Robot Runner

Checks for new releases on GitHub and updates automatically.
"""

import os
import sys
import time
import requests
import tempfile
import platform
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

from .version import Version, get_current_version, save_current_version
from .checksum import verify_with_checksum_file, calculate_sha256
from .backup import BackupManager


class AutoUpdater:
    """Auto-updater client for Robot Runner"""

    def __init__(
        self,
        github_repo: str = "tu-usuario/robotrunner_windows",
        check_interval: int = 3600,
        auto_update: bool = True,
        update_channel: str = "stable"
    ):
        """
        Initialize auto-updater

        Args:
            github_repo: GitHub repository in format 'owner/repo'
            check_interval: Seconds between update checks (default: 3600 = 1 hour)
            auto_update: Enable automatic updates (default: True)
            update_channel: 'stable', 'beta', or 'canary' (default: 'stable')
        """
        self.github_repo = github_repo
        self.check_interval = check_interval
        self.auto_update = auto_update
        self.update_channel = update_channel

        self.api_base = f"https://api.github.com/repos/{github_repo}"
        self.backup_manager = BackupManager()

        # Detect platform
        self.platform = self._get_platform()
        self.executable_name = self._get_executable_name()

    def _get_platform(self) -> str:
        """Get current platform identifier"""
        system = platform.system().lower()

        if system == "windows":
            return "Windows"
        elif system == "linux":
            return "Linux"
        elif system == "darwin":
            return "macOS"
        else:
            raise RuntimeError(f"Unsupported platform: {system}")

    def _get_executable_name(self) -> str:
        """Get executable name for current platform"""
        if self.platform == "Windows":
            return "RobotRunner.exe"
        else:
            return "RobotRunner"

    def check_for_updates(self) -> Optional[Dict]:
        """
        Check if new version is available

        Returns:
            Dictionary with update info if available, None otherwise
            {
                'version': Version object,
                'download_url': str,
                'checksum_url': str,
                'release_notes': str
            }
        """
        try:
            # Get latest release from GitHub
            response = requests.get(
                f"{self.api_base}/releases/latest",
                timeout=10
            )
            response.raise_for_status()
            release_data = response.json()

            # Parse version
            latest_version = Version.from_string(release_data['tag_name'])
            current_version = get_current_version()

            # Check if update is available
            if latest_version <= current_version:
                return None

            # Filter by channel
            if not self._matches_channel(latest_version):
                return None

            # Find asset for current platform
            asset_name = f"RobotRunner-{self.platform}-x64"
            if self.platform == "Windows":
                asset_name += ".exe"

            download_url = None
            checksum_url = None

            for asset in release_data['assets']:
                if asset['name'] == asset_name:
                    download_url = asset['browser_download_url']
                elif asset['name'] == f"{asset_name}.sha256":
                    checksum_url = asset['browser_download_url']

            if not download_url or not checksum_url:
                print(f"⚠️  No assets found for {self.platform}")
                return None

            return {
                'version': latest_version,
                'download_url': download_url,
                'checksum_url': checksum_url,
                'release_notes': release_data.get('body', '')
            }

        except requests.RequestException as e:
            print(f"⚠️  Failed to check for updates: {e}")
            return None
        except Exception as e:
            print(f"❌ Error checking for updates: {e}")
            return None

    def _matches_channel(self, version: Version) -> bool:
        """Check if version matches update channel"""
        if self.update_channel == "stable":
            # Stable channel: no prerelease
            return not version.prerelease

        elif self.update_channel == "beta":
            # Beta channel: stable + beta
            return not version.prerelease or "beta" in version.prerelease

        elif self.update_channel == "canary":
            # Canary channel: all versions
            return True

        return False

    def download_update(self, update_info: Dict, temp_dir: Path) -> Optional[Path]:
        """
        Download update binary and checksum

        Args:
            update_info: Update info from check_for_updates()
            temp_dir: Temporary directory for downloads

        Returns:
            Path to downloaded file if successful, None otherwise
        """
        try:
            # Download binary
            print(f"📥 Downloading {update_info['version']}...")
            binary_path = temp_dir / self.executable_name

            response = requests.get(update_info['download_url'], stream=True, timeout=300)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(binary_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        # Progress indicator
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r   Progress: {progress:.1f}%", end='', flush=True)

            print()  # New line after progress

            # Download checksum
            checksum_path = temp_dir / f"{self.executable_name}.sha256"
            response = requests.get(update_info['checksum_url'], timeout=10)
            response.raise_for_status()

            with open(checksum_path, 'wb') as f:
                f.write(response.content)

            return binary_path

        except Exception as e:
            print(f"❌ Failed to download update: {e}")
            return None

    def verify_update(self, binary_path: Path) -> bool:
        """
        Verify downloaded update integrity

        Args:
            binary_path: Path to downloaded binary

        Returns:
            True if verification passed, False otherwise
        """
        checksum_path = binary_path.parent / f"{binary_path.name}.sha256"

        if not checksum_path.exists():
            print("❌ Checksum file not found")
            return False

        print("🔍 Verifying integrity...")
        if verify_with_checksum_file(binary_path, checksum_path):
            print("✅ Integrity verification passed")
            return True
        else:
            print("❌ Integrity verification FAILED")
            return False

    def install_update(self, binary_path: Path, version: Version) -> bool:
        """
        Install downloaded update

        Args:
            binary_path: Path to new binary
            version: Version being installed

        Returns:
            True if installation successful, False otherwise
        """
        try:
            # Get current executable path
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                current_exe = Path(sys.executable)
            else:
                # Running from source - use dummy path for testing
                current_exe = Path.cwd() / self.executable_name

            # Create backup
            print("💾 Creating backup...")
            current_version = get_current_version()
            backup_path = self.backup_manager.create_backup(current_exe, current_version)

            if not backup_path:
                print("❌ Failed to create backup")
                return False

            # Replace executable
            print("📦 Installing update...")

            # On Windows, we might need to rename old exe first
            if self.platform == "Windows":
                temp_old = current_exe.parent / f"{current_exe.stem}_old{current_exe.suffix}"
                if current_exe.exists():
                    current_exe.rename(temp_old)

                try:
                    import shutil
                    shutil.copy2(binary_path, current_exe)

                    # Remove old exe
                    if temp_old.exists():
                        temp_old.unlink()

                except Exception as e:
                    # Restore old exe if copy failed
                    if temp_old.exists():
                        temp_old.rename(current_exe)
                    raise e
            else:
                # Unix: can replace directly
                import shutil
                shutil.copy2(binary_path, current_exe)
                current_exe.chmod(0o755)  # Make executable

            # Update version file
            save_current_version(version, current_exe.parent / "version.json")

            print(f"✅ Update installed: {version}")
            return True

        except Exception as e:
            print(f"❌ Failed to install update: {e}")
            return False

    def rollback(self) -> bool:
        """
        Rollback to previous version

        Returns:
            True if rollback successful, False otherwise
        """
        print("🔄 Rolling back to previous version...")

        latest_backup = self.backup_manager.get_latest_backup()
        if not latest_backup:
            print("❌ No backup available for rollback")
            return False

        if getattr(sys, 'frozen', False):
            current_exe = Path(sys.executable)
        else:
            current_exe = Path.cwd() / self.executable_name

        return self.backup_manager.restore_backup(latest_backup, current_exe)

    def perform_update(self) -> bool:
        """
        Check and perform update if available

        Returns:
            True if update was performed, False otherwise
        """
        # Check for updates
        update_info = self.check_for_updates()
        if not update_info:
            return False

        print(f"\n🎉 New version available: {update_info['version']}")
        print(f"   Current version: {get_current_version()}")

        if not self.auto_update:
            print("   Auto-update is disabled")
            return False

        # Download update
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            binary_path = self.download_update(update_info, temp_path)

            if not binary_path:
                return False

            # Verify integrity
            if not self.verify_update(binary_path):
                return False

            # Install update
            if not self.install_update(binary_path, update_info['version']):
                return False

            # Cleanup old backups
            self.backup_manager.cleanup_old_backups(keep_count=5)

            print("✨ Update completed successfully!")
            print("🔄 Restart required to use new version")
            return True

    def run_update_loop(self):
        """
        Run continuous update check loop

        This will check for updates every check_interval seconds.
        """
        print(f"🔄 Auto-updater started (checking every {self.check_interval}s)")
        print(f"   Channel: {self.update_channel}")
        print(f"   Current version: {get_current_version()}")

        while True:
            try:
                self.perform_update()
            except Exception as e:
                print(f"❌ Error in update loop: {e}")

            # Wait before next check
            time.sleep(self.check_interval)