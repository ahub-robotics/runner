"""
PyInstaller hook for MSS (screen capture library).

Ensures platform-specific MSS modules are included.
"""
import sys
from PyInstaller.utils.hooks import collect_submodules

# Collect all MSS submodules
hiddenimports = collect_submodules('mss')

# Platform-specific modules
if sys.platform == 'darwin':
    hiddenimports += ['mss.darwin']
elif sys.platform.startswith('linux'):
    hiddenimports += ['mss.linux']
elif sys.platform.startswith('win'):
    hiddenimports += ['mss.windows']
