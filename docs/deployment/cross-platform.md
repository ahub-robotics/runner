# Robot Runner - Compatibilidad Multiplataforma

## Resumen

Robot Runner ha sido diseñado para funcionar de manera consistente en **Windows**, **Linux** y **macOS**. Las funciones críticas de control de procesos (pausar, reanudar y detener) utilizan la biblioteca `psutil` para garantizar comportamiento uniforme en todas las plataformas.

---

## Plataformas Soportadas

| Plataforma | Versión Mínima | Estado | Notas |
|------------|----------------|--------|-------|
| **Windows** | Windows 10 | ✅ Totalmente soportado | Usa TerminateProcess API |
| **Linux** | Kernel 3.x+ | ✅ Totalmente soportado | Usa señales POSIX |
| **macOS** | 10.14 (Mojave)+ | ✅ Totalmente soportado | Usa señales POSIX + fix fork safety |

---

## Funciones Multiplataforma

### 1. Pausar Ejecución (`pause_execution()`)

**Implementación Multiplataforma:**
- Utiliza `psutil.Process.suspend()` en todas las plataformas
- Suspende el proceso padre y todos sus hijos recursivamente
- Manejo robusto de errores (procesos que ya no existen, permisos denegados)

**Cómo Funciona:**

```python
def pause_execution(self):
    parent = psutil.Process(self.run_robot_process.pid)

    # Suspender hijos primero
    for child in parent.children(recursive=True):
        child.suspend()

    # Suspender padre
    parent.suspend()
```

**Detalles por Plataforma:**
- **Windows**: Usa `SuspendThread` API internamente
- **Linux**: Envía señal `SIGSTOP` internamente
- **macOS**: Envía señal `SIGSTOP` internamente

---

### 2. Reanudar Ejecución (`resume_execution()`)

**Implementación Multiplataforma:**
- Utiliza `psutil.Process.resume()` en todas las plataformas
- Reanuda el proceso padre primero, luego los hijos
- Manejo robusto de errores

**Cómo Funciona:**

```python
def resume_execution(self):
    parent = psutil.Process(self.run_robot_process.pid)

    # Reanudar padre primero
    parent.resume()

    # Reanudar hijos después
    for child in parent.children(recursive=True):
        child.resume()
```

**Detalles por Plataforma:**
- **Windows**: Usa `ResumeThread` API internamente
- **Linux**: Envía señal `SIGCONT` internamente
- **macOS**: Envía señal `SIGCONT` internamente

---

### 3. Detener Ejecución (`stop_execution()`)

**Implementación Multiplataforma:**
- Utiliza `psutil.Process.terminate()` y `.kill()` en todas las plataformas
- Implementa terminación grácil con fallback a terminación forzada
- Manejo robusto de procesos huérfanos

**Estrategia de Terminación (3 pasos):**

1. **Terminación Grácil**: `terminate()` envía señal de terminación
2. **Espera**: 3 segundos de timeout para que el proceso termine
3. **Terminación Forzada**: `kill()` fuerza la terminación si aún está corriendo

**Cómo Funciona:**

```python
def stop_execution(self):
    parent = psutil.Process(self.run_robot_process.pid)
    children = parent.children(recursive=True)

    # Paso 1: Terminar grácilmente
    for child in children:
        child.terminate()
    parent.terminate()

    # Paso 2: Esperar
    try:
        parent.wait(timeout=3)
    except psutil.TimeoutExpired:
        # Paso 3: Forzar terminación
        for child in children:
            if child.is_running():
                child.kill()
        if parent.is_running():
            parent.kill()
```

**Detalles por Plataforma:**
- **Windows**:
  - `terminate()` usa `TerminateProcess` API
  - `kill()` usa `TerminateProcess` con force
- **Linux**:
  - `terminate()` envía `SIGTERM`
  - `kill()` envía `SIGKILL`
- **macOS**:
  - `terminate()` envía `SIGTERM`
  - `kill()` envía `SIGKILL`

---

## Ventajas de Usar psutil

### Antes (código dependiente de plataforma):

```python
# ❌ Código antiguo - dependiente de plataforma
if platform.system() == 'Windows':
    p = psutil.Process(self.run_robot_process.pid)
    p.suspend()
else:
    os.killpg(self.run_robot_process.pid, signal.SIGSTOP)  # No funciona en todos los casos
```

**Problemas:**
- Necesita `if/else` para cada plataforma
- `os.killpg()` requiere grupos de procesos (no siempre disponibles)
- Difícil de mantener y probar
- No maneja procesos hijos de manera consistente

### Después (código multiplataforma):

