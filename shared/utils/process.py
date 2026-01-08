"""
Process Management Utilities.

Provides functions for managing server processes:
    - find_gunicorn_processes: Find all running Gunicorn processes
    - kill_process: Terminate a process gracefully or forcefully
"""
import os
import signal
import subprocess
import platform


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
                try:
                    result = subprocess.run(
                        ['lsof', '-t', '-i', f':{port}', '-sTCP:LISTEN'],
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
