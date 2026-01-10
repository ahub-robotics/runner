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


def kill_process(pid, force=False):
    """
    Mata un proceso de forma simple y directa.

    Args:
        pid (int): PID del proceso a matar
        force (bool): Si True, usa SIGKILL en lugar de SIGTERM

    Returns:
        bool: True si el proceso fue terminado, False si no
    """
    try:
        if platform.system() == 'Windows':
            # En Windows, usar taskkill
            cmd = ['taskkill', '/PID', str(pid)]
            if force:
                cmd.insert(1, '/F')
            subprocess.run(cmd, capture_output=True, timeout=5)
        else:
            # En Linux/macOS, usar kill directo
            sig = signal.SIGKILL if force else signal.SIGTERM
            os.kill(pid, sig)

        return True

    except (ProcessLookupError, PermissionError):
        # Proceso ya no existe o no tenemos permisos
        return True
    except subprocess.TimeoutExpired:
        print(f"   ⚠️  Timeout matando PID {pid}")
        return False
    except Exception as e:
        print(f"   ⚠️  Error con PID {pid}: {e}")
        return False
