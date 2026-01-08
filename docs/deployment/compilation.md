# Compilation Guide - Robot Runner v2.0

Guía para compilar Robot Runner con PyInstaller.

---

## Overview

Robot Runner se puede compilar en ejecutables standalone para distribución usando **PyInstaller**.

**Beneficios**:
- Sin necesidad de Python instalado
- Dependencias incluidas
- Fácil distribución
- Instalación simplificada

---

## Requisitos

- Python 3.9+
- PyInstaller 5.13+
- Sistema operativo target (compilar en mismo OS que target)

```bash
pip install pyinstaller==5.13.0
```

---

## Compilación Rápida

### Usando app.spec

Robot Runner incluye `app.spec` pre-configurado:

```bash
# Compilar
pyinstaller app.spec

# Output en: dist/RobotRunner/
```

---

## app.spec Explicado

```python
# Entry point
a = Analysis(
    ['run.py'],              # Main entry point
    pathex=['.'],            # Search paths
    binaries=[],             # Additional binaries
    datas=[
        ('templates', 'templates'),      # HTML templates
        ('static', 'static'),            # CSS, JS, images
        ('ssl', 'ssl'),                  # SSL certificates
        ('config.json', '.'),            # Configuration
    ],
    hiddenimports=[
        'api',
        'executors',
        'streaming',
        'shared',
        'cli',
        'gui',
        # Flask dependencies
        'flask',
        'flask.json',
        'werkzeug',
        # Celery dependencies
        'celery',
        'celery.app',
        'kombu',
        # Other
        'redis',
        'mss',
        'PIL',
        'pystray',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

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
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/logo.ico',  # Application icon
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RobotRunner',
)
```

---

## Compilación por Plataforma

### macOS

```bash
# Compilar
pyinstaller app.spec

# Crear DMG (opcional)
hdiutil create -volname "Robot Runner" -srcfolder dist/RobotRunner -ov -format UDZO dist/RobotRunner.dmg

# Firmar (opcional)
codesign --force --deep --sign "Developer ID Application: Your Name" dist/RobotRunner.app
```

**Output**: `dist/RobotRunner/RobotRunner` (executable)

### Linux

```bash
# Compilar
pyinstaller app.spec

# Crear tarball
cd dist
tar -czf RobotRunner-Linux.tar.gz RobotRunner/
cd ..

# Output: dist/RobotRunner-Linux.tar.gz
```

### Windows

```bash
# Compilar
pyinstaller app.spec

# Crear installer con NSIS (opcional)
makensis installer.nsi

# Output: dist/RobotRunner/RobotRunner.exe
```

---

## Problemas Comunes y Soluciones

### 1. Missing Modules

**Error**: `ModuleNotFoundError: No module named 'X'`

**Solución**: Agregar a `hiddenimports` en app.spec:

```python
hiddenimports=[
    'missing_module',
    'another.module',
]
```

### 2. Missing Files

**Error**: `FileNotFoundError: [Errno 2] No such file or directory: 'templates'`

**Solución**: Agregar a `datas` en app.spec:

```python
datas=[
    ('path/to/file', 'destination'),
    ('path/to/dir', 'destination_dir'),
]
```

### 3. Large Executable Size

**Solución 1**: Excluir módulos innecesarios:

```python
excludes=[
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
]
```

**Solución 2**: Usar UPX compression (ya habilitado en app.spec):

```python
upx=True
```

### 4. Flask Templates Not Found

**Error**: `TemplateNotFound`

**Solución**: Verificar que templates estén en datas y que Flask busque en ruta correcta:

```python
# api/app.py
import sys
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder = os.path.join(sys._MEIPASS, 'static')
else:
    # Running as script
    template_folder = 'templates'
    static_folder = 'static'

app = Flask(__name__,
    template_folder=template_folder,
    static_folder=static_folder)
```

### 5. SSL Certificates Not Found

**Solución**: Incluir SSL directory en datas:

```python
datas=[
    ('ssl', 'ssl'),
]
```

Y actualizar paths en código:

```python
import sys
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)

ssl_cert = os.path.join(base_path, 'ssl', 'cert.pem')
```

