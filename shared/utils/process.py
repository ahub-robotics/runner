"""
Process Management Utilities.

Provides functions for managing server processes:
    - find_gunicorn_processes: Find all running Gunicorn processes
    - find_processes_on_port: Find processes listening on a specific port (cross-platform)
    - kill_process: Terminate a process gracefully or forcefully
"""
import os
import signal
import subprocess
import platform


def find_processes_on_port(port):
    """
    Encuentra procesos escuchando en un puerto específico (multiplataforma).

    Esta función funciona en Windows, Linux y macOS:
    - Windows: usa netstat
    - Linux/macOS: usa lsof

    Args:
        port (int): Puerto a verificar

    Returns:
        list: Lista de PIDs de procesos escuchando en el puerto
    """
    pids = []

    try:
        if platform.system() == 'Windows':
            # Windows: usar netstat
            # netstat -ano muestra todas las conexiones con PIDs
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Buscar líneas que contengan el puerto en LISTENING
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    # El PID está al final de la línea
                    parts = line.split()
                    if parts:
                        try:
                            pid = int(parts[-1])
                            if pid not in pids:
                                pids.append(pid)
                        except (ValueError, IndexError):
                            pass

        else:
            # Linux/macOS: usar lsof
            result = subprocess.run(
                ['lsof', '-t', '-i', f':{port}', '-sTCP:LISTEN'],
                capture_output=True,
                text=True,
                timeout=5
            )

            for pid_str in result.stdout.strip().split('\n'):
                if pid_str:
                    try:
                        pids.append(int(pid_str))
                    except ValueError:
                        pass

    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        # lsof no existe o timeout
        pass
    except Exception as e:
        print(f"⚠️  Error buscando procesos en puerto {port}: {e}")

    return pids


