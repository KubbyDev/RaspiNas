# Wrapper that calls the python program
# Don't forget to run AndroidWrapper\update_sources.bat to fetch the python program

from os.path import dirname
import os
import sync

# Adds or replaces the given property with the new value
def changeProperty(property, newValue):
    # Reads the current config file if it exists
    try:
        f = open("client.conf", "r")
        content = f.read()
        f.close()
    except:
        content = ""
    # Creates the new file content and adds all the lines except the ones that define the property
    res = []
    for line in content.splitlines():
        if not line.startswith(property + "="):
            res.append(line)
    # Adds the wanted property
    res.append(property + "=" + newValue)
    # Writes the lines back to the config file
    f = open("client.conf", "w+")
    for line in res:
        f.write(line+"\r\n")
    f.close()

def launch(localDir, logsDir):
    # Sets the working directory to the python scripts directory
    os.chdir(dirname(__file__))
    # Sets the local directory and the logs file in the config file
    changeProperty("local_dir", localDir)
    changeProperty("logs_file", logsDir+"/logs.txt")
    # Launches the main program
    sync.main("client.conf")