---

## Optimización

### Reducir Tamaño

1. **Excluir tests**:
```python
excludes=['tests', 'pytest']
```

2. **One-file mode** (todo en un ejecutable):
```python
exe = EXE(
    ...,
    one_file=True,  # En lugar de one_dir
)
```

3. **Strip binaries** (Linux/macOS):
```bash
strip dist/RobotRunner/RobotRunner
```

### Mejorar Tiempo de Inicio

1. **Usar bootloader personalizado**
2. **Optimizar imports** (lazy imports donde sea posible)
3. **Cachear módulos**

---

## Testing del Ejecutable

```bash
# Ejecutar
cd dist/RobotRunner
./RobotRunner  # Linux/macOS
RobotRunner.exe  # Windows

# Verificar logs
tail -f logs/server.log

# Test API
curl -k https://localhost:5001/health
```

---

## Distribución

### Crear Paquete de Distribución

**macOS** (DMG):
```bash
# Crear DMG con installer
create-dmg \
  --volname "Robot Runner" \
  --volicon "resources/logo.icns" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "RobotRunner.app" 175 120 \
  --hide-extension "RobotRunner.app" \
  --app-drop-link 425 120 \
  "dist/RobotRunner.dmg" \
  "dist/RobotRunner/"
```

**Linux** (Tarball):
```bash
cd dist
tar -czf RobotRunner-v2.0.0-Linux.tar.gz RobotRunner/
sha256sum RobotRunner-v2.0.0-Linux.tar.gz > checksums.txt
```

**Windows** (ZIP + Installer):
```bash
# ZIP
cd dist
Compress-Archive -Path RobotRunner -DestinationPath RobotRunner-v2.0.0-Windows.zip

# NSIS Installer (opcional)
makensis installer.nsi
```

---

## CI/CD para Compilación Automática

### GitHub Actions

`.github/workflows/build.yml`:

```yaml
name: Build Executables

on:
  release:
    types: [created]

jobs:
  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller
      - name: Build
        run: pyinstaller app.spec
      - name: Create tarball
        run: |
          cd dist
          tar -czf RobotRunner-Linux.tar.gz RobotRunner/
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: linux-build
          path: dist/RobotRunner-Linux.tar.gz

  build-macos:
    runs-on: macos-latest
    steps:
      # Similar to Linux

  build-windows:
    runs-on: windows-latest
    steps:
      # Similar to Linux, but create ZIP
```

---

## Verificación Post-Compilación

### Checklist

- [ ] Ejecutable inicia correctamente
- [ ] Web UI accesible en https://localhost:5001
- [ ] Login funciona
- [ ] API endpoints responden
- [ ] SSL certificates se cargan
- [ ] Config.json se lee correctamente
- [ ] Logs se escriben en logs/
- [ ] Redis connection funciona
- [ ] Celery workers inician
- [ ] Streaming funciona
- [ ] Robot execution funciona

---

## Troubleshooting Avanzado

### Debug Mode

Compilar con debug mode para ver imports y errores:

```bash
pyinstaller --debug=all app.spec
```

### Ver Contenido del Ejecutable

```bash
# Ver archivos incluidos
pyi-archive_viewer dist/RobotRunner/RobotRunner

# Extraer contenido
pyi-archive_viewer dist/RobotRunner/RobotRunner
? X filename.py  # Extract file
```

### Logs de PyInstaller

```bash
# Ver logs de build
cat build/RobotRunner/warn-RobotRunner.txt
```

---

## Recursos Adicionales

- [PyInstaller Documentation](https://pyinstaller.org/)
- [PyInstaller Hooks](https://github.com/pyinstaller/pyinstaller-hooks-contrib)
- [Common Issues](https://github.com/pyinstaller/pyinstaller/wiki)

---

## Próximos Pasos

- Leer [Installation Guide](installation.md) para instrucciones de instalación
- Consultar [Production Guide](production.md) para deployment
- Ver [Cross-Platform Guide](cross-platform.md) para notas específicas del SO

---

**Actualizado**: 2026-01-08
**Versión**: 2.0.0
