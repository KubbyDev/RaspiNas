import server
import localdir
import logfile
from logfile import log
from os.path import join, isfile, realpath, commonprefix

# This script synchronises the local directory and the server
# Execute it with no argument and it will use the client.conf config file
# in the working directory. The first argument is given is the config file

# Config -----------------------------------------------------------------------

# This holds the default config. Overwritten by the contents of the config file
config = {
    "host":"raspberrypi.local",   # FTP server ip
    "username":"raspinas",        # FTP user name
    "password":"",                # FTP user password. Has priority on passwordFile if given
    "password_file":"password",   # File containing the FTP user password. The password field has priority if given
    "logs_file":"client.log",     # Logs file
    "local_dir":"LocalDir",       # Local location or the synchronised directory
}

# Tools ------------------------------------------------------------------------

# Reads the config file and extracts the values
def read_config(file):
    global config
    # Verifies that the file exists
    if not isfile(file):
        print("WARNING: Could not find the config file here " + file)
        print("Using default config values")
        return
    f = open(file, "r")
    lines = f.read().splitlines()
    # For each line of the file
    for line in lines:
        # Removes the comments
        if '#' in line: line = line[:line.find('#')]
        # If the line contains an =, processes it
        index = line.find('=')
        if index == -1: continue
        config[line[:index]] = line[index+1:]
    f.close()

# This function ensures that the file is in the local directory
# (to protect against directory traversal attacks. Ex: naming a file C:\test)
def is_in_local_dir(file):
    global config
    return commonprefix((realpath(file),config['local_dir'])) == config['local_dir']

# Code -------------------------------------------------------------------------

def main(configFile):
    global config

    # Reads and apply the config file
    read_config(configFile)
    logfile.start(config['logs_file'])

    # Connects to the server
    host = config['host']
    username = config['username']
    password = config['password']
    if not password:
        file = open(config['password_file'], "r")
        password = file.read()
        file.close()
    server.connect(host, username, password)

    # Gets the list of files on the server folder and in the local folder
    localfiles = localdir.get_all_files(config['local_dir'])
    serverfiles = server.list_files()

    # If a file have the same name on the client and the server but with different
    # size, backups the file on the server and uploads the client's version
    for lName, lSize in localfiles:
        for sName, sSize in serverfiles:
            if lName == sName and lSize != sSize:
                log("Backing up " + sName + "...")
                print("Backing up " + sName + "...")
                server.backup_file(sName)
                serverfiles.remove((sName, sSize))

    # Downloads every file that is on the server but not in the local folder
    for file in serverfiles:
        if not file in localfiles:
            log("Downloading " + file[0] + "...")
            print("Downloading " + file[0] + "...")
            filepath = join(config['local_dir'], file[0])
            if is_in_local_dir(filepath):
                server.fetch_file(file[0], filepath)
            # Protection against directory traversal
            else:
                log("Detected directory traversal attempt, aborting", "W: ")
                raise Exception("Detected directory traversal attempt\n" \
                                + filepath + " is not in the local directory")
 
    # Uploads everyfile that is in the local folder but not on the server
    for file in localfiles:
        if not file in serverfiles:
            log("Uploading " + file[0] + "...")
            print("Uploading " + file[0] + "...")
            server.send_file(join(config['local_dir'], file[0]))

    # Exits
    server.disconnect()
    print("Server and local dir are now synchronised!")
