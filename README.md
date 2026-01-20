# 🤖 Robot Runner

**Sistema de ejecución remota de robots de automatización con comunicación segura y despliegue automático**

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/tu-org/robot-runner)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](docs/general/production-ready.md)

---

## 📖 ¿Qué es Robot Runner?

Robot Runner es una plataforma completa para la **ejecución remota y gestión de robots de automatización**. Permite controlar, monitorizar y desplegar robots en múltiples máquinas de forma centralizada con soporte multiplataforma.

### ✨ Características Principales

- 🌐 **Multiplataforma** - Windows, Linux y macOS
- 🔒 **Seguro** - SSL/TLS, autenticación por tokens, túneles Cloudflare
- 📹 **Streaming** - Visualización de pantalla en tiempo real
- 🔄 **CI/CD Integrado** - Despliegue automático en todas las máquinas
- 📦 **Compilable** - Genera ejecutables standalone con PyInstaller
- 🎯 **Escalable** - Despliega en 1 o 1000 máquinas fácilmente
- 🛠️ **Modular** - Arquitectura limpia y extensible
- 🧪 **Testeado** - Suite completa de 161 tests automatizados

---

## 🚀 Quick Start

### Instalación Rápida (5 minutos)

```bash
# 1. Clonar repositorio
git clone https://github.com/tu-org/robot-runner
cd robot-runner

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar (editar config.json o usar CLI)
cp config_template.json config.json

# 4. Ejecutar
python run.py
```

Accede a `https://localhost:8088` y comienza a ejecutar robots.

📖 **Guías de inicio:**
- [Instalación Detallada](docs/deployment/installation.md)
- [Configuración Inicial](docs/development/setup.md)
- [Configuración con Túnel Cloudflare](docs/general/tunnel-setup.md)

---

## 📚 Documentación

### 🎯 Documentación General

| Documento | Descripción |
|-----------|-------------|
| [**Listo para Producción**](docs/general/production-ready.md) | Resumen completo de preparación para producción |
| [**Setup CI/CD**](docs/general/ci-cd-setup.md) | Quick start del sistema de integración continua |
| [**Configuración de Túneles**](docs/general/tunnel-setup.md) | Configuración de túneles Cloudflare |
| [**Changelog**](docs/general/changelog.md) | Historial de cambios y versiones |
| [**Reporte de Validación**](docs/general/validation-report.md) | Validación de funcionalidad y tests |

### 🏗️ Arquitectura

| Documento | Descripción |
|-----------|-------------|
| [**Visión General**](docs/architecture/overview.md) | Arquitectura del sistema completo |
| [**Componentes**](docs/architecture/components.md) | Descripción de módulos principales |
| [**Flujo de Datos**](docs/architecture/data-flow.md) | Cómo fluye la información en el sistema |
| [**Arquitectura Windows**](docs/architecture/windows-architecture.md) | Detalles específicos de Windows |

### 🔌 API

| Documento | Descripción |
|-----------|-------------|
| [**REST API**](docs/api/rest-api.md) | Referencia completa de endpoints |
| [**Autenticación**](docs/api/authentication.md) | Sistema de tokens y seguridad |

### 👨‍💻 Desarrollo

| Documento | Descripción |
|-----------|-------------|
| [**Setup de Desarrollo**](docs/development/setup.md) | Configurar entorno de desarrollo |
| [**Testing**](docs/development/testing.md) | Ejecutar tests y coverage |
| [**Contribuir**](docs/development/contributing.md) | Guía para contribuidores |

### 🚀 Despliegue y Producción

| Documento | Descripción |
|-----------|-------------|
| [**Instalación**](docs/deployment/installation.md) | Instalar Robot Runner paso a paso |
| [**Producción**](docs/deployment/production.md) | Configuración para entornos de producción |
| [**Despliegue en Producción**](docs/deployment/production-deployment.md) | Estrategias de despliegue masivo |
| [**Compilación**](docs/deployment/compilation.md) | Compilar ejecutables con PyInstaller |
| [**Guía de Compilación Completa**](docs/deployment/compilation-guide.md) | Guía detallada de build multiplataforma |
| [**CI/CD Completo**](docs/deployment/ci-cd-guide.md) | Sistema completo de integración y despliegue continuo |
| [**Setup CI/CD Rápido**](docs/general/ci-cd-setup.md) | Quick start de CI/CD en 15 minutos |
| [**Auto-Actualización**](docs/deployment/auto-update-guide.md) | Sistema de updates automáticos |
| [**Cross-Platform**](docs/deployment/cross-platform.md) | Soporte multiplataforma |

### 🔐 Seguridad

