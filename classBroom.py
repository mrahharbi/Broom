
import psutil
class CPU:
    def __init__(self):
        self.cpu_percent= psutil.cpu_percent(interval=1)
        self.cpu_count = psutil.cpu_count(logical=False)
        self.cpu_status = psutil.cpu_stats()
    def time (self):
        return f"System Boot Time (seconds since epoch ): {psutil.boot_time()}"
    def usage(self):
        return f"CPU Usage (%): {self.cpu_percent}%"
    def info (self):
        return f"CPU Cross (%): {self.cpu_count}%"
    def status(self):
        return f"CPU Status (%): {self.cpu_status}"

class Memory:
    def __init__(self):
        self.virtual = psutil.virtual_memory().total
        self.free = psutil.virtual_memory().available
        self.used = psutil.virtual_memory().used
        self.percent = psutil.virtual_memory().percent
    def info (self):
        return f"Memory Usage (%): {self.percent}%"
    def status (self):
        return f"Memory Status (%): {self.percent}%"
    def usage (self):
        return f"Memory Usage (%): {self.percent}%"
    def free (self):
        return f"Memory Free (%): {self.free}%"


def user():
    return f"{psutil.users()}"

