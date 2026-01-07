# -*- mode: python ; coding: utf-8 -*-
# =================================================================
# PyInstaller Spec File - Robot Runner
# =================================================================
# Este archivo define cómo empaquetar Robot Runner en un ejecutable.
#
# Uso:
#     pyinstaller app.spec
#
# El ejecutable resultará en: dist/RobotRunner/
# =================================================================

a = Analysis(
    ['run.py'],  # Entry point principal (antes: app.py)
    pathex=['.'],  # Rutas de búsqueda para módulos
    binaries=[],  # Binarios adicionales a incluir
    datas=[
        # Archivos de datos a incluir en el ejecutable
        ('templates', 'templates'),  # Templates HTML de Flask
        ('static', 'static'),  # Archivos estáticos (CSS, JS, imágenes)
        ('config.json', '.'),  # Archivo de configuración
        ('Robots', 'Robots'),  # Scripts de robots
        ('ssl', 'ssl'),  # Certificados SSL
        ('src', 'src'),  # Paquete src/ con código del servidor
    ],
    hiddenimports=[
        # Imports que PyInstaller podría no detectar automáticamente
        'src',
        'src.app',
        'src.server',
        'src.robot',
        'src.config',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='RobotRunner',  # Nombre del ejecutable
    debug=False,  # No incluir debugging
    bootloader_ignore_signals=False,
    strip=False,  # No strip symbols
    upx=True,  # Comprimir con UPX
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No mostrar consola (modo GUI)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/logo.ico',  # Icono de la aplicación
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RobotRunner'  # Nombre del directorio de distribución
)