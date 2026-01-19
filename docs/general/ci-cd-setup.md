# 🔄 Setup CI/CD - Guía Rápida

**Configurar integración continua y despliegue automático en 15 minutos**

---

## Quick Start

```bash
# 1. Hacer cambios
git add .
git commit -m "Feature: New functionality"

# 2. Crear tag versionado
git tag -a v1.0.0 -m "Release 1.0.0"

# 3. Push (dispara GitHub Actions)
git push origin v1.0.0

# 4. ¡Las máquinas se actualizan automáticamente!
```

⏱️ **15-60 minutos** desde tag hasta todas las máquinas actualizadas

---

## Cómo Funciona

1. **Developer** crea tag → 2. **GitHub Actions** compila → 3. **Release** automático → 4. **Clientes** descargan y actualizan

---

## Requisitos

- ✅ Repositorio GitHub
- ✅ GitHub Actions habilitado
- ✅ Archivo `.github/workflows/build-and-release.yml`
- ✅ Clientes con auto-update habilitado

---

## Versionado

Usar [Semantic Versioning](https://semver.org/):

- `v1.0.0` - Release inicial
- `v1.1.0` - Nueva funcionalidad
- `v1.1.1` - Bug fix
- `v2.0.0` - Breaking change

---

## Troubleshooting

**Build falla:** Ver logs en Actions tab

**Clientes no actualizan:** Verificar `~/Robot/logs/updater.log`

---

📖 [Ver guía completa](../deployment/ci-cd-guide.md)

**Última actualización:** 2026-01-19