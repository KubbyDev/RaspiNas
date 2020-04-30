import time

__path = "client.log"

# Adds a log line
def log(message, source="I: ", end=""):
    global __path
    f = open(__path, "a+", newline="\n")
    for line in message.splitlines():
        f.write(source + line + "\r\n")
    f.write(end)
    f.close()

def start(path=None):
    global __path
    if path != None: __path = path
    log("\r\n\r\n" + time.ctime(), source="")
   
