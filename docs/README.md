# 📚 Documentación de Robot Runner

Índice completo de toda la documentación del proyecto Robot Runner.

---

## 📖 Índice Principal

- [🏠 README Principal](../README.md) - Inicio rápido y visión general
- [📋 Changelog](general/changelog.md) - Historial de cambios
- [✅ Estado de Producción](general/production-ready.md) - Preparación para producción

---

## 🎯 Documentación General

| Documento | Descripción | Tamaño |
|-----------|-------------|--------|
| [**Listo para Producción**](general/production-ready.md) | Resumen completo de preparación para producción | 11 KB |
| [**Setup CI/CD**](general/ci-cd-setup.md) | Quick start del sistema de integración continua (15 min) | 11 KB |
| [**Configuración de Túneles**](general/tunnel-setup.md) | Configuración de túneles Cloudflare | 7 KB |
| [**Changelog**](general/changelog.md) | Historial de cambios y versiones | 8 KB |
| [**Reporte de Validación**](general/validation-report.md) | Validación de funcionalidad y tests | 8 KB |

---

## 🏗️ Arquitectura

| Documento | Descripción | Tamaño |
|-----------|-------------|--------|
| [**Visión General**](architecture/overview.md) | Arquitectura del sistema completo | - |
| [**Componentes**](architecture/components.md) | Descripción de módulos principales | - |
| [**Flujo de Datos**](architecture/data-flow.md) | Cómo fluye la información en el sistema | - |
| [**Arquitectura Windows**](architecture/windows-architecture.md) | Detalles específicos de Windows | - |

**Temas cubiertos:**
- Patrón de diseño modular
- Comunicación entre componentes
- Sistema de estado compartido (Redis)
- Arquitectura de Celery workers
- Integración de streaming

---

## 🔌 API

| Documento | Descripción | Tamaño |
|-----------|-------------|--------|
| [**REST API**](api/rest-api.md) | Referencia completa de endpoints | - |
| [**Autenticación**](api/authentication.md) | Sistema de tokens y seguridad | - |

**Endpoints documentados:**
- `/status` - Estado del robot
- `/execution` - Ejecución de tareas
- `/run`, `/stop`, `/pause`, `/resume` - Control de ejecución
- `/stream/*` - Streaming de pantalla
- `/tunnel/*` - Gestión de túneles

---

## 👨‍💻 Desarrollo

| Documento | Descripción | Tamaño |
|-----------|-------------|--------|
| [**Setup de Desarrollo**](development/setup.md) | Configurar entorno de desarrollo | - |
| [**Testing**](development/testing.md) | Ejecutar tests y coverage | - |
| [**Contribuir**](development/contributing.md) | Guía para contribuidores | - |

**Contenido:**
- Configuración del entorno local
- Ejecución de tests (161 tests)
- Code coverage (42.84%)
- Guías de estilo de código
- Workflow de contribución

---

## 🚀 Despliegue y Producción

### Instalación y Configuración

| Documento | Descripción | Tamaño |
|-----------|-------------|--------|
| [**Instalación**](deployment/installation.md) | Instalar Robot Runner paso a paso | 10 KB |
| [**Producción**](deployment/production.md) | Configuración para entornos de producción | 11 KB |
| [**Cross-Platform**](deployment/cross-platform.md) | Soporte multiplataforma | 9 KB |

### Compilación

| Documento | Descripción | Tamaño |
|-----------|-------------|--------|
| [**Compilación**](deployment/compilation.md) | Compilar ejecutables con PyInstaller | 9 KB |
| [**Guía de Compilación Completa**](deployment/compilation-guide.md) | Guía detallada de build (6000+ palabras) | 12 KB |

**Plataformas soportadas:**
- Windows 10/11 (64-bit)
- Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)
- macOS (Big Sur 11+)

### Distribución Masiva

| Documento | Descripción | Tamaño |
|-----------|-------------|--------|
| [**Despliegue en Producción**](deployment/production-deployment.md) | Estrategias de distribución masiva (8000+ palabras) | 14 KB |

**Métodos de distribución:**
1. **Script Automatizado** - Para 1-10 máquinas (7 min)
2. **Despliegue Remoto** - Para 10-100 máquinas (15-20 min)
3. **Binarios Compilados** - Para 100+ máquinas (2 min/usuario)
4. **CI/CD Auto-Update** - Para cualquier escala (15-20 min)

---

## 🔄 CI/CD y Auto-Actualización

| Documento | Descripción | Tamaño |
|-----------|-------------|--------|
| [**Guía CI/CD Completa**](deployment/ci-cd-guide.md) | Sistema completo de integración continua (6000+ palabras) | 20 KB |
| [**Setup CI/CD Rápido**](general/ci-cd-setup.md) | Quick start de 15 minutos | 11 KB |

**Sistema CI/CD incluye:**
- GitHub Actions workflow completo
- Compilación automática (Windows + Linux)
- Creación automática de releases
- Servidor de actualizaciones
- Auto-actualización en clientes
- Rollback automático
- Monitorización de versiones

**Flujo completo:**
```bash
git tag -a v1.1.0 -m "Release 1.1.0"
git push origin v1.1.0
# → GitHub Actions compila
# → Crea release
# → Todas las máquinas se actualizan en ~1 hora
```

---

