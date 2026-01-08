# Build Directory - Robot Runner v2.0

Configuración y scripts para compilación multiplataforma con PyInstaller.

---

## Estructura

```
build/
├── README.md                    # Este archivo
├── hooks/                       # PyInstaller custom hooks
│   ├── hook-celery.py          # Hook para Celery
│   ├── hook-flask.py           # Hook para Flask
│   ├── hook-mss.py             # Hook para MSS (screen capture)
│   └── hook-pystray.py         # Hook para pystray (system tray)
├── scripts/                     # Scripts de build por plataforma
│   ├── build_macos.sh          # Build para macOS
│   ├── build_linux.sh          # Build para Linux
│   └── build_windows.bat       # Build para Windows
└── configs/                     # Configuraciones específicas (futuro)
```

---

## Quick Start

### macOS

```bash
# Build
./build/scripts/build_macos.sh

# Output: dist/RobotRunner-macOS.zip
```

### Linux

```bash
# Build
./build/scripts/build_linux.sh

# Output: dist/RobotRunner-Linux.tar.gz
```

### Windows

```cmd
REM Build
build\scripts\build_windows.bat

REM Output: dist\RobotRunner-Windows.zip
```

---

## Requisitos

### Todos los Sistemas

- **Python 3.9+**
- **PyInstaller 5.13+**: `pip install pyinstaller`
- **Dependencias**: `pip install -r requirements.txt`

### macOS Específico

- **Xcode Command Line Tools**
- **create-dmg** (opcional para DMG): `brew install create-dmg`

### Linux Específico

- **build-essential**
- **python3-dev**

### Windows Específico

- **Visual C++ Build Tools**
- **PyWin32**: Instalado automáticamente con PyInstaller

---

## Custom Hooks

Los hooks personalizados en `hooks/` aseguran que PyInstaller incluya todos los módulos necesarios.

### hook-celery.py

- Recolecta todos los submódulos de Celery
- Incluye Kombu y Billiard
- Asegura que backends y workers estén presentes

### hook-flask.py

- Recolecta Flask, Werkzeug y Jinja2
- Incluye templates y static files handling
- Añade blueprints support

### hook-mss.py

- Incluye módulos específicos por plataforma
- macOS: `mss.darwin`
- Linux: `mss.linux`
- Windows: `mss.windows`

### hook-pystray.py

- Incluye backends de system tray por plataforma
- macOS: `pystray._darwin`
- Linux: `pystray._gtk`
- Windows: `pystray._win32`

---

## Build Process

### 1. Clean

Elimina builds anteriores:
```bash
rm -rf build/RobotRunner dist/RobotRunner
```

### 2. Build

Ejecuta PyInstaller con app.spec:
```bash
pyinstaller app.spec
```

### 3. Package

Crea distributable:
- **macOS**: ZIP + DMG (opcional)
- **Linux**: tar.gz + checksums
- **Windows**: ZIP

### 4. Test

Verifica que el ejecutable funciona:
```bash
./dist/RobotRunner/RobotRunner --help
```

---

## Troubleshooting

### "ModuleNotFoundError" durante ejecución

**Solución**: Agregar módulo a `hiddenimports` en `app.spec`:

```python
hiddenimports=[
    'missing_module',
    'another.module',
]
```

### Templates/Static Files no encontrados

**Solución**: Verificar que estén en `datas` de `app.spec`:

```python
datas=[
    ('templates', 'templates'),
    ('static', 'static'),
]
```

### Ejecutable muy grande

**Soluciones**:
1. Agregar módulos innecesarios a `excludes` en `app.spec`
2. Habilitar UPX compression (ya habilitado)
3. Usar `strip` en Linux/macOS

### Error "Cannot find existing PyQt5 plugin directories"

**Solución**: No usamos PyQt5, asegurar que esté en `excludes`:

```python
excludes=['PyQt5', 'PyQt6']
```

---

## CI/CD Integration

Para builds automáticos en GitHub Actions, ver:
- `.github/workflows/build.yml` (pendiente de crear en FASE 11)

Ejemplo:

```yaml
jobs:
  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -r requirements.txt pyinstaller
      - run: ./build/scripts/build_macos.sh
      - uses: actions/upload-artifact@v3
        with:
          name: robotrunner-macos
          path: dist/RobotRunner-macOS.zip
```

---

## Platform-Specific Notes

### macOS

- **Code Signing**: Requerido para distribución fuera de App Store
- **Notarization**: Requerido para macOS 10.15+
- **DMG**: Mejor experiencia de usuario que ZIP

**Code Signing**:
```bash
codesign --force --deep --sign "Developer ID Application: Your Name" dist/RobotRunner.app
```

### Linux

- **Desktop Entry**: Crear `.desktop` file para menú de aplicaciones
- **AppImage**: Considerar AppImage para mejor compatibilidad
- **Dependencies**: Verificar shared libraries con `ldd`

### Windows

- **Installer**: Considerar NSIS o Inno Setup para installer
- **UAC**: Configurar manifest si requiere admin
- **Antivirus**: Firmar con certificado para evitar false positives

---

## Size Optimization

### Current Sizes (Approximate)

- **macOS**: ~150 MB (uncompressed), ~50 MB (ZIP)
- **Linux**: ~120 MB (uncompressed), ~40 MB (tar.gz)
- **Windows**: ~130 MB (uncompressed), ~45 MB (ZIP)

### Reduce Size

1. **Exclude unnecessary modules**:
```python
excludes=['matplotlib', 'numpy', 'pandas', 'scipy']
```

2. **One-file mode** (slower startup):
```python
exe = EXE(..., onefile=True)
```

3. **UPX compression** (ya habilitado):
```python
upx=True
```

---

## Testing Builds

### Automated Tests

```bash
# Build
./build/scripts/build_macos.sh

# Test executable exists
test -f dist/RobotRunner/RobotRunner

# Test executable runs
./dist/RobotRunner/RobotRunner --help

# Test server starts (with timeout)
timeout 5 ./dist/RobotRunner/RobotRunner || true
```

### Manual Tests

1. ✅ Executable starts without errors
2. ✅ Web UI accessible at https://localhost:5001
3. ✅ Login works
4. ✅ API endpoints respond
5. ✅ SSL certificates load
6. ✅ Config.json read correctly
7. ✅ Logs write to logs/
8. ✅ Redis connection works
9. ✅ Celery workers start
10. ✅ System tray (if applicable)

---

## Resources

- [PyInstaller Documentation](https://pyinstaller.org/)
- [PyInstaller Hooks](https://github.com/pyinstaller/pyinstaller-hooks-contrib)
- [Compilation Guide](../docs/deployment/compilation.md)

---

**Última actualización**: 2026-01-08
**Versión**: 2.0.0
