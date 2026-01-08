# Contributing Guide - Robot Runner v2.0

Guía para contribuir al proyecto Robot Runner.

---

## ¡Bienvenido!

Agradecemos tu interés en contribuir a Robot Runner. Este documento te guiará en el proceso de contribución.

---

## Código de Conducta

- Sé respetuoso y profesional
- Acepta críticas constructivas
- Enfócate en lo mejor para el proyecto
- Ayuda a otros contribuidores

---

## Cómo Contribuir

### 1. Reportar Bugs

Antes de reportar un bug:
- Busca en [Issues](https://github.com/your-org/robotrunner/issues) si ya fue reportado
- Asegúrate de que es realmente un bug, no un error de configuración

**Información a incluir**:
- Versión de Robot Runner
- Sistema operativo y versión
- Versión de Python
- Pasos para reproducir el bug
- Comportamiento esperado vs actual
- Logs relevantes
- Screenshots (si aplica)

**Template**:

```markdown
## Bug Description
[Descripción clara y concisa del bug]

## Steps to Reproduce
1. [Paso 1]
2. [Paso 2]
3. [Paso 3]

## Expected Behavior
[Qué esperabas que pasara]

## Actual Behavior
[Qué pasó realmente]

## Environment
- Robot Runner version: 2.0.0
- OS: macOS 13.5
- Python: 3.9.7
- Redis: 5.0.14

## Logs
```
[Logs relevantes]
```

## Screenshots
[Si aplica]
```

### 2. Proponer Features

Antes de proponer una feature:
- Busca en Issues si ya fue sugerida
- Asegúrate de que alinea con los objetivos del proyecto

**Template**:

```markdown
## Feature Description
[Descripción clara de la feature]

## Use Case
[Por qué es necesaria esta feature]

## Proposed Solution
[Cómo propones implementarla]

## Alternatives Considered
[Otras soluciones consideradas]

## Additional Context
[Cualquier contexto adicional]
```

### 3. Contribuir Código

#### Fork y Clone

```bash
# Fork el repositorio en GitHub

# Clone tu fork
git clone https://github.com/YOUR-USERNAME/robotrunner.git
cd robotrunner

# Agregar upstream remote
git remote add upstream https://github.com/your-org/robotrunner.git
```

#### Crear una Branch

```bash
# Actualizar master
git checkout master
git pull upstream master

# Crear feature branch
git checkout -b feature/my-feature

# O bugfix branch
git checkout -b bugfix/fix-issue-123
```

#### Hacer Cambios

1. **Escribir código** siguiendo [Style Guide](#style-guide)
2. **Escribir tests** para tu código (obligatorio)
3. **Actualizar documentación** si es necesario
4. **Ejecutar tests** para asegurar que todo funciona

```bash
# Run tests
pytest

# Check code style
black --check .
flake8 .

# Run type checking
mypy .
```

#### Commit

Usamos **Conventional Commits**:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: Nueva feature
- `fix`: Bug fix
- `docs`: Cambios en documentación
- `style`: Formateo (no afecta código)
- `refactor`: Refactoring
- `test`: Agregar/modificar tests
- `chore`: Tareas de mantenimiento
- `perf`: Mejoras de performance

**Scope** (opcional):
- `api`: API layer
- `executors`: Executors layer
- `streaming`: Streaming layer
- `shared`: Shared layer
- `cli`: CLI
- `gui`: GUI
- `tests`: Tests
- `docs`: Documentation

**Examples**:

```bash
# Feature
git commit -m "feat(api): add pause/resume endpoints for execution control"

# Bug fix
git commit -m "fix(streaming): resolve frame capture crash on macOS"

# Documentation
git commit -m "docs(api): update authentication examples"

# Refactor
git commit -m "refactor(executors): extract process management to shared utils"
```

#### Push y Pull Request

```bash
# Push tu branch
git push origin feature/my-feature

# Abrir Pull Request en GitHub
```

**PR Template**:

```markdown
## Description
[Descripción de los cambios]

## Type of Change
- [ ] Bug fix (non-breaking change que arregla un issue)
- [ ] New feature (non-breaking change que agrega funcionalidad)
- [ ] Breaking change (fix o feature que causa que funcionalidad existente no funcione como se esperaba)
- [ ] Documentation update

## Related Issues
Closes #123

## How Has This Been Tested?
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Mi código sigue el style guide del proyecto
- [ ] He realizado un self-review de mi código
- [ ] He comentado mi código donde es necesario
- [ ] He actualizado la documentación
- [ ] Mis cambios no generan nuevos warnings
- [ ] He agregado tests que prueban mi fix/feature
- [ ] Los tests nuevos y existentes pasan localmente
- [ ] Los cambios requieren actualización de documentación y la he actualizado

## Screenshots (si aplica)
[Screenshots]
```

---

## Style Guide

### Python Code Style

Seguimos **PEP 8** con algunas excepciones:

- **Max line length**: 100 caracteres (no 79)
- **String quotes**: Preferir comillas dobles `"` sobre simples `'`
- **Imports**: Ordenar alphabetically dentro de cada grupo

**Usar Black para formateo automático**:

```bash
black .
```

### Import Order

```python
# 1. Standard library
import os
import sys

# 2. Third-party
import flask
import redis

# 3. Local application
from api import get_server
from shared.config.loader import get_config_data
```

### Naming Conventions

```python
# Variables y funciones: snake_case
def calculate_execution_time():
    execution_id = "exec-123"

# Classes: PascalCase
class ServerManager:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# Private functions/methods: _leading_underscore
def _internal_helper():
    pass
```

### Docstrings

Usar **Google Style**:

```python
def function_with_args(arg1, arg2, optional_arg=None):
    """
    Brief description of function.

    Longer description if needed.

    Args:
        arg1 (str): Description of arg1
        arg2 (int): Description of arg2
        optional_arg (dict, optional): Description. Defaults to None.

    Returns:
        bool: Description of return value

    Raises:
        ValueError: When arg1 is invalid
    """
    pass


class MyClass:
    """
    Brief description of class.

    Attributes:
        attr1 (str): Description of attr1
        attr2 (int): Description of attr2
    """

    def __init__(self, attr1):
        """Initialize MyClass.

        Args:
            attr1 (str): Description
        """
        self.attr1 = attr1
```

### Type Hints

Usar type hints donde sea posible:

```python
from typing import Dict, List, Optional

def process_execution(
    execution_id: str,
    params: Dict[str, str],
    timeout: Optional[int] = None
) -> bool:
    """Process robot execution."""
    pass
```

---

## Testing Requirements

### Coverage

- **Minimum**: 70% overall coverage
- **New code**: >80% coverage para nuevas features

### Test Types

1. **Unit tests**: Obligatorio para nueva funcionalidad
2. **Integration tests**: Obligatorio para nuevos endpoints
3. **Manual tests**: Opcional para debugging complejo

### Running Tests Locally

```bash
# All tests
pytest

# With coverage
pytest --cov=. --cov-report=term-missing

# Specific test
pytest tests/unit/test_api_auth.py -v
```

---

## Documentation Requirements

### When to Update Docs

- **Nuevos endpoints**: Actualizar `docs/api/rest-api.md`
- **Nuevos componentes**: Actualizar `docs/architecture/components.md`
- **Cambios en setup**: Actualizar `docs/development/setup.md`
- **Nuevas features**: Actualizar README.md y docs relevantes

### Documentation Style

- Usar Markdown
- Incluir code examples
- Mantener tono profesional y claro
- Incluir diagramas cuando sea útil (ASCII art está bien)

---

## Review Process

### Code Review Checklist

Reviewers evaluarán:

- [ ] **Funcionalidad**: ¿El código hace lo que dice?
- [ ] **Tests**: ¿Hay tests adecuados?
- [ ] **Style**: ¿Sigue el style guide?
- [ ] **Performance**: ¿Es eficiente?
- [ ] **Security**: ¿Hay vulnerabilidades?
- [ ] **Documentation**: ¿Está documentado?
- [ ] **Breaking changes**: ¿Rompe funcionalidad existente?

### Addressing Review Comments

1. **Responder a todos los comentarios**
2. **Hacer cambios solicitados**
3. **Marcar como resuelto** cuando esté listo
4. **Re-request review** después de cambios

### Merge Criteria

PR será mergeado cuando:
- ✅ Todos los checks de CI pasan
- ✅ Al menos 1 approval de maintainer
- ✅ Todos los comentarios resueltos
- ✅ No conflicts con master

---

## Development Workflow

### Feature Development

```bash
# 1. Actualizar master
git checkout master
git pull upstream master

# 2. Crear branch
git checkout -b feature/new-feature

# 3. Desarrollar
# - Escribir código
# - Escribir tests
# - Actualizar docs

# 4. Commit frecuentemente
git add .
git commit -m "feat(scope): description"

# 5. Push y crear PR
git push origin feature/new-feature
```

### Bug Fix Workflow

```bash
# 1. Crear bugfix branch
git checkout -b bugfix/fix-issue-123

# 2. Fix bug
# - Escribir test que reproduce el bug
# - Fix el código
# - Verificar que test pasa

# 3. Commit
git commit -m "fix(scope): description\n\nCloses #123"

# 4. Push y crear PR
git push origin bugfix/fix-issue-123
```

---

## Release Process

(Para maintainers)

### Version Numbering

Seguimos **Semantic Versioning** (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: Nuevas features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. [ ] Actualizar version en todos los archivos relevantes
2. [ ] Actualizar CHANGELOG.md
3. [ ] Ejecutar full test suite
4. [ ] Crear release tag
5. [ ] Build y publicar artifacts (PyInstaller)
6. [ ] Crear GitHub release con notes
7. [ ] Anunciar release

---

## Getting Help

### Communication Channels

- **GitHub Issues**: Para bugs y features
- **GitHub Discussions**: Para preguntas y discusiones
- **Email**: dev@robotrunner.com

### Resources

- [Architecture Docs](../architecture/overview.md)
- [API Docs](../api/rest-api.md)
- [Testing Guide](testing.md)
- [Setup Guide](setup.md)

---

## Recognition

Contributors serán reconocidos en:
- CONTRIBUTORS.md
- Release notes
- GitHub contributors page

---

## License

Al contribuir, aceptas que tus contribuciones serán licenciadas bajo la misma licencia que el proyecto.

---

**¡Gracias por contribuir a Robot Runner!** 🤖

---

**Actualizado**: 2026-01-08
**Versión**: 2.0.0