## 🔐 Seguridad

| Documento | Descripción | Tamaño |
|-----------|-------------|--------|
| [**Sistema CA**](security/ssl-certificates.md) | Gestión de certificados SSL/TLS | - |
| [**Changelog de Seguridad**](security/changelog.md) | Historial de cambios de seguridad | - |

**Características de seguridad:**
- Autenticación por token
- SSL/TLS con CA propia
- Cloudflare Tunnel
- Verificación de checksums (SHA256)
- Backup y rollback automático

---

## 📖 Documentación de Usuario

| Documento | Descripción | Tamaño |
|-----------|-------------|--------|
| [**Documentación Funcional**](functional-documentation.md) | Guía de usuario completa | - |
| [**Documentación Técnica**](technical-documentation.md) | Referencia técnica detallada | - |
| [**Nuevas Funcionalidades**](nuevas-funcionalidades.md) | Características añadidas recientemente | - |
| [**Setup Windows**](windows-setup.md) | Configuración específica de Windows | - |

---

## 🗂️ Documentación por Caso de Uso

### Para Desarrolladores

1. [Setup de Desarrollo](development/setup.md)
2. [Arquitectura del Sistema](architecture/overview.md)
3. [API Reference](api/rest-api.md)
4. [Testing](development/testing.md)
5. [Contribuir](development/contributing.md)

### Para Administradores de Sistemas

1. [Instalación](deployment/installation.md)
2. [Despliegue en Producción](deployment/production-deployment.md)
3. [CI/CD Setup](general/ci-cd-setup.md)
4. [Configuración de Túneles](general/tunnel-setup.md)
5. [Seguridad](security/ssl-certificates.md)

### Para DevOps

1. [CI/CD Completo](deployment/ci-cd-guide.md)
2. [Compilación](deployment/compilation-guide.md)
3. [Despliegue Masivo](deployment/production-deployment.md)
4. [Cross-Platform](deployment/cross-platform.md)

### Para Usuarios Finales

1. [Documentación Funcional](functional-documentation.md)
2. [Setup Rápido](../README.md#quick-start)
3. [Configuración Básica](deployment/installation.md)

---

## 📊 Estadísticas de Documentación

| Categoría | Documentos | Tamaño Total |
|-----------|-----------|--------------|
| **General** | 5 | ~45 KB |
| **Arquitectura** | 4 | - |
| **API** | 2 | - |
| **Desarrollo** | 3 | - |
| **Despliegue** | 7 | ~70 KB |
| **Seguridad** | 2 | - |
| **Usuario** | 4 | - |
| **TOTAL** | **27 documentos** | **>115 KB** |

---

## 🔍 Búsqueda Rápida

### Por Tema

- **Instalación**: [installation.md](deployment/installation.md), [production.md](deployment/production.md)
- **Compilación**: [compilation.md](deployment/compilation.md), [compilation-guide.md](deployment/compilation-guide.md)
- **CI/CD**: [ci-cd-guide.md](deployment/ci-cd-guide.md), [ci-cd-setup.md](general/ci-cd-setup.md)
- **Seguridad**: [ssl-certificates.md](security/ssl-certificates.md), [authentication.md](api/authentication.md)
- **API**: [rest-api.md](api/rest-api.md), [authentication.md](api/authentication.md)
- **Testing**: [testing.md](development/testing.md), [validation-report.md](general/validation-report.md)

### Por Plataforma

- **Windows**: [windows-setup.md](windows-setup.md), [windows-architecture.md](architecture/windows-architecture.md)
- **Linux**: [cross-platform.md](deployment/cross-platform.md), [installation.md](deployment/installation.md)
- **macOS**: [cross-platform.md](deployment/cross-platform.md), [compilation-guide.md](deployment/compilation-guide.md)

### Por Nivel de Experiencia

- **Principiante**: [README](../README.md), [installation.md](deployment/installation.md), [functional-documentation.md](functional-documentation.md)
- **Intermedio**: [production.md](deployment/production.md), [api/rest-api.md](api/rest-api.md), [testing.md](development/testing.md)
- **Avanzado**: [ci-cd-guide.md](deployment/ci-cd-guide.md), [production-deployment.md](deployment/production-deployment.md), [architecture/*](architecture/)

---

## 📝 Cómo Contribuir a la Documentación

1. Lee la [guía de contribución](development/contributing.md)
2. Los documentos están en formato Markdown
3. Usa títulos descriptivos y enlaces internos
4. Incluye ejemplos de código cuando sea relevante
5. Actualiza este índice si agregas documentos nuevos

---

## 🔗 Enlaces Externos

- [Repositorio GitHub](https://github.com/tu-org/robot-runner)
- [Issues y Bugs](https://github.com/tu-org/robot-runner/issues)
- [Discussions](https://github.com/tu-org/robot-runner/discussions)
- [Releases](https://github.com/tu-org/robot-runner/releases)

---

## 📞 Soporte

¿No encuentras lo que buscas?

- 🐛 [Reporta un problema](https://github.com/tu-org/robot-runner/issues/new)
- 💬 [Pregunta en Discussions](https://github.com/tu-org/robot-runner/discussions)
- 📧 Contacto: support@tuempresa.com

---

**Última actualización:** 2026-01-16
**Versión de documentación:** 2.0.0