| Documento | Descripción |
|-----------|-------------|
| [**Sistema CA**](docs/security/ssl-certificates.md) | Gestión de certificados SSL/TLS |
| [**Changelog de Seguridad**](docs/security/changelog.md) | Historial de cambios de seguridad |

### 📖 Otros

| Documento | Descripción |
|-----------|-------------|
| [**Documentación Funcional**](docs/functional-documentation.md) | Guía de usuario completa |
| [**Documentación Técnica**](docs/technical-documentation.md) | Referencia técnica detallada |
| [**Nuevas Funcionalidades**](docs/nuevas-funcionalidades.md) | Características añadidas recientemente |
| [**Setup Windows**](docs/windows-setup.md) | Configuración específica de Windows |

---

## 🎯 Casos de Uso

### 1. Instalación en Una Máquina

```bash
# Instalación automatizada (Windows)
.\installers\windows\install_production.ps1

# O instalación manual
pip install -r requirements.txt
python run.py
```

⏱️ **Tiempo:** 7 minutos

📖 [Ver guía completa](docs/deployment/installation.md)

---

### 2. Despliegue en Múltiples Máquinas (5-50)

```powershell
# Crear lista de máquinas
# Editar: installers/windows/machines.txt

# Desplegar remotamente
.\installers\windows\deploy_multiple.ps1 `
    -ComputerFile "machines.txt" `
    -Token "YOUR_TOKEN"
```

⏱️ **Tiempo:** 15-20 minutos para 50 máquinas (paralelo)

