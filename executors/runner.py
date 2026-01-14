"""
Robot Runner - Módulo de Ejecución de Robots

Este módulo maneja la ejecución de robots de automatización de manera multiplataforma.
Compatible con Windows, Linux y macOS.

Las funciones de control de procesos (pause, resume, stop) utilizan psutil para
garantizar compatibilidad completa entre plataformas.
"""
import base64
import datetime
import random
import string
import subprocess
import sys
import platform
import time

import git
import psutil
from git import Repo
import requests
import os


class Robot:
    def __init__(self, data):
        if not ".git" in data['repo_url']:
            self.repoUrl = data['repo_url'] + '.git'
        else:
            self.repoUrl = data['repo_url']
        self.RobotId = data['RobotId']
        self.RobotName = data['Name']

class Runner:
    def __init__(self, **kwargs):

        self.remote = None
        self.robot_id = None
        self.token = None
        self.robot = None
        self.execution_id = None
        self.robot_folder = None
        self.robot_params = None
        self.run_robot_process = None
        self.branch = None
        self.url = self.clean_url(kwargs.get("url","https://robot-console-a73e07ff7a0d.herokuapp.com/"))
        self.machine_id = kwargs.get("machine_id")
        self.license_key = kwargs.get("license_key")
        self.folder = kwargs.get("folder")
        self.server = kwargs.get("server")
        self.token = kwargs.get("token")
        self.ip = kwargs.get("ip", os.popen('curl -s ifconfig.me').readline())
        self.headers = {'Authorization': f'Token {self.token}'}
        self.http_protocol = self.__get_http_protocol()
        self.port = kwargs.get("port", 5055)

        # Redis state manager (se inyectará desde Server)
        self.redis_state = None


    @staticmethod
    def clean_url(url):
        """
        This method is used to clean the url of the robot manager console API.
        """
        if "https://" in url:
            url = url.replace("https://", "")
        elif "http://" in url:
            url = url.replace("http://", "")
        if url[-1] == "/":
            url = url[:-1]
        return url

    def __get_http_protocol(self):
        """
        This method is used to get the protocol of the iBott API.
        Returns:
            http_protocol: str
        """
        if "https://" in self.url:
            return "https://"
        return "http://"

    def set_robot_folder(self):
        """
        This method is used to set the folder of the robot
        where the robot will be installed.
        """
        self.robot_folder = f"{self.folder}/{self.robot_id}"



    def set_robo_params(self, params):
        """
        This method is used to set the robot parameters sent from the robot manager console.
        """
        if len(params) > 0:
            for key in params:
                string = params[key]
                if "base64" in string:
                    try:
                        # Remove any whitespace characters like newlines, spaces, etc.
                        string = string.strip()
                        base = string.split(",")[-1]
                        filename = string.split(",")[0]
                        file = base64.b64decode(base, validate=True)
                        folder = self.robot_folder
                        f = open(os.path.join(folder, filename), "wb")
                        f.write(file)
                        f.close()
                        params[key] = os.path.join(folder, filename)
                    except Exception as e:
                        print(e)
        return params

    def set_robot(self, data):
        """
        This method is used to set the robot.
        """
        self.robot_id = data['robot']
        self.execution_id = data['execution']
        self.branch = data["branch"]
        self.get_robot_data()
        self.set_robot_folder()
        if data['params']:
            self.robot_params = self.set_robo_params(data['params'])
        else:
            self.robot_params = "None"


    def set_machine_ip(self, status='free'):
        """
        This method is used to set the machine ip and status

        Args:
            status (str): Estado de la máquina ('free', 'closed', 'running', 'blocked')
        """
        self.headers = {'Authorization': f'Token {self.token}'}
        endpoint = f"{self.http_protocol}{self.url}/api/machines/{self.machine_id}/set_machine/"
        data = {'LicenseKey': self.license_key, "ipAddress": self.ip, 'port': self.port, 'status': status}
        try:
            request = requests.put(endpoint, data, headers=self.headers)
        except Exception as e:
            raise ConnectionError(e)

        if request.status_code != 200:
            raise ConnectionError(request.text)

    def get_robot_data(self):
        """
        This method is used to get the robot data.
        """
        endpoint = f'{self.http_protocol}{self.url}/api/robots/{self.robot_id}'
        RobotData = requests.get(endpoint, headers=self.headers)
        self.robot = Robot(RobotData.json())
        return self.robot



    def pause_execution(self):
        """
        Pausa la ejecución del robot de manera multiplataforma.

        Funciona en:
        - Windows: Usa psutil.Process.suspend() en todos los procesos de la jerarquía
        - Linux: Usa psutil.Process.suspend()
        - macOS: Usa psutil.Process.suspend()

        Nota: Suspende el proceso principal y todos sus hijos recursivamente.
        """
        if self.run_robot_process:
            if self.run_robot_process and self.run_robot_process.poll() is None:
                try:
                    # Obtener el proceso padre (puede ser cmd.exe en Windows si se usa shell=True)
                    parent = psutil.Process(self.run_robot_process.pid)

                    # Recolectar TODOS los procesos a suspender (padre + hijos)
                    processes_to_suspend = []

                    # Agregar proceso padre
                    processes_to_suspend.append(parent)

                    # Obtener hijos recursivamente
                    try:
                        children = parent.children(recursive=True)
                        processes_to_suspend.extend(children)
                        print(f"[PAUSE] Encontrados {len(children)} procesos hijos")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                    # En Windows, esperamos un momento para asegurar que todos los procesos estén iniciados
                    if platform.system() == 'Windows':
                        time.sleep(0.1)
                        # Volver a verificar por si aparecieron más hijos
                        try:
                            children = parent.children(recursive=True)
                            # Agregar solo nuevos procesos
                            for child in children:
                                if child not in processes_to_suspend:
                                    processes_to_suspend.append(child)
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                    print(f"[PAUSE] Total de procesos a suspender: {len(processes_to_suspend)}")

                    # Suspender todos los procesos (de hijos a padres)
                    suspended_count = 0
                    for proc in reversed(processes_to_suspend):  # reversed para suspender hijos primero
                        try:
                            # Verificar que el proceso aún existe antes de suspender
                            if proc.is_running():
                                proc.suspend()
                                suspended_count += 1
                                print(f"[PAUSE] Suspendido PID {proc.pid} ({proc.name()})")
                        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired) as e:
                            print(f"Warning: No se pudo suspender proceso {proc.pid}: {e}")

                    print(f"[PAUSE] ✅ Total suspendidos: {suspended_count}/{len(processes_to_suspend)}")
                    self.send_log(f"Execution Paused ({suspended_count} processes)")

                    # Actualizar estado en Redis para confirmar que se pausó exitosamente
                    if hasattr(self, 'redis_state') and self.redis_state and self.execution_id:
                        self.redis_state.save_execution_state(self.execution_id, {
                            'status': 'paused',
                            'paused_at': time.time()
                        })
                        print(f"[ROBOT] ✅ Estado actualizado en Redis: paused")

                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    error_msg = f"Error pausing execution: {e}"
                    self.send_log(error_msg, "syex")
                    raise Exception(error_msg)


    def resume_execution(self):
        """
        Reanuda la ejecución del robot de manera multiplataforma.

        Funciona en:
        - Windows: Usa psutil.Process.resume() en todos los procesos de la jerarquía
        - Linux: Usa psutil.Process.resume()
        - macOS: Usa psutil.Process.resume()

        Nota: Reanuda el proceso padre primero y luego todos sus hijos recursivamente.
        """
        if self.run_robot_process:
            if self.run_robot_process and self.run_robot_process.poll() is None:
                try:
                    # Obtener el proceso padre (puede ser cmd.exe en Windows si se usa shell=True)
                    parent = psutil.Process(self.run_robot_process.pid)

                    # Recolectar TODOS los procesos a reanudar (padre + hijos)
                    processes_to_resume = []

                    # Agregar proceso padre
                    processes_to_resume.append(parent)

                    # Obtener hijos recursivamente
                    try:
                        children = parent.children(recursive=True)
                        processes_to_resume.extend(children)
                        print(f"[RESUME] Encontrados {len(children)} procesos hijos")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                    print(f"[RESUME] Total de procesos a reanudar: {len(processes_to_resume)}")

                    # Reanudar todos los procesos (de padres a hijos)
                    resumed_count = 0
                    for proc in processes_to_resume:  # padre primero, luego hijos
                        try:
                            # Verificar que el proceso aún existe antes de reanudar
                            if proc.is_running():
                                proc.resume()
                                resumed_count += 1
                                print(f"[RESUME] Reanudado PID {proc.pid} ({proc.name()})")
                        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired) as e:
                            print(f"Warning: No se pudo reanudar proceso {proc.pid}: {e}")

                    print(f"[RESUME] ✅ Total reanudados: {resumed_count}/{len(processes_to_resume)}")
                    self.send_log(f"Execution Resumed ({resumed_count} processes)")

                    # Actualizar estado en Redis para confirmar que se reanudó exitosamente
                    if hasattr(self, 'redis_state') and self.redis_state and self.execution_id:
                        self.redis_state.save_execution_state(self.execution_id, {
                            'status': 'running',
                            'resumed_at': time.time()
                        })
                        print(f"[ROBOT] ✅ Estado actualizado en Redis: running")

                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    error_msg = f"Error resuming execution: {e}"
                    print(error_msg)
                    self.send_log(error_msg, "syex")
                    raise Exception(error_msg)

    def stop_execution(self):
        """
        Detiene la ejecución del robot de manera multiplataforma.

        Funciona en:
        - Windows: Usa psutil.Process.terminate() y luego .kill() si es necesario
        - Linux: Usa psutil.Process.terminate() y luego .kill() si es necesario
        - macOS: Usa psutil.Process.terminate() y luego .kill() si es necesario

        Estrategia:
        1. Guarda PIDs de todos los descendientes (incluyendo chromedriver/chrome)
        2. Intenta terminar grácilmente (SIGTERM en Unix, TerminateProcess en Windows)
        3. Espera 3 segundos para que el proceso termine
        4. Si no termina, fuerza la terminación (SIGKILL)
        5. Verifica PIDs guardados y termina huérfanos
        6. Busca chromedriver/chrome por nombre como último recurso

        Nota: Detiene el proceso principal y todos sus hijos recursivamente.
        También detecta y termina procesos chromedriver que puedan quedar huérfanos.
        """
        descendant_pids = set()  # Guardar PIDs fuera del if para uso posterior

        if self.run_robot_process:
            if self.run_robot_process.poll() is None:
                try:
                    # Usar psutil en todas las plataformas para consistencia
                    parent = psutil.Process(self.run_robot_process.pid)

                    # IMPORTANTE: Obtener TODOS los descendientes y guardar PIDs + info
                    # Esto incluye chromedriver, chrome, y cualquier otro hijo
                    children = parent.children(recursive=True)

                    # Guardar PIDs y nombres para rastreo posterior
                    descendant_info = {}
                    for child in children:
                        try:
                            descendant_info[child.pid] = {
                                'name': child.name(),
                                'cmdline': child.cmdline()
                            }
                            descendant_pids.add(child.pid)
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                    descendant_pids.add(parent.pid)
                    print(f"[STOP] Detectados {len(descendant_pids)} procesos a terminar")

                    # Paso 1: Intentar terminación grácil
                    # Terminar procesos hijos primero (de abajo hacia arriba)
                    for child in children:
                        try:
                            child.terminate()
                        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                            print(f"Warning: Could not terminate child process {child.pid}: {e}")

                    # Terminar proceso padre
                    parent.terminate()

                    # Paso 2: Esperar a que terminen grácilmente (timeout de 3 segundos)
                    try:
                        parent.wait(timeout=3)
                        self.send_log("Execution Stopped")
                    except psutil.TimeoutExpired:
                        # Paso 3: Si no terminó, forzar terminación
                        print("[STOP] Process did not terminate gracefully, forcing kill...")

                        # IMPORTANTE: Refrescar lista de hijos antes de force kill
                        # (pueden haber nuevos procesos o el árbol puede haber cambiado)
                        try:
                            children = parent.children(recursive=True)
                        except psutil.NoSuchProcess:
                            # El padre ya no existe, obtener hijos de los PIDs conocidos
                            children = []
                            for pid in list(descendant_pids):
                                try:
                                    proc = psutil.Process(pid)
                                    if proc.is_running():
                                        children.append(proc)
                                        # También agregar sus hijos
                                        children.extend(proc.children(recursive=True))
                                except (psutil.NoSuchProcess, psutil.AccessDenied):
                                    pass

                        # Forzar terminación de procesos hijos
                        for child in children:
                            try:
                                if child.is_running():
                                    child.kill()
                            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                                print(f"Warning: Could not kill child process {child.pid}: {e}")

                        # Forzar terminación del proceso padre
                        try:
                            if parent.is_running():
                                parent.kill()
                        except psutil.NoSuchProcess:
                            pass

                        self.send_log("Execution Forcefully Stopped")

                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    error_msg = f"Error stopping execution: {e}"
                    print(error_msg)
                    self.send_log(error_msg, "syex")
                    # No lanzar excepción aquí, solo registrar el error

        # Paso 4: CLEANUP - Verificar PIDs guardados y terminar huérfanos
        # Esperar un momento para que los procesos terminen
        time.sleep(0.5)

        killed_count = 0

        print("[CLEANUP] Verificando PIDs de descendientes guardados...")
        for pid in descendant_pids:
            try:
                proc = psutil.Process(pid)
                if proc.is_running():
                    proc_name = proc.name()
                    print(f"[CLEANUP] Terminando PID guardado: {pid} ({proc_name})")
                    proc.kill()
                    killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass  # Proceso ya terminó o no tenemos acceso

        # Paso 5: CLEANUP FINAL - Buscar chromedriver/chrome por nombre como último recurso
        print("[CLEANUP] Buscando chromedriver/chrome por nombre...")
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                try:
                    proc_name = proc.info['name'].lower()
                    cmdline = proc.info['cmdline'] or []
                    cmdline_str = ' '.join(cmdline).lower()

                    # Detectar chromedriver o chrome en modo automation
                    is_automation = any([
                        'chromedriver' in proc_name,
                        ('chrome' in proc_name or 'chromium' in proc_name) and any(
                            flag in cmdline_str for flag in [
                                '--test-type',
                                '--enable-automation',
                                '--remote-debugging-port',
                                'chromedriver'
                            ]
                        ),
                    ])

                    # Si es un proceso de automation y no está en nuestra lista (huérfano nuevo)
                    if is_automation and proc.info['pid'] not in descendant_pids:
                        # Verificar que sea reciente (creado en los últimos 10 minutos)
                        # para evitar matar chromes de otros robots
                        import time as time_module
                        process_age = time_module.time() - proc.info['create_time']
                        if process_age < 600:  # 10 minutos
                            print(f"[CLEANUP] Terminando proceso de automation huérfano: {proc.info['pid']} ({proc_name})")
                            proc.kill()
                            killed_count += 1

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

        except Exception as e:
            print(f"[CLEANUP] ⚠️  Error durante búsqueda por nombre: {e}")

        if killed_count > 0:
            print(f"[CLEANUP] ✅ {killed_count} proceso(s) huérfano(s) terminado(s)")
        else:
            print("[CLEANUP] ✅ No se encontraron procesos huérfanos")

        self.run_robot_process = None



    def copy_repo(self):
        """ This method is used to copy the robot repository. """

        endpoint = f'{self.http_protocol}{self.url}/api/git'
        gitData = requests.get(endpoint, headers=self.headers)
        git_token = gitData.json()[0]['git_token']
        account = self.robot.repoUrl.split("/")[-2]
        repo = self.robot.repoUrl.split("/")[-1]
        self.remote = f"https://{git_token}:@github.com/{account}/{repo}"
        try:
            if os.path.exists(f"{self.robot_folder}/.git"):
                self.send_log(f"Pulling repo from {self.robot.repoUrl}")
                git.cmd.Git(self.robot_folder).pull(self.remote, self.branch)
                self.send_log("Repo pulled successfully")
            else:
                self.send_log(f"Cloning repo from {self.robot.repoUrl}")
                Repo.clone_from(self.remote, self.robot_folder, branch=self.branch)
                self.send_log("Repo cloned successfully")
        except Exception as e:
            self.send_log(e.__str__(), "syex")
            raise Exception(e)

    def run_robot(self):
        """
        Create a subprocess that run robot process with the given arguments.

        FASE 1: Setup (venv + dependencies)
        FASE 2: Callback "actually_started" a iBott Console
        FASE 3: Ejecución del robot
        """
        self.send_log("Running the process")
        args = {"RobotId": self.robot_id,
                "url": self.http_protocol + self.url,
                "token": self.token,
                "ExecutionId": self.execution_id,
                'params': self.robot_params}

        # FASE 1: Setup del entorno (venv + dependencias)
        # Esto puede tomar 5-10 segundos, por eso lo hacemos ANTES del callback
        self.send_log("Setting up virtual environment and dependencies")

        try:
            if platform.system() == 'Windows':
                setup_command = [
                    f"py -m venv {self.robot_folder}\\venv",
                    f"{self.robot_folder}\\venv\\Scripts\\activate",
                    f"\"{self.robot_folder}\\venv\\Scripts\\python.exe\" -m pip install -q -r \"{self.robot_folder}\\requirements.txt\""
                ]
                run_command = f"\"{self.robot_folder}\\venv\\Scripts\\python.exe\" \"{self.robot_folder}\\main.py\" \"{args}\""
            else:
                setup_command = [
                    f"python3 -m venv {self.robot_folder}/venv",
                    f"{self.robot_folder}/venv/bin/pip3 install -q -r {self.robot_folder}/requirements.txt"
                ]
                run_command = f"{self.robot_folder}/venv/bin/python {self.robot_folder}/main.py \"{args}\""

            # Ejecutar setup (puede tomar varios segundos)
            setup_cmd = " && ".join(setup_command)
            setup_process = subprocess.run(
                setup_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos máximo para setup
            )

            if setup_process.returncode != 0:
                error_msg = f"Setup failed: {setup_process.stderr}"
                self.send_log(error_msg, "syex")
                raise Exception(error_msg)

            self.send_log("Environment setup completed successfully")

        except subprocess.TimeoutExpired:
            error_msg = "Setup timeout: Dependencies installation took too long"
            self.send_log(error_msg, "syex")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Setup error: {str(e)}"
            self.send_log(error_msg, "syex")
            raise

        # FASE 2: Callback "actually_started" - El robot VA A INICIAR AHORA
        # Este es el momento PRECISO para notificar a iBott que el robot está por ejecutar
        try:
            self.send_log("Notifying iBott Console: Robot is about to start")
            endpoint = f'{self.http_protocol}{self.url}/api/executions/{self.execution_id}/set_status/'
            callback_data = {
                'status': 'working',
                'actually_started': True  # Flag especial que indica inicio real
            }
            response = requests.put(endpoint, data=callback_data, headers=self.headers, timeout=5)

            if response.status_code == 202:
                self.send_log("✓ iBott Console notified: Robot actually started")
            else:
                # No fatal, pero logear para debugging
                self.send_log(f"Warning: Callback returned status {response.status_code}", "log")
        except Exception as e:
            # El callback no debe bloquear la ejecución
            self.send_log(f"Warning: Could not send callback to iBott: {e}", "log")

        # FASE 3: Ejecutar el robot
        self.send_log("Starting robot execution")
        self.run_robot_process = subprocess.Popen(run_command,
                                                  shell=True,
                                                  bufsize=1,
                                                  stdout=subprocess.PIPE,
                                                  stderr=subprocess.STDOUT,
                                                  encoding='utf-8',
                                                  errors='replace'
                                                  )

        # Guardar PID en Redis si está disponible
        if hasattr(self, 'redis_state') and self.redis_state and self.execution_id:
            self.redis_state.save_execution_state(self.execution_id, {
                'pid': self.run_robot_process.pid
            })

        self.set_status("working")

        # Estado para pause/resume
        last_pause_check = time.time()
        PAUSE_CHECK_INTERVAL = 0.5  # Verificar cada 500ms para ser más reactivo

        # Configurar lectura no bloqueante para Unix
        import select
        import os

        if platform.system() != 'Windows':
            # En Unix, hacer el file descriptor no bloqueante
            import fcntl
            fd = self.run_robot_process.stdout.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        while True:
            # Verificar si el proceso terminó
            if self.run_robot_process.poll() is not None:
                # Leer cualquier output restante
                try:
                    remaining = self.run_robot_process.stdout.read()
                    if remaining:
                        for line in remaining.splitlines():
                            if line.strip():
                                if "error" in line.strip().lower():
                                    self.send_log(line.strip(), "syex")
                                else:
                                    self.send_log(line.strip())
                except:
                    pass
                break

            # Intentar leer output (no bloqueante en Unix)
            realtime_output = None

            if platform.system() != 'Windows':
                # Unix: usar select para verificar si hay datos disponibles
                ready, _, _ = select.select([self.run_robot_process.stdout], [], [], 0.1)
                if ready:
                    try:
                        realtime_output = self.run_robot_process.stdout.readline()
                    except:
                        pass
            else:
                # Windows: readline bloqueante pero con verificación frecuente de proceso
                # (Windows no soporta select en pipes)
                try:
                    # Usar un timeout simulado verificando el proceso frecuentemente
                    import threading
                    result = []

                    def read_line():
                        try:
                            line = self.run_robot_process.stdout.readline()
                            result.append(line)
                        except:
                            pass

                    thread = threading.Thread(target=read_line, daemon=True)
                    thread.start()
                    thread.join(timeout=0.1)

                    if result:
                        realtime_output = result[0]
                except:
                    pass

            # Procesar output si hay
            if realtime_output and realtime_output.strip():
                if "error" in realtime_output.strip().lower():
                    self.send_log(realtime_output.strip(), "syex")
                else:
                    self.send_log(realtime_output.strip())
                sys.stdout.flush()

            # Verificar periódicamente pause/resume desde Redis
            now = time.time()
            if now - last_pause_check >= PAUSE_CHECK_INTERVAL:
                last_pause_check = now

                if hasattr(self, 'redis_state') and self.redis_state and self.execution_id:
                    control = self.redis_state.get_pause_control(self.execution_id)

                    # Si se solicitó pausa
                    if control['pause_requested'] and not getattr(self, '_is_paused', False):
                        print(f"[ROBOT] Detectada solicitud de pausa")
                        try:
                            self.pause_execution()
                            self._is_paused = True
                        except Exception as e:
                            print(f"[ROBOT] Error al pausar: {e}")

                    # Si se solicitó reanudación
                    elif control['resume_requested'] and getattr(self, '_is_paused', False):
                        print(f"[ROBOT] Detectada solicitud de reanudación")
                        try:
                            self.resume_execution()
                            self._is_paused = False
                            self.redis_state.clear_pause_control(self.execution_id)
                        except Exception as e:
                            print(f"[ROBOT] Error al reanudar: {e}")

            # Pequeña pausa para no consumir CPU innecesariamente
            time.sleep(0.05)

        self.finish_execution()

        # Check if process exists and get its return code
        # IMPORTANTE: Guardar el returncode ANTES de limpiar el proceso
        # para que server.py pueda acceder a él
        if self.run_robot_process is not None:
            returncode = self.run_robot_process.returncode

            # Guardar returncode en variable de instancia para que server.py pueda acceder
            self.last_returncode = returncode
            print(f"[ROBOT] Exit code guardado: {returncode}")

            if returncode == 0:
                self.set_status("ok")
            elif returncode == 15:
                self.set_status("stopped")
            else:
                self.set_status("fail")
        else:
            # Process is None, something went wrong
            print("[ROBOT] ⚠️  Process is None, setting status to fail")
            self.last_returncode = 1  # Error
            self.set_status("fail")

        # Limpiar el proceso después de guardar el returncode
        self.run_robot_process = None


    def finish_execution(self):
        """
        finish robot execution and send the result to the server
        """

        self.robot_id = None
        self.send_log("Execution Finished")

    def set_status(self, status: str):
        """Set status of robot execution in the robot manager"""
        endpoint = f'{self.http_protocol}{self.url}/api/executions/{self.execution_id}/set_status/'
        requests.put(endpoint, data={'status': status}, headers=self.headers)

    def send_log(self, message, log_type="log"):
        """
        send log to robot manage console
        Arguments:
            message {string} -- message to send
            log_type {string} -- type of the log
        """

        endpoint = f'{self.http_protocol}{self.url}/api/logs/'

        log_data = {
            "LogType": log_type,
            "LogData": message,
            "ExecutionId": self.execution_id,
            "LogId": ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(64)),
            "DateTime": datetime.datetime.now()
        }
        try:
            requests.post(endpoint, log_data, headers=self.headers)
        except Exception as e:
            raise e