def find_gunicorn_processes():
    """
    Encuentra todos los procesos de Gunicorn corriendo.

    Returns:
        list: Lista de PIDs de procesos de Gunicorn
    """
    pids = set()

    try:
        if platform.system() == 'Windows':
            # En Windows, buscar procesos python
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'],
                capture_output=True,
                text=True,
                timeout=10
            )
            for line in result.stdout.split('\n'):
                if 'python' in line.lower():
                    parts = line.split(',')
                    if len(parts) >= 2:
                        pid_str = parts[1].strip('"')
                        try:
                            pids.add(int(pid_str))
                        except ValueError:
                            pass
        else:
            # En Linux/macOS, buscar procesos relacionados con gunicorn
            # Método 1: Buscar directamente "gunicorn"
            try:
                result = subprocess.run(
                    ['pgrep', '-f', 'gunicorn'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                for pid_str in result.stdout.strip().split('\n'):
                    if pid_str:
                        try:
                            pids.add(int(pid_str))
                        except ValueError:
                            pass
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

            # Método 2: Buscar "run.py --server-only" o "cli.run_server"
            for pattern in ['run.py', 'cli.run_server', 'api.wsgi']:
                try:
                    result = subprocess.run(
                        ['pgrep', '-f', pattern],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    for pid_str in result.stdout.strip().split('\n'):
                        if pid_str:
                            try:
                                pids.add(int(pid_str))
                            except ValueError:
                                pass
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass

            # Método 3: Buscar procesos escuchando en puertos comunes (5001, 5055)
            for port in [5001, 5055]:
                port_pids = find_processes_on_port(port)
                pids.update(port_pids)

    except subprocess.TimeoutExpired:
        print(f"⚠️  Timeout buscando procesos")
    except Exception as e:
        print(f"⚠️  Error buscando procesos: {e}")

    return list(pids)


def is_cloudflared_running():
    """
    Verifica si cloudflared tunnel está corriendo (multiplataforma).

    Esta función funciona en Windows, Linux y macOS:
    - Windows: usa tasklist
    - Linux/macOS: usa pgrep

    Returns:
        bool: True si cloudflared está corriendo, False si no
    """
    try:
        if platform.system() == 'Windows':
            # Windows: usar tasklist para buscar cloudflared.exe
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq cloudflared.exe', '/FO', 'CSV'],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Verificar si cloudflared aparece en la salida
            # La salida incluye header y líneas con el proceso
            lines = result.stdout.strip().split('\n')
            # Si hay más de 1 línea (header + proceso), cloudflared está corriendo
            return len(lines) > 1 and 'cloudflared.exe' in result.stdout.lower()

        else:
            # Linux/macOS: usar pgrep
            result = subprocess.run(
                ['pgrep', '-f', 'cloudflared tunnel run'],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Si pgrep retorna algo, el proceso está corriendo
            return bool(result.stdout.strip())

    except (subprocess.TimeoutExpired, FileNotFoundError):
        # Comando no existe o timeout - asumir que no está corriendo
        return False
    except Exception as e:
        print(f"⚠️  Error verificando cloudflared: {e}")
        return False


def find_cloudflared_processes():
    """
    Encuentra todos los procesos de cloudflared corriendo (multiplataforma).

    Returns:
        list: Lista de PIDs de procesos de cloudflared
    """
    pids = []

    try:
        if platform.system() == 'Windows':
            # Windows: usar tasklist
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq cloudflared.exe', '/FO', 'CSV'],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Parsear salida CSV
            for line in result.stdout.split('\n'):
                if 'cloudflared.exe' in line.lower():
                    parts = line.split(',')
                    if len(parts) >= 2:
                        pid_str = parts[1].strip('"')
                        try:
                            pids.append(int(pid_str))
                        except ValueError:
                            pass

        else:
            # Linux/macOS: usar pgrep
            result = subprocess.run(
                ['pgrep', '-f', 'cloudflared'],
                capture_output=True,
                text=True,
                timeout=5
            )

            for pid_str in result.stdout.strip().split('\n'):
                if pid_str:
                    try:
                        pids.append(int(pid_str))
                    except ValueError:
                        pass

    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    except Exception as e:
        print(f"⚠️  Error buscando procesos cloudflared: {e}")

    return pids


def kill_process(pid, force=True):
    """
    Mata un proceso de forma simple y directa.

    Args:
        pid (int): PID del proceso a matar
        force (bool): Si True, usa SIGKILL/taskkill /F (default: True)

    Returns:
        bool: True si el proceso fue terminado, False si no
    """
    try:
        if platform.system() == 'Windows':
            # En Windows, usar taskkill con /F (force) por defecto
            # Esto es necesario para procesos como cloudflared que no responden a SIGTERM
            cmd = ['taskkill', '/PID', str(pid)]
            if force:
                cmd.append('/F')

            result = subprocess.run(cmd, capture_output=True, timeout=5, text=True)

            # Verificar si se ejecutó correctamente
            if result.returncode == 0:
                print(f"   ✅ Proceso {pid} terminado correctamente")
                return True
            else:
                # Si falló, puede ser que el proceso ya no existe (lo cual es OK)
                if 'not found' in result.stderr.lower() or 'no se encuentra' in result.stderr.lower():
                    print(f"   ℹ️  Proceso {pid} ya no existe")
                    return True
                else:
                    print(f"   ⚠️  Error terminando proceso {pid}: {result.stderr}")
                    return False
        else:
            # En Linux/macOS, usar kill directo
            sig = signal.SIGKILL if force else signal.SIGTERM
            os.kill(pid, sig)
            print(f"   ✅ Proceso {pid} terminado con señal {sig}")
            return True

    except (ProcessLookupError, PermissionError):
        # Proceso ya no existe o no tenemos permisos
        print(f"   ℹ️  Proceso {pid} ya no existe o no hay permisos")
        return True
    except subprocess.TimeoutExpired:
        print(f"   ⚠️  Timeout matando PID {pid}")
        return False
    except Exception as e:
        print(f"   ⚠️  Error con PID {pid}: {e}")
        return False
