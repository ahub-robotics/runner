# 🔄 Guía CI/CD Completa

**Sistema completo de integración continua y despliegue automático**

---

## Visión General

El sistema CI/CD de Robot Runner automatiza completamente el ciclo:

```
Code → Build → Test → Release → Deploy → Monitor
```

---

## Componentes

### 1. GitHub Actions

Compila automáticamente en cada tag:

```yaml
# .github/workflows/build-and-release.yml
on:
  push:
    tags:
      - 'v*'
```

### 2. Build Matrix

Compila para 3 plataformas en paralelo:

- Windows (PyInstaller)
- Linux (PyInstaller)
- macOS (PyInstaller + .app)

### 3. Release Automation

Crea GitHub Release con:
- Binarios compilados
- Checksums SHA256
- Release notes

### 4. Auto-Updater

Clientes verifican y descargan automáticamente:
- Cada 1 hora (configurable)
- Verificación SHA256
- Backup + Rollback automático

---

## Workflow Completo

### Paso 1: Desarrollo

```bash
# Hacer cambios
git add .
git commit -m "Feature: Add new functionality"
```

### Paso 2: Testing Local

```bash
# Ejecutar tests
pytest tests/

# Verificar coverage
pytest --cov=. --cov-report=html

# Build local (opcional)
./build/scripts/build_windows.bat
```

### Paso 3: Crear Release

```bash
# Crear tag versionado
git tag -a v1.0.0 -m "Release 1.0.0

Features:
- Nueva funcionalidad X
- Mejora en rendimiento Y

Fixes:
- Bug fix Z
"

# Push tag (dispara GitHub Actions)
git push origin v1.0.0
```

### Paso 4: Build Automático

GitHub Actions ejecuta:

1. **Checkout código**
2. **Setup Python 3.11**
3. **Install dependencies**
4. **Run tests** (opcional)
5. **Build binarios** (Win/Lin/Mac)
6. **Generate checksums**
7. **Create GitHub Release**
8. **Upload artifacts**

⏱️ Duración: 3-5 minutos

### Paso 5: Auto-Deploy en Clientes

Clientes ejecutan:

```python
# shared/updater/auto_updater.py

while True:
    # Verificar nueva versión (cada 1h)
    latest = check_github_release()

    if latest > current_version:
        # Descargar binario + checksum
        download_release(latest)

        # Verificar SHA256
        if verify_checksum():
            # Backup actual
            backup_current()

            # Reemplazar ejecutable
            replace_executable()

            # Restart servicio
            restart_service()

            # Health check
            if not health_check():
                # Rollback si falla
                rollback()

    sleep(3600)  # 1 hora
```

⏱️ Duración: 5-10 minutos por máquina

---

## Configuración

### GitHub Secrets

Necesarios en Settings → Secrets:

- `GITHUB_TOKEN` (auto-generado)

### Variables de Entorno

```bash
# En clientes
GITHUB_REPO=tu-org/robot-runner
AUTO_UPDATE_ENABLED=true
CHECK_INTERVAL=3600  # segundos
```

---

## Versionado Semántico

```
v{MAJOR}.{MINOR}.{PATCH}
```

**Reglas:**
- `MAJOR`: Breaking changes
- `MINOR`: New features (compatible)
- `PATCH`: Bug fixes

**Ejemplos:**
- `v1.0.0` → `v1.1.0` (nueva feature)
- `v1.1.0` → `v1.1.1` (bug fix)
- `v1.1.1` → `v2.0.0` (breaking change)

---

## Estrategias de Rollout

### 1. Rollout Inmediato (100%)

```bash
git tag v1.0.0
git push origin v1.0.0
# Todas las máquinas se actualizan en 1-60 min
```

**Uso:** Bug fixes urgentes

### 2. Rollout Gradual (Canary)

```bash
# Opción A: Tags específicos
git tag v1.0.0-canary  # Solo máquinas en "canary channel"
git tag v1.0.0-stable  # Todas las demás

# Opción B: Configuración por máquina
{
  "update_channel": "canary"  # o "stable"
}
```

