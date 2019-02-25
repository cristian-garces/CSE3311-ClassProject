import threading
from pathlib import Path

login_logs_lock = threading.Semaphore()


class LoginLogger(threading.Thread):
    def __init__(self, msg=None, directory=None):
        threading.Thread.__init__(self)
        self.directory = directory or ""
        self.message = msg or "No error message provided."

    def run(self):
        with login_logs_lock:
            Path(self.directory).mkdir(parents=True, exist_ok=True)
            with open("{0}login.log".format(self.directory), mode="a+") as login_logs:
                login_logs.write(self.message)
