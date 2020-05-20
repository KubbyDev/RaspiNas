import socket
import time
import os
import commandlink
from commandlink import send_request
from datalink import DataLink
from logfile import log

# Config -----------------------------------------------------------------------

__storageDir = "/storage"   # Main storage directory on the server
__backupDir = "/backup"     # Backup directory on the server

# Set by configure()
__hostName = ""
__username = ""
__password = ""
__timeout = 0.1
__maxFetchRetries = 5

# Global variables -------------------------------------------------------------

__serverIP = "" # Set by connect()

# Tools ------------------------------------------------------------------------

# Extracts the file name from a path
def __extract_name(path):
    return path[path.rfind(os.path.sep)+1:]

# Formats the raw response of LIST to (name, size) tuples
def __format_files_list(list):
    res = []
    for file in list.splitlines():
        parts = file.split(None, 8)
        res.append((parts[8], int(parts[4])))
    return res

# Goes to the given directory
def __change_directory(dir): send_request("CWD " + dir, startsWith="250")

# Code -------------------------------------------------------------------------

# Configures some data on the server before connecting
def configure(config):
    global __hostName
    global __timeout
    global __username
    global __password
    global __maxFetchRetries
    __hostName = config['server_ip']
    __username = config['username']
    __password = config['password']
    __timeout = float(config['socket_timeout'])
    __maxFetchRetries = int(config['max_retries'])
    if __password == "":
        file = open(config['password_file'])
        __password = file.read()
        file.close()
        
# Connects and authenticates to the server
def connect(hostname, user, password):
    global __serverIP
    global __hostName
    global __timeout
    global __username
    global __password
    global __storageDir
    # Finds the ip address
    log("Finding ip of host " + hostname + "...")
    try: ip = socket.gethostbyname(hostname)
    except:
        log("Could not resolve host " + hostname, "E: ")
        raise Exception("Could not resolve host " + hostname)
    __serverIP = ip
    # Opens the command link and sets the data link up
    commandlink.open(ip)
    # Sends the authentication messages
    send_request("AUTH SSL", startsWith="530")
    send_request("USER " + user, startsWith="331")
    send_request("PASS " + password, startsWith="230")
    # Sets the connection up
    send_request("TYPE I", startsWith="200")
    __change_directory(__storageDir)

# Sends a file to the server
def send_file(path, destName=None):
    global __serverIP
    if not destName: destName = __extract_name(path)
    # Establishes a data connection
    dataSocket = datalink.connect(__serverIP)
    # Asks for a file upload
    send_request("STOR " + destName)
    # Sends the file data
    datafile = open(path, "rb")
    filedata = datafile.read()
    log("Sending data from " + path + "...")
    dataSocket.send(filedata)
    datafile.close()
    # Closes the data connection
    datalink.close(dataSocket)

# Downloads the file with given name to given path
def fetch_file(name, destPath=None):
    global __serverIP
    if not destPath: destPath = name
    # Establishes a data connection
    link = DataLink(__serverIP)
    # Asks for a file download
    send_request("RETR " + name, startsWith="150")
    log("Receiving data from " + name + "...")
    # Receives the file
    filedata = link.receive_data()
    datafile = open(destPath, "wb+")
    datafile.write(filedata)
    datafile.close()
    # Closes the data connection
    link.close()

# Returns a list of all the files in the current working directory
# The list elements are tuples (name, size_bytes)
def list_files():
    global __serverIP
    # Establishes a data connection
    link = DataLink(__serverIP)
    # Asks for the files list
    send_request("LIST", startsWith="150")
    log("Receiving list of files...")
    # Receives the list
    rawData = link.receive_data().decode("ascii")
    files = __format_files_list(rawData)
    log("Found " + str(len(files)) + " files")
    # Closes the data connection
    link.close()
    return files

# Moves the target file to the backup folder
def backup_file(name):
    global __backupDir
    global __storageDir
    send_request("RNFR " + __storageDir + "/" + name)
    send_request("RNTO " + __backupDir + "/" + name)

# Disconnects from the server
def disconnect():
    log("Disconnecting...")
    commandlink.close()