```python
# ✅ Código nuevo - multiplataforma
parent = psutil.Process(self.run_robot_process.pid)
children = parent.children(recursive=True)

for child in children:
    child.suspend()
parent.suspend()
```

**Ventajas:**
- Un solo código para todas las plataformas
- `psutil` maneja las diferencias internas
- Fácil de mantener y entender
- Manejo consistente de procesos hijos
- Mejor manejo de errores

---

## Manejo de Errores

Todas las funciones multiplataforma manejan estos errores:

| Error | Descripción | Acción |
|-------|-------------|--------|
| `psutil.NoSuchProcess` | El proceso ya no existe | Se captura y registra warning |
| `psutil.AccessDenied` | Sin permisos para el proceso | Se captura y registra warning |
| `psutil.TimeoutExpired` | Timeout al esperar terminación | Se fuerza kill |

**Ejemplo de Manejo:**

```python
try:
    child.suspend()
except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
    print(f"Warning: Could not suspend child process {child.pid}: {e}")
```

---

## Consideraciones Especiales por Plataforma

### Windows

1. **Grupos de Procesos**: No usa `os.killpg()` ya que Windows no tiene el concepto de grupos de procesos de la misma manera
2. **Terminación**: `TerminateProcess` es más agresivo que `SIGTERM` en Unix
3. **Permisos**: Requiere permisos de administrador para algunos procesos del sistema

### Linux

1. **Señales**: Soporta todas las señales POSIX estándar
2. **Grupos de Procesos**: Totalmente soportados pero no necesarios con psutil
3. **Zombies**: psutil maneja automáticamente procesos zombie

### macOS

1. **Fork Safety**: Requiere `OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES` para Gunicorn
2. **Señales**: Similar a Linux con señales POSIX
3. **Sandboxing**: Puede requerir permisos adicionales en versiones recientes

---

## Dependencias

### psutil

**Versión Requerida**: >= 5.9.0

```bash
pip install psutil>=5.9.0
```

**Capacidades Multiplataforma de psutil:**

| Función | Windows | Linux | macOS |
|---------|---------|-------|-------|
| `Process.suspend()` | ✅ | ✅ | ✅ |
| `Process.resume()` | ✅ | ✅ | ✅ |
| `Process.terminate()` | ✅ | ✅ | ✅ |
| `Process.kill()` | ✅ | ✅ | ✅ |
| `Process.children()` | ✅ | ✅ | ✅ |
| `Process.wait()` | ✅ | ✅ | ✅ |

---

## Testing

### Pruebas Recomendadas por Plataforma

**Windows:**
```powershell
# Ejecutar robot de prueba
python app.py

# En otra terminal, probar pause/resume/stop
curl -k https://127.0.0.1:5055/pause
curl -k https://127.0.0.1:5055/resume
curl -k https://127.0.0.1:5055/stop
```

**Linux/macOS:**
```bash
# Ejecutar robot de prueba
python3 app.py

# En otra terminal, probar pause/resume/stop
curl -k https://127.0.0.1:5055/pause
curl -k https://127.0.0.1:5055/resume
curl -k https://127.0.0.1:5055/stop
```

### Verificar Procesos

**Windows:**
```powershell
Get-Process python
```

**Linux/macOS:**
```bash
ps aux | grep python
```

---

## Mejoras Futuras

1. **Logs Estructurados**: Agregar logging detallado de operaciones de proceso
2. **Métricas**: Registrar tiempo de respuesta de pause/resume/stop
3. **Health Checks**: Verificar estado de procesos periódicamente
4. **Recuperación Automática**: Reiniciar procesos si se detectan problemas
5. **Limpieza de Zombies**: Implementar limpieza automática de procesos zombie

---

## Recursos

- [Documentación psutil](https://psutil.readthedocs.io/)
- [Señales POSIX](https://man7.org/linux/man-pages/man7/signal.7.html)
- [Windows Process API](https://learn.microsoft.com/en-us/windows/win32/procthread/process-and-thread-functions)

---

## Troubleshooting

### Problema: "Access Denied" al pausar/detener

**Windows:**
```powershell
# Ejecutar como Administrador
```

**Linux/macOS:**
```bash
# Verificar permisos
ps aux | grep python
# Ejecutar con sudo si es necesario (no recomendado para producción)
```

### Problema: Procesos no terminan

**Solución:**
- El timeout de 3 segundos puede no ser suficiente para procesos complejos
- Modificar `parent.wait(timeout=3)` a un valor mayor en `robot.py:264`

### Problema: Procesos huérfanos quedan corriendo

**Windows:**
```powershell
Get-Process python | Stop-Process -Force
```

**Linux/macOS:**
```bash
pkill -9 python
```

---

**Última Actualización**: 2025-11-19
**Versión del Documento**: 1.0