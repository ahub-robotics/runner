import base64
import datetime
import random
import signal
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
        self.port = kwargs.get("port", 8088)


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


    def set_machine_ip(self):
        """
        This method is used to set the machine ip
        """
        self.headers = {'Authorization': f'Token {self.token}'}
        endpoint = f"{self.http_protocol}{self.url}/api/machines/{self.machine_id}/set_machine/"
        data = {'LicenseKey': self.license_key, "ipAddress": self.ip, 'port': self.port, 'status': 'free'}
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
        """ This method is used to pause the execution. """
        if self.run_robot_process:
            if self.run_robot_process and self.run_robot_process.poll() is None:
                if platform.system() == 'Windows':
                    p = psutil.Process(self.run_robot_process.pid)
                    p.suspend()
                    for child in p.children(recursive=True):
                        child.suspend()
                else:
                    os.killpg(self.run_robot_process.pid, signal.SIGSTOP)

                self.send_log("Execution Paused")


    def resume_execution(self):
        """ This method is used to resume the execution. """
        if self.run_robot_process:
            if self.run_robot_process and self.run_robot_process.poll() is None:
                if platform.system() == 'Windows':
                    p = psutil.Process(self.run_robot_process.pid)
                    for child in p.children(recursive=True):
                        child.resume()
                    p.resume()
                else:
                    os.killpg(self.run_robot_process.pid, signal.SIGCONT)

                self.send_log("Execution Resumed")

    def stop_execution(self):
        """ This method is used to stop the execution. """
        if self.run_robot_process:
            if self.run_robot_process.poll() is None:
                if platform.system() == 'Windows':
                    p = psutil.Process(self.run_robot_process.pid)
                    for child in p.children(recursive=True):
                        child.kill()
                    p.kill()
                else:
                    os.killpg(self.run_robot_process.pid, signal.SIGKILL)
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
        Create a subprocess that run robot process with the given arguments
        """
        self.send_log("Running the process")
        args = {"RobotId": self.robot_id,
                "url": self.http_protocol + self.url,
                "token": self.token,
                "ExecutionId": self.execution_id,
                'params': self.robot_params}

        if platform.system() == 'Windows':
            #WINDOWS COMMAND
            command = [f"py -m venv {self.robot_folder}\\venv",
                       f"{self.robot_folder}\\venv\\Scripts\\activate",
                       f"py -m pip install -r \"{self.robot_folder}\\requirements.txt\"",
                       f"python \"{self.robot_folder}\\main.py\" \"{args}\""]

        else:
            #UNIX COMMAND
            command = [f"python3 -m venv {self.robot_folder}/venv",
                       f"{self.robot_folder}/venv/bin/pip3 install -r {self.robot_folder}/requirements.txt",
                       f"{self.robot_folder}/venv/bin/python {self.robot_folder}/main.py \"{args}\""]

        command = " && ".join(command)

        self.run_robot_process = subprocess.Popen(command,
                                                  shell=True,
                                                  bufsize=1,
                                                  stdout=subprocess.PIPE,
                                                  stderr=subprocess.STDOUT,
                                                  encoding='utf-8',
                                                  errors='replace',
                                                  creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                                                  )

        self.set_status("working")

        while True:
            #Get Realtime Output
            realtime_output = self.run_robot_process.stdout.readline()
            if realtime_output == '' and self.run_robot_process.poll() is not None:
                break
            if realtime_output:
                if "error" in realtime_output.strip().lower():
                    self.send_log(realtime_output.strip(), "syex")
                else:
                    self.send_log(realtime_output.strip())
                sys.stdout.flush()
        self.finish_execution()
        if self.run_robot_process.returncode == 0:
            self.set_status("ok")
        elif self.run_robot_process.returncode == 15:
            self.set_status("stopped")
        else:
            self.set_status("fail")

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
