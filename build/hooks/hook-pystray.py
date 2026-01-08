"""
PyInstaller hook for pystray (system tray library).

Ensures platform-specific pystray modules are included.
"""
import sys
from PyInstaller.utils.hooks import collect_submodules

# Collect all pystray submodules
hiddenimports = collect_submodules('pystray')

# Platform-specific modules
if sys.platform == 'darwin':
    hiddenimports += ['pystray._darwin']
elif sys.platform.startswith('linux'):
    hiddenimports += ['pystray._gtk']
elif sys.platform.startswith('win'):
    hiddenimports += ['pystray._win32']
