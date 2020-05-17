import time
import threading

__path = "client.log"
__lock = threading.Lock()

# Adds a log line
def log(message, source="I: ", end=""):
    global __path
    global __lock
    __lock.acquire()
    f = open(__path, "a+", newline="\n")
    for line in message.splitlines():
        f.write(source + line + "\r\n")
    f.write(end)
    f.close()
    __lock.release()

def start(path=None):
    global __path
    if path != None: __path = path
    log("\r\n\r\n" + time.ctime(), source="")

