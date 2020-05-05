import os
from logfile import log

# Code -------------------------------------------------------------------------

# Returns a list with the path of all the files in the given folder
def get_all_files(folder):
    log("Scanning local directory...")
    res = []
    for f in os.listdir(folder):
        abspath = os.path.join(folder, f)
        if os.path.isfile(abspath):
            res.append((f, os.path.getsize(abspath)))
    log("Found " + str(len(res)) + " files in the local directory")
    return res
        
