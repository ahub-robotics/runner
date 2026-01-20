# -*- mode: python ; coding: utf-8 -*-
# =================================================================
# PyInstaller Spec File - Robot Runner v2.0 (ONE FILE)
# =================================================================
# Versión optimizada para CI/CD - genera un solo ejecutable
#
# Uso:
#     pyinstaller app-onefile.spec
#
# Output:
#     dist/RobotRunner      - Ejecutable único (Linux/macOS)
#     dist/RobotRunner.exe  - Ejecutable único (Windows)
# =================================================================

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Detectar plataforma
IS_WINDOWS = sys.platform.startswith('win')
IS_MACOS = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')

a = Analysis(
    ['run.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('ssl', 'ssl'),
        ('resources', 'resources'),
        ('config.json', '.'),
        ('version.json', '.'),
    ],
    hiddenimports=[
        # Core modules
        'api', 'api.app', 'api.auth', 'api.middleware', 'api.wsgi',
        'api.web', 'api.web.auth', 'api.web.ui', 'api.web.settings',
        'api.rest', 'api.rest.status', 'api.rest.execution', 'api.rest.info',
        'api.streaming', 'api.streaming.control', 'api.streaming.feed',
        'api.tunnel', 'api.tunnel.routes',
        'api.server', 'api.server.routes',

        # Executors
        'executors', 'executors.runner', 'executors.server', 'executors.tasks', 'executors.process_manager',

        # Streaming
        'streaming', 'streaming.streamer', 'streaming.tasks', 'streaming.capture',

        # Shared
        'shared', 'shared.config', 'shared.config.loader', 'shared.config.cli',
        'shared.state', 'shared.state.redis_client', 'shared.state.redis_manager', 'shared.state.redis_state',
        'shared.celery_app', 'shared.celery_app.config', 'shared.celery_app.worker',
        'shared.utils', 'shared.utils.process', 'shared.utils.ssl_utils', 'shared.utils.tunnel',
        'shared.updater', 'shared.updater.auto_updater', 'shared.updater.version',
        'shared.updater.checksum', 'shared.updater.backup',

        # CLI & GUI
        'cli', 'cli.run_server', 'cli.run_tray',
        'gui', 'gui.tray_app',

        # Flask
        'flask', 'flask.app', 'flask.blueprints', 'flask.json', 'flask.sessions',
        'werkzeug', 'werkzeug.security', 'werkzeug.serving',
        'jinja2', 'jinja2.ext', 'markupsafe',

        # Gunicorn
        'gunicorn', 'gunicorn.app', 'gunicorn.app.base', 'gunicorn.workers', 'gunicorn.workers.sync',

        # Celery
        'celery', 'celery.app', 'celery.app.task', 'celery.backends', 'celery.backends.redis',
        'celery.concurrency', 'celery.worker',
        'kombu', 'kombu.transport', 'kombu.transport.redis',
        'billiard',

        # Redis
        'redis', 'redis.client', 'redis.connection',

        # RobotFramework
        'robot', 'robot.api', 'robot.run', 'robot.libdoc',

        # Streaming
        'mss', 'mss.darwin', 'mss.linux', 'mss.windows',
        'PIL', 'PIL.Image', 'PIL.ImageGrab',

        # System tray
        'pystray',
        'pystray._win32' if IS_WINDOWS else 'pystray._darwin' if IS_MACOS else 'pystray._gtk',

        # Other
        'requests', 'yaml', 'json', 'subprocess', 'threading', 'multiprocessing',
        'queue', 'ssl', 'base64', 'io',
    ],
    hookspath=['build/hooks'] if os.path.exists('build/hooks') else [],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'pandas', 'scipy', 'PIL.ImageTk',
        'tkinter', 'IPython', 'jupyter', 'notebook', 'pytest',
        'test', 'tests', 'setuptools', 'pip',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ============================================================================
# ONE FILE EXECUTABLE - Todo en un solo archivo
# ============================================================================
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,      # ← Incluir binaries en el exe
    a.zipfiles,      # ← Incluir zipfiles en el exe
    a.datas,         # ← Incluir datas en el exe
    [],
    name='RobotRunner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Sin ventana de consola
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/logo.ico' if os.path.exists('resources/logo.ico') else None,
)