from os.path import dirname
import os
import sync

def changeLocalDir(localDir):
    # Reads the current config file if it exists
    try:
        f = open("client.conf", "r")
        content = f.read()
        f.close()
    except:
        content = ""
    # Splits the file in lines and updates the lines that define local_dir
    found = False
    lines = content.splitlines()
    for i in range(len(lines)):
        if lines[i].startswith("local_dir="):
            lines[i] = "local_dir=" + localDir
            found = True
    # If the local_dir was not defined, adds it
    if not found:
        lines.append("local_dir=" + localDir)
    # Writes the lines back to the config file
    f = open("client.conf", "w+")
    for line in lines:
        f.write(line+"\r\n")
    f.close()

def launch(localDir):
    # Sets the working directory to the python scripts directory
    os.chdir(dirname(__file__))
    # Sets the local directory in the config file
    changeLocalDir(localDir)
    # Launches the main program
    sync.main("client.conf")

# default working directory is /data/user/0/com.example.androidwrapper/files/chaquopy/AssetFinder/app