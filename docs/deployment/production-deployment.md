# 🚀 Despliegue en Producción

**Guía completa para distribuir Robot Runner en múltiples máquinas**

---

## Estrategias de Despliegue

| Método | Máquinas | Tiempo | Complejidad | Ideal Para |
|--------|----------|--------|-------------|------------|
| Script Local | 1-10 | 7 min/máq | Baja | Instalación manual |
| Despliegue Remoto | 10-100 | 20 min | Media | IT Teams |
| Binarios Compilados | 100+ | 3 min/user | Media | Usuarios finales |
| CI/CD Auto-Update | Ilimitado | 20 min | Alta | Enterprise |

---

## Método 1: Script Local

```powershell
# Windows
.\installers\windows\install_production.ps1 -Token "YOUR_TOKEN"

# Linux
./installers/linux/install_production.sh --token "YOUR_TOKEN"
```

⏱️ 7 minutos por máquina

---

## Método 2: Despliegue Remoto

```powershell
# Lista de máquinas en machines.txt
.\installers\windows\deploy_multiple.ps1 `
    -ComputerFile "machines.txt" `
    -Token "YOUR_TOKEN" `
    -Parallel 10
```

⏱️ 15-20 minutos para 50 máquinas

---

## Método 3: Binarios Compilados

```bash
# 1. Compilar
.\build\scripts\build_windows.bat

# 2. Distribuir ZIP
dist/RobotRunner-v1.0.0-Windows.zip

# 3. Usuarios extraen y ejecutan
```

⏱️ 2-3 minutos por usuario

---

## Método 4: CI/CD + Auto-Update

```bash
# 1. Crear tag
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0

# 2. GitHub Actions compila automáticamente
# 3. Clientes se actualizan solos
```

⏱️ 15-60 minutos total

---

## Configuración de Producción

```json
{
  "url": "https://api.tuempresa.com",
  "token": "YOUR_TOKEN",
  "machine_id": "PROD-ROBOT-01",
  "port": "5001",
  "tunnel_subdomain": "robot-01.automatehub.es",
  "auto_update_enabled": true
}
```

---

## Despliegue por Fases

1. **Piloto** (3-5 máquinas) - 1-2 días
2. **Rollout Gradual** (20% → 50% → 100%)
3. **Monitorización** post-despliegue

---

## Rollback

### Automático
Sistema detecta fallas y restaura backup anterior automáticamente.

### Manual
```bash
cp ~/Robot/backup/backup_*/RobotRunner.exe ~/Robot/
systemctl restart robotrunner
```

---

## Checklist

- [ ] Tests 87%+ pasando
- [ ] Configuración validada
- [ ] Backups configurados
- [ ] Monitorización lista
- [ ] Rollback testeado
- [ ] Usuarios notificados

---

📖 [Ver guía detallada de instalación](./installation.md)

**Última actualización:** 2026-01-19