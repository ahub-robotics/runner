import json
from robot import Runner
import os


class Server(Runner):
    def __init__(self, kwargs):
        super().__init__(**kwargs)
        self.data = None
        self.thread = None
        self.status = "closed"

    def run(self, data):
        self.data = data
        self.set_robot(self.data)
        self.send_log("Execution Started")
        self.copy_repo()
        self.run_robot()
        self.status = "free"

    def pause(self):
        self.status = "paused"
        try:
            self.pause_execution()
        except:
            print("Unable to pause execution.")

    def resume(self):
        self.status = "running"
        try:
            self.resume_execution()
        except:
            print("Unable to pause resume.")

    def stop(self):
        self.status = "free"
        try:
            self.stop_execution()
        except:
            print("Unable to stop execution.")
