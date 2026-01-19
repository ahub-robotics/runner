# 📋 Changelog

Historial de cambios y versiones de Robot Runner

---

## [2.0.0] - 2026-01-19

### 🎉 Release Mayor - Arquitectura v2.0

#### ✨ Añadido
- Arquitectura modular completa
- Soporte multiplataforma (Windows, Linux, macOS)
- Sistema CI/CD con GitHub Actions
- Auto-actualización automática en clientes
- Túneles Cloudflare Zero Trust
- Sistema de compilación con PyInstaller
- Scripts de instalación automatizada
- Despliegue masivo en múltiples máquinas
- Suite de 161 tests automatizados
- Documentación completa (20+ documentos)
- SSL/TLS con certificados CA propios
- Sistema de backup y rollback automático
- Tray app para Windows

#### 🔧 Cambiado
- Refactorización completa del código
- Nueva estructura de proyecto modular
- Mejoras en el sistema de estado (SQLite)
- Sistema de logging mejorado
- API REST rediseñada

#### 🐛 Corregido
- Múltiples bugs de compatibilidad Windows
- Problemas de gestión de túneles
- Errores en detección de procesos multiplataforma
- Fix en manejo de hostnames de túneles
- Corrección de URLs de acceso en mensajes de inicio

#### 🔒 Seguridad
- Implementación de autenticación por tokens
- Sistema SSL/TLS completo
- Verificación SHA256 en actualizaciones
- Túneles seguros con Cloudflare

---

## [1.x.x] - 2025

### Versiones Legacy

Historial de versiones anteriores a la refactorización v2.0.

Ver repositorio para detalles completos.

---

## Tipos de Cambios

- **✨ Añadido**: Nueva funcionalidad
- **🔧 Cambiado**: Cambios en funcionalidad existente
- **⚠️ Deprecado**: Funcionalidad que será removida
- **🗑️ Eliminado**: Funcionalidad removida
- **🐛 Corregido**: Bug fixes
- **🔒 Seguridad**: Cambios relacionados con seguridad

---

## Versionado Semántico

Robot Runner sigue [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH
```

- **MAJOR**: Cambios incompatibles con versiones anteriores
- **MINOR**: Nueva funcionalidad compatible con versiones anteriores
- **PATCH**: Bug fixes compatibles con versiones anteriores

---

**Última actualización:** 2026-01-19