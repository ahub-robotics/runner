# 🏗️ Guía de Compilación Completa

**Guía detallada para compilar Robot Runner en ejecutables standalone**

---

## Tabla de Contenidos

- [Introducción](#introducción)
- [Requisitos](#requisitos)
- [Compilación Windows](#compilación-windows)
- [Compilación Linux](#compilación-linux)
- [Compilación macOS](#compilación-macos)
- [PyInstaller Spec](#pyinstaller-spec)
- [Hooks Personalizados](#hooks-personalizados)
- [Optimización](#optimización)
- [Troubleshooting](#troubleshooting)

---

## Introducción

Robot Runner puede compilarse en ejecutables standalone que no requieren Python instalado.

### Ventajas

✅ **No requiere Python** en máquinas destino
✅ **Instalación rápida** (copiar y ejecutar)
✅ **Distribución simple** (un solo archivo ejecutable)
✅ **Versionado claro** (executable nombrado con versión)
✅ **Updates fáciles** (reemplazar ejecutable)

### Tecnología

Usamos **PyInstaller 6.10+** para crear binarios optimizados.

---

## Requisitos

### Herramientas

- Python 3.11+
- PyInstaller 6.10+
- Dependencias del proyecto

### Instalación

```bash
pip install -r requirements.txt
pip install pyinstaller==6.10.0
```

---

## Compilación Windows

### Opción 1: Script Automatizado

```powershell
# Compilar
.\build\scripts\build_windows.bat

# Output: dist\RobotRunner.exe
```

### Opción 2: Manual

```powershell
# Limpiar builds anteriores
rmdir /s /q build dist

# Compilar con PyInstaller
pyinstaller app.spec --clean

# Verificar
.\dist\RobotRunner.exe --version
```

### Resultado

```
dist/
└── RobotRunner.exe (80-120 MB)
```

---

## Compilación Linux

### Script Automatizado

```bash
#!/bin/bash
# build/scripts/build_linux.sh

./build/scripts/build_linux.sh

# Output: dist/RobotRunner
```

### Manual

```bash
# Limpiar
rm -rf build dist

# Compilar
pyinstaller app.spec --clean

# Dar permisos
chmod +x dist/RobotRunner

# Verificar
./dist/RobotRunner --version
```

---

## Compilación macOS

### Consideraciones

- Genera `.app` bundle para distribución
- Requiere firma de código (opcional)
- Soporta Intel y Apple Silicon

### Script

```bash
./build/scripts/build_macos.sh

# Output: dist/RobotRunner.app
```

### Firma de Código (Opcional)

```bash
# Requiere Apple Developer Account
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Tu Nombre" \
  dist/RobotRunner.app
```

---

## PyInstaller Spec

### app.spec

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('config_template.json', '.'),
    ],
    hiddenimports=[
        'flask',
        'celery',
        'redis',
        'engineio.async_drivers.threading',
        'pkg_resources.py2_warn',
    ],
    hookspath=['build/hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='RobotRunner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Comprimir con UPX
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Mostrar consola
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico'  # Windows icon
)
```

---

## Hooks Personalizados

### build/hooks/hook-pystray.py

```python
from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('pystray')
```

### build/hooks/hook-flask.py

```python
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('flask')
```

---

## Optimización

### Reducir Tamaño

1. **Excluir módulos no usados**
```python
excludes=[
    'matplotlib', 'numpy', 'pandas', 'scipy',
    'PIL', 'tkinter', 'wx', 'PyQt5',
]
```

2. **Comprimir con UPX**
```python
upx=True
upx_exclude=['vcruntime140.dll', 'python311.dll']
```

3. **Un solo archivo** (más lento de iniciar)
```python
onefile=True
```

### Mejorar Velocidad de Inicio

1. **Múltiples archivos** (más rápido)
```python
onefile=False
```

2. **Compilar en modo release** (sin debug)
```python
debug=False
strip=True
```

---

## Crear Instalador ZIP

```bash
# Windows
.\build\scripts\create_installer_zip.bat

# Genera: dist/RobotRunner-v1.0.0-Windows.zip
```

### Contenido del ZIP

```
RobotRunner-v1.0.0-Windows.zip
├── RobotRunner.exe
├── config_template.json
├── README.txt
└── LICENSE.txt
```

---

## Build Multiplataforma con GitHub Actions

### .github/workflows/build-and-release.yml

```yaml
name: Build and Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    strategy:
      matrix:
        os: [windows-latest, ubuntu-latest, macos-latest]
        include:
          - os: windows-latest
            artifact: RobotRunner-Windows.exe
          - os: ubuntu-latest
            artifact: RobotRunner-Linux
          - os: macos-latest
            artifact: RobotRunner-macOS.app

    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller==6.10.0

      - name: Build
        run: pyinstaller app.spec --clean

      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: ${{ matrix.artifact }}
          path: dist/

  release:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: dist/*
```

---

## Troubleshooting

### Error: "ModuleNotFoundError" al ejecutar

**Causa:** Falta hiddenimport

**Solución:**
```python
hiddenimports=[
    'modulo_faltante',
]
```

### Error: Ejecutable muy grande (> 200 MB)

**Solución:**
1. Excluir módulos no usados
2. Activar compresión UPX
3. Verificar `datas` innecesarios

### Error: Lento al iniciar

**Causa:** Modo `onefile=True`

**Solución:** Usar `onefile=False` o esperar 3-5 segundos

### Error: Antivirus bloquea ejecutable

**Causa:** Firma de código faltante

**Solución:**
- Windows: Firmar con certificado Authenticode
- macOS: Firmar con Apple Developer ID
- Añadir excepción al antivirus temporalmente

---

## Benchmarks

| Plataforma | Tamaño | Tiempo Build | Tiempo Inicio |
|------------|--------|--------------|---------------|
| Windows .exe | 95 MB | 3 min | 2-3 seg |
| Linux bin | 85 MB | 2.5 min | 1-2 seg |
| macOS .app | 100 MB | 3.5 min | 2-4 seg |

---

## Referencias

- [PyInstaller Documentation](https://pyinstaller.org/)
- [PyInstaller Spec Files](https://pyinstaller.org/en/stable/spec-files.html)
- [UPX Compressor](https://upx.github.io/)

---

**Última actualización:** 2026-01-19
**Versión:** 2.0.0