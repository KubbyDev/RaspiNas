import server
import localdir
import logfile
from logfile import log
from os.path import join

# Config -----------------------------------------------------------------------

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
    contents = f.read()
    f.close()
    return contents

# Code -------------------------------------------------------------------------

# Reads and apply the config file
readConfig()
logfile.start(config['log_file'])

# Connects to the server
ip = config['server_ip']
username = config['username']
password = config['password']
if not password: password = contents(config['password_file'])
server.connect(ip, username, password)

# Gets the list of files on the server folder and in the local folder
localfiles = localdir.get_all_files(config['local_dir'])
serverfiles = server.list_files()

# If a file have the same name on the client and the server but with different
# size, backups the file on the server and uploads the client's version
for lName, lSize in localfiles:
    for sName, sSize in serverfiles:
        if lName == sName and lSize != sSize:
            log("Backing up " + sName + "...")
            server.backup_file(sName)
            serverfiles.remove((sName, sSize))

# Downloads every file that is on the server but not in the local folder
for file in serverfiles:
    if not file in localfiles:
        log("Downloading " + file[0] + "...")
        server.fetch_file(file[0], join(config['local_dir'], file[0]))

# Uploads everyfile that is in the local folder but not on the server
for file in localfiles:
    if not file in serverfiles:
        log("Uploading " + file[0] + "...")
        server.send_file(join(config['local_dir'], file[0]))

# Exits
server.disconnect()