**Uso:** Features grandes

### 3. Rollout Programado

```python
# shared/updater/scheduler.py

# Solo actualizar en ventana de mantenimiento
if is_maintenance_window():
    update()
```

**Uso:** Entornos críticos

---

## Monitoring

### Build Status

```
https://github.com/tu-org/robot-runner/actions
```

Ver estado de builds en tiempo real

### Release Status

```bash
# API de GitHub
curl https://api.github.com/repos/tu-org/robot-runner/releases/latest
```

### Client Status

```bash
# Logs del updater
tail -f ~/Robot/logs/updater.log

# Health check
curl https://localhost:5001/health
```

---

## Troubleshooting

### Build falla en Actions

1. Ver logs en Actions tab
2. Identificar error
3. Corregir código
4. Crear nuevo tag: `v1.0.1`

### Cliente no actualiza

```bash
# Verificar logs
cat ~/Robot/logs/updater.log

# Verificar conectividad
curl -I https://api.github.com

# Verificar configuración
cat ~/Robot/config.json | grep auto_update
```

### Update falla en cliente

Sistema hace rollback automático:

```
[UPDATER] ❌ Health check failed
[UPDATER] 🔄 Rolling back to v0.9.0
[UPDATER] ✅ Rollback successful
```

---

## Rollback Manual

### Rollback de Release

```bash
# Eliminar tag malo
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0

# Eliminar Release en GitHub
# (o marcarlo como "draft")
```

### Rollback en Cliente

```bash
# Restaurar backup
cp ~/Robot/backup/backup_*/RobotRunner.exe ~/Robot/

# Reiniciar
systemctl restart robotrunner  # Linux
net restart RobotRunner  # Windows
```

---

## Métricas

### Build Time

- Windows: 3-4 min
- Linux: 2-3 min
- macOS: 3-5 min
- **Total**: ~5 min (paralelo)

### Deployment Time

- Detección: 0-60 min (depende del check interval)
- Descarga: 1-2 min
- Instalación: 1-2 min
- **Total**: 5-65 min por máquina

### Success Rate

- Build: 95%+ (con tests)
- Update: 98%+ (con rollback)
- Overall: 93%+ (end-to-end)

---

## Best Practices

### Pre-Release

- [ ] Ejecutar tests localmente
- [ ] Incrementar versión correctamente
- [ ] Escribir release notes claras
- [ ] Testear build local

### Release

- [ ] Usar tags versionados (`v*`)
- [ ] Seguir Semantic Versioning
- [ ] Incluir changelog en tag message
- [ ] Verificar que Actions completa exitosamente

### Post-Release

- [ ] Monitorizar logs de clientes
- [ ] Verificar métricas de actualización
- [ ] Responder a issues rápidamente
- [ ] Documentar problemas encontrados

---

## Automatizaciones Avanzadas

### Tests Automáticos Pre-Build

```yaml
# .github/workflows/build-and-release.yml

- name: Run Tests
  run: |
    pytest tests/ --cov

- name: Check Coverage
  run: |
    coverage report --fail-under=85
```

### Notificaciones

```yaml
- name: Notify Slack
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "Build failed: ${{ github.ref }}"
      }
```

### Multi-Environment

```yaml
strategy:
  matrix:
    environment: [staging, production]

env:
  DEPLOY_ENV: ${{ matrix.environment }}
```

---

## Seguridad

### Firma de Código

```yaml
# Windows
- name: Sign Binary
  run: |
    signtool sign /f cert.pfx /p ${{ secrets.CERT_PASSWORD }} dist/RobotRunner.exe
```

### Verificación de Checksums

```python
# Cliente verifica SHA256 antes de instalar
if not verify_checksum(binary, checksum):
    raise SecurityError("Checksum mismatch")
```

### Dependabot

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
```

---

## Referencias

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Semantic Versioning](https://semver.org/)
- [CI/CD Setup Rápido](../general/ci-cd-setup.md)

---

**Última actualización:** 2026-01-19
**Versión:** 2.0.0