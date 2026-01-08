# Robot Runner - Documentación

Documentación completa para Robot Runner v2.0 - Sistema de ejecución remota de robots con arquitectura modular.

## 📚 Índice de Documentación

### 🏗️ Arquitectura
Comprende la arquitectura del sistema y sus componentes.

- [**Visión General**](architecture/overview.md) - Arquitectura de alto nivel y diseño del sistema
- [**Componentes**](architecture/components.md) - Componentes principales y su interacción
- [**Flujo de Datos**](architecture/data-flow.md) - Cómo fluyen los datos a través del sistema
- [**Diagramas**](architecture/diagrams/) - Diagramas visuales de la arquitectura

### 🔌 API
Documentación de la API REST y autenticación.

- [**REST API**](api/rest-api.md) - Documentación completa de la API REST
- [**Autenticación**](api/authentication.md) - Sistema de autenticación y tokens
- [**Endpoints**](api/endpoints.md) - Referencia completa de endpoints

### 💻 Desarrollo
Guías para desarrolladores que contribuyen al proyecto.

- [**Setup**](development/setup.md) - Configuración del entorno de desarrollo
- [**Testing**](development/testing.md) - Guía de testing y cobertura
- [**Contributing**](development/contributing.md) - Guía de contribución al proyecto
- [**Architecture Decisions**](development/architecture-decisions.md) - Decisiones arquitectónicas (ADRs)

### 🚀 Deployment
Instrucciones de instalación y despliegue.

- [**Instalación**](deployment/installation.md) - Guía de instalación paso a paso
- [**Producción**](deployment/production.md) - Deployment en entornos de producción
- [**Compilación**](deployment/compilation.md) - Compilación con PyInstaller
- [**Cross-Platform**](deployment/cross-platform.md) - Notas para diferentes sistemas operativos

### 🔒 Seguridad
Documentación de seguridad y certificados.

- [**Certificados SSL**](security/ssl-certificates.md) - Gestión de certificados SSL/TLS
- [**Security Changelog**](security/changelog.md) - Historial de cambios de seguridad

### 📖 Documentación Legacy
Documentación de versiones anteriores (para referencia).

- [**Documentación Técnica v1**](TECHNICAL-DOCUMENTATION.md) - Documentación técnica original
- [**Documentación Funcional v1**](FUNCTIONAL-DOCUMENTATION.md) - Guía de usuario v1
- [**Nuevas Funcionalidades**](NUEVAS_FUNCIONALIDADES.md) - Changelog de features

---

## 🚀 Inicio Rápido

### Para Usuarios
1. Lee la [Guía de Instalación](deployment/installation.md)
2. Consulta la [Documentación Funcional](FUNCTIONAL-DOCUMENTATION.md)
3. Revisa [Cross-Platform](deployment/cross-platform.md) para tu sistema operativo

### Para Desarrolladores
1. Configura tu entorno con [Setup](development/setup.md)
2. Lee la [Arquitectura](architecture/overview.md)
3. Consulta la [Guía de Contribución](development/contributing.md)
4. Ejecuta tests con [Testing Guide](development/testing.md)

### Para Integradores de API
1. Revisa la [Documentación de API](api/rest-api.md)
2. Configura [Autenticación](api/authentication.md)
3. Consulta [Referencia de Endpoints](api/endpoints.md)

---

## 🔄 Versiones

- **v2.0** (Actual) - Arquitectura modular con Flask Blueprints, tests completos
- **v1.x** - Arquitectura monolítica (legacy)

### Cambios Principales v2.0
- ✅ Arquitectura modular (api/, executors/, streaming/, shared/)
- ✅ División de app.py monolítico en 15+ módulos especializados
- ✅ Suite completa de tests (171 tests: unit + integration)
- ✅ CLI mejorado con entry points dedicados
- ✅ System tray app separada
- ✅ Documentación completa y actualizada

---

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/tu-org/robotrunner/issues)
- **Discusiones**: [GitHub Discussions](https://github.com/tu-org/robotrunner/discussions)
- **Email**: support@robotrunner.com

---

## 📄 Licencia

[Especificar licencia aquí]

---

**Última actualización**: 2026-01-08
**Versión de documentación**: 2.0.0
