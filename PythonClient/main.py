import server
import localdir
from os.path import join

# Config -----------------------------------------------------------------------

memesDir = "memes"
backupDir = "backup"
configFile = "client.conf"

# Global variables -------------------------------------------------------------

# This holds the default config. Overwritten by the contents of the config file
config = {
    "server_ip":"192.168.1.44",
    "username":"pi",
    "password":"", # Has priority on passwordFile if given
    "password_file":"password",
    "log_file":"client.log",
    "local_dir":"",
}
logFile = None

# Tools ------------------------------------------------------------------------

# Reads the config file and extracts the values
def readConfig():
    global config
    global configFile
    f = open(configFile, "r")
    lines = f.read().splitlines()
    for line in lines:
        index = line.find('=')
        if index == -1: continue
        config[line[:index]] = line[index+1:]
    f.close()

def contents(file):
    f = open(file, "r")
    password = f.read()
    f.close()
    return password

# Code -------------------------------------------------------------------------

# Reads and apply the config file
readConfig()
logFile = open(config['log_file'], "w+", newline="\n")
server.logFile = logFile
localdir.logFile = logFile

# Connects to the server
ip = config['server_ip']
username = config['username']
password = config['password']
if not password: password = contents(config['password_file'])
server.connect(ip, username, password)

# Gets the list of files on the server folder and in the local folder
localfiles = localdir.get_all_files(config['local_dir'])
server.change_directory(memesDir)
serverfiles = server.list_files()

# Downloads every file that is on the server but not in the local folder
for file in serverfiles:
    if not file in localfiles:
        server.fetch_file(file[0], join(config['local_dir'], file[0]))

# Uploads everyfile that is in the local folder but not on the server
for file in localfiles:
    if not file in serverfiles:
        server.send_file(join(config['local_dir'], file[0]))

# Exits
server.disconnect()
logFile.close()
