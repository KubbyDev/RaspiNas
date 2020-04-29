import os

# Config -----------------------------------------------------------------------

logFile = None # Initialised by main.py

# Code -------------------------------------------------------------------------

# Returns a list with the path of all the files in the given folder
def get_all_files(folder):
    logFile.write("I: Scanning local directory...\r\n")
    res = []
    for f in os.listdir(folder):
        abspath = os.path.join(folder, f)
        if os.path.isfile(abspath):
            res.append((f, os.path.getsize(abspath)))
    logFile.write("I: Found " + str(len(res)) + " files in the local directory\r\n")
    return res
        