📖 [Ver guía de despliegue masivo](docs/deployment/production-deployment.md#despliegue-masivo)

---

### 3. Compilar y Distribuir Binarios (100+ máquinas)

```bash
# 1. Compilar ejecutable
.\build\scripts\build_windows.bat

# 2. Crear paquete distributable
.\build\scripts\create_installer_zip.bat

# 3. Distribuir ZIP a usuarios
# dist/RobotRunner-v1.0.0-Windows.zip
```

⏱️ **Tiempo:** 2-3 minutos por usuario final

📖 [Ver guía de compilación](docs/deployment/compilation-guide.md)

---

### 4. CI/CD - Despliegue Automático

```bash
# 1. Hacer cambios en el código
git commit -m "Add new feature"

# 2. Crear tag de versión
git tag -a v1.1.0 -m "Release 1.1.0"
git push origin v1.1.0

# 3. ¡GitHub Actions hace el resto!
#    - Compila binarios (Windows + Linux)
#    - Crea GitHub Release
#    - Todas las máquinas se actualizan automáticamente
```

⏱️ **Tiempo:** 15-20 minutos desde push hasta todas las máquinas actualizadas

📖 [Ver guía CI/CD](docs/deployment/ci-cd-guide.md)

---

## 🛠️ Tecnologías

**Backend:**
- Flask 3.0+ (Web framework modular)
- Gunicorn (WSGI server con SSL)
- Celery 5.3+ (Tareas asíncronas)
- Redis (Estado compartido)
- RabbitMQ (Message broker)

**Testing:**
- pytest 7.4+ (161 tests)
- pytest-cov (42.84% coverage)
- pytest-mock

**Build & Deploy:**
- PyInstaller 6.10+ (Compilación)
- GitHub Actions (CI/CD)
- PowerShell (Scripts Windows)

**Security:**
- OpenSSL (Certificados CA)
- Token-based Auth
- Cloudflare Tunnel

---

## 📊 Estructura del Proyecto

```
robot-runner/
├── run.py                          # Entry point principal
├── config.json                     # Configuración
├── requirements.txt                # Dependencias
│
├── api/                            # 🌐 Interfaz web y REST API
│   ├── web/                        # Interfaz web
│   ├── rest/                       # API REST
│   ├── streaming/                  # Sistema de streaming
│   └── tunnel/                     # Gestión de túneles
│
├── executors/                      # 🤖 Ejecución de robots
│   ├── runner.py
│   ├── server.py
│   └── tasks.py
│
├── streaming/                      # 📹 Streaming de pantalla
│   ├── streamer.py
│   ├── capture.py
│   └── tasks.py
│
├── shared/                         # 🔧 Código común
│   ├── config/                     # Configuración
│   ├── state/                      # Estado (Redis)
│   ├── celery_app/                 # Celery
│   ├── updater/                    # Auto-actualización
│   └── utils/                      # Utilidades
│
├── installers/                     # 📦 Scripts de instalación
│   └── windows/
│       ├── install_production.ps1  # Instalación desatendida
│       ├── deploy_multiple.ps1     # Despliegue masivo
│       └── install_all.ps1         # Instalación interactiva
│
├── build/                          # 🏗️ Sistema de compilación
│   ├── scripts/                    # Scripts de build
│   └── hooks/                      # PyInstaller hooks
│
├── docs/                           # 📚 Documentación completa
│   ├── general/                    # Documentación general
│   ├── architecture/               # Arquitectura
│   ├── api/                        # API Reference
│   ├── development/                # Guías de desarrollo
│   ├── deployment/                 # Despliegue y producción
│   └── security/                   # Seguridad
│
├── update_server/                  # 🔄 Servidor de actualizaciones
│   └── app.py                      # API Flask
│
├── tests/                          # 🧪 Suite de tests
│   ├── unit/                       # Tests unitarios
│   └── integration/                # Tests de integración
│
└── .github/workflows/              # ⚙️ GitHub Actions CI/CD
    └── build-and-release.yml
```

---

## 🔒 Seguridad

Robot Runner implementa múltiples capas de seguridad:

- ✅ **Autenticación por Token** - Todas las peticiones API requieren token
- ✅ **SSL/TLS** - Comunicación cifrada con certificados CA propios
- ✅ **Cloudflare Tunnel** - Túnel seguro sin exponer puertos
- ✅ **Verificación de Checksums** - SHA256 en descargas de actualizaciones
- ✅ **Backup Automático** - Antes de cada actualización
- ✅ **Rollback Automático** - Si una actualización falla

📖 [Ver documentación de seguridad](docs/security/ssl-certificates.md)

---

## 🎓 Comparativa de Métodos de Distribución

| Método | Tiempo Setup | Complejidad | Ideal Para |
|--------|--------------|-------------|------------|
| **Script Automatizado** | 7 min | ⭐ Baja | 1-10 máquinas |
| **Despliegue Remoto** | 15-20 min (50 máquinas) | ⭐⭐ Media | 10-100 máquinas |
| **Binarios Compilados** | 2 min/usuario | ⭐⭐ Media | 100+ máquinas |
| **CI/CD Auto-Update** | 15-20 min (todas) | ⭐⭐⭐ Alta | Cualquier escala |

📖 [Ver comparativa completa](docs/deployment/production-deployment.md#comparativa-de-estrategias)

---

## 🚦 Estado del Proyecto

### ✅ Completado

- [x] Arquitectura modular v2.0
- [x] Suite de tests (161 tests, 87% passing)
- [x] Compilación multiplataforma (Windows, Linux, macOS)
- [x] Sistema de instalación automatizada
- [x] Despliegue masivo en múltiples máquinas
- [x] CI/CD con GitHub Actions
- [x] Auto-actualización en clientes
- [x] Servidor de actualizaciones
- [x] Documentación completa (20+ documentos)

### 🔜 Próximamente

- [ ] Dashboard web de administración
- [ ] Métricas y monitorización (Prometheus/Grafana)
- [ ] Soporte para Docker/Kubernetes
- [ ] API REST v2 con FastAPI
- [ ] WebSocket para comunicación en tiempo real

---

## 📞 Soporte y Contribución

### 🐛 Reportar Problemas

¿Encontraste un bug? [Abre un issue](https://github.com/tu-org/robot-runner/issues)

### 💡 Sugerir Mejoras

¿Tienes una idea? [Crea una discussion](https://github.com/tu-org/robot-runner/discussions)

### 🤝 Contribuir

Lee nuestra [guía de contribución](docs/development/contributing.md)

### 📧 Contacto

Para soporte empresarial: support@tuempresa.com

---

## 📜 Licencia

Este proyecto está licenciado bajo [MIT License](LICENSE)

---

## 🙏 Agradecimientos

Desarrollado con ❤️ usando:
- [Flask](https://flask.palletsprojects.com/)
- [Celery](https://docs.celeryq.dev/)
- [PyInstaller](https://pyinstaller.org/)
- [GitHub Actions](https://github.com/features/actions)

---

## 📈 Estadísticas

![GitHub Stars](https://img.shields.io/github/stars/tu-org/robot-runner?style=social)
![GitHub Forks](https://img.shields.io/github/forks/tu-org/robot-runner?style=social)
![GitHub Issues](https://img.shields.io/github/issues/tu-org/robot-runner)
![GitHub Pull Requests](https://img.shields.io/github/issues-pr/tu-org/robot-runner)

---

**¿Listo para empezar?** 🚀

Elige tu método preferido:
- 📖 [Instalación rápida en una máquina](docs/deployment/installation.md)
- 🌐 [Despliegue en múltiples máquinas](docs/deployment/production-deployment.md)
- 🔄 [Configurar CI/CD automático](docs/general/ci-cd-setup.md)

---

**Última actualización:** 2026-01-16
**Versión:** 2.0.0
