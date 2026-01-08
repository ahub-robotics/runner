# -*- mode: python ; coding: utf-8 -*-
# =================================================================
# PyInstaller Spec File - Robot Runner v2.0
# =================================================================
# Compilación para arquitectura modular refactorizada.
#
# Uso:
#     pyinstaller app.spec
#
# Output:
#     dist/RobotRunner/  - Directorio con ejecutable y dependencias
#
# Plataformas:
#     - macOS:   dist/RobotRunner/RobotRunner
#     - Linux:   dist/RobotRunner/RobotRunner
#     - Windows: dist/RobotRunner/RobotRunner.exe
# =================================================================

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Detectar plataforma
IS_WINDOWS = sys.platform.startswith('win')
IS_MACOS = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')

# ============================================================================
# ANALYSIS - Recolectar módulos y datos
# ============================================================================

a = Analysis(
    ['run.py'],  # Entry point principal
    pathex=['.'],  # Rutas de búsqueda para módulos
    binaries=[],
    datas=[
        # Templates y static files (Flask)
        ('templates', 'templates'),
        ('static', 'static'),

        # SSL certificates
        ('ssl', 'ssl'),

        # Resources
        ('resources', 'resources'),

        # Configuration (example)
        ('config.json', '.'),

        # Robots directory (si existe)
        # ('Robots', 'Robots'),  # Descomentar si se necesita
    ],

    hiddenimports=[
        # ========== Core modules ==========
        'api',
        'api.app',
        'api.auth',
        'api.middleware',
        'api.wsgi',

        # Web blueprints
        'api.web',
        'api.web.auth',
        'api.web.ui',
        'api.web.settings',

        # REST blueprints
        'api.rest',
        'api.rest.status',
        'api.rest.execution',
        'api.rest.info',

        # Streaming blueprints
        'api.streaming',
        'api.streaming.control',
        'api.streaming.feed',

        # Tunnel blueprints
        'api.tunnel',
        'api.tunnel.routes',

        # Server management
        'api.server',
        'api.server.routes',

        # ========== Executors ==========
        'executors',
        'executors.runner',
        'executors.server',
        'executors.tasks',
        'executors.process_manager',

        # ========== Streaming ==========
        'streaming',
        'streaming.streamer',
        'streaming.tasks',
        'streaming.capture',

        # ========== Shared ==========
        'shared',
        'shared.config',
        'shared.config.loader',
        'shared.config.cli',
        'shared.state',
        'shared.state.redis_client',
        'shared.state.redis_manager',
        'shared.state.redis_state',
        'shared.celery_app',
        'shared.celery_app.config',
        'shared.celery_app.worker',
        'shared.utils',
        'shared.utils.process',
        'shared.utils.ssl_utils',
        'shared.utils.tunnel',

        # ========== CLI & GUI ==========
        'cli',
        'cli.run_server',
        'cli.run_tray',
        'gui',
        'gui.tray_app',

        # ========== Flask dependencies ==========
        'flask',
        'flask.app',
        'flask.blueprints',
        'flask.json',
        'flask.sessions',
        'werkzeug',
        'werkzeug.security',
        'werkzeug.serving',
        'jinja2',
        'jinja2.ext',
        'markupsafe',

        # ========== Gunicorn ==========
        'gunicorn',
        'gunicorn.app',
        'gunicorn.app.base',
        'gunicorn.workers',
        'gunicorn.workers.sync',

        # ========== Celery dependencies ==========
        'celery',
        'celery.app',
        'celery.app.task',
        'celery.backends',
        'celery.backends.redis',
        'celery.concurrency',
        'celery.worker',
        'kombu',
        'kombu.transport',
        'kombu.transport.redis',
        'billiard',

        # ========== Redis ==========
        'redis',
        'redis.client',
        'redis.connection',

        # ========== RobotFramework ==========
        'robot',
        'robot.api',
        'robot.run',
        'robot.libdoc',

        # ========== Streaming dependencies ==========
        'mss',
        'mss.darwin',  # macOS
        'mss.linux',   # Linux
        'mss.windows', # Windows
        'PIL',
        'PIL.Image',
        'PIL.ImageGrab',

        # ========== System tray ==========
        'pystray',
        'pystray._win32' if IS_WINDOWS else 'pystray._darwin' if IS_MACOS else 'pystray._gtk',

        # ========== Other dependencies ==========
        'requests',
        'yaml',
        'json',
        'subprocess',
        'threading',
        'multiprocessing',
        'queue',
        'ssl',
        'base64',
        'io',
    ],

    hookspath=['build/hooks'],  # Custom hooks
    hooksconfig={},
    runtime_hooks=[],

    excludes=[
        # Excluir módulos innecesarios para reducir tamaño
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL.ImageTk',  # Tkinter (no lo usamos)
        'tkinter',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'test',
        'tests',
        'setuptools',
        'pip',
    ],

    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ============================================================================
# PYZ - Python Archive
# ============================================================================

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# ============================================================================
# EXE - Executable
# ============================================================================

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='RobotRunner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window (GUI mode)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/logo.ico' if os.path.exists('resources/logo.ico') else None,
)

# ============================================================================
# COLLECT - Bundle everything
# ============================================================================

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RobotRunner'
)

# ============================================================================
# Platform-specific configurations
# ============================================================================

# macOS: Create .app bundle (opcional, descomentar si se desea)
# if IS_MACOS:
#     app = BUNDLE(
#         coll,
#         name='RobotRunner.app',
#         icon='resources/logo.icns',
#         bundle_identifier='com.yourcompany.robotrunner',
#         info_plist={
#             'NSPrincipalClass': 'NSApplication',
#             'NSHighResolutionCapable': 'True',
#         },
#     )
