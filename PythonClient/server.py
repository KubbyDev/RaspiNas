import socket
import time
import os
from logfile import log

# Config -----------------------------------------------------------------------

__commandBufferSize = 64    # Length of the command TCP buffer
__dataBufferSize = 1024     # Length of the data TCP buffer
__storageDir = "/storage"   # Main storage directory on the server
__backupDir = "/backup"     # Backup directory on the server

# Set by configure()
__hostName = ""
__username = ""
__password = ""
__timeout = 0.1
__maxFetchRetries = 5

# Global variables -------------------------------------------------------------

__socket = None # Socket of the command TCP connection
__serverIP = "" # Set by connect()

# Tools ------------------------------------------------------------------------

# Receives all the data the server sends and returns it (on the command socket)
def __receive():
    global __socket
    global __commandBufferSize
    received = b''
    buf = b'a'
    while buf != b'':
        # Tries to receive data
        try:
            buf = __socket.recv(__commandBufferSize)
            received += buf
        except: buf = b''
    log(received.decode("ascii"), "<< ")
    return received

# Sends a request and returns the response
def __send_request(request):
    global __socket
    global __timeout
    __socket.send(bytes(request, "ascii") + b"\r\n")
    log(request, ">> ")
    return __receive()

# Decodes the pasv command response and returns the port
def __decode_pasv(resp):
    respStr = resp.decode("ascii")
    respStr = respStr[respStr.find('(')+1:respStr.find(')')]
    numbers = respStr.split(',')
    return int(numbers[4])*256 + int(numbers[5])

# Extracts the file name from a path
def __extract_name(path):
    return path[path.rfind(os.path.sep)+1:]

# Establishes a data connection with the server and returns (socket, port)
def __connect_data_channel():
    global __serverIP
    global __timeout
    # Establishes a data connection
    pasvResp = __send_request("PASV")
    dataPort = __decode_pasv(pasvResp)
    log("Connecting data channel at port " + str(dataPort) + "...")
    dataSocket = socket.socket()
    dataSocket.connect((__serverIP, dataPort))
    dataSocket.settimeout(__timeout)
    return dataSocket, dataPort

# Closes a data connection
def __close_data_channel(socket):
    port = str(socket.getpeername()[1])
    socket.close()
    log("Closed data channel at port " + port)

# Receives data from a data channel
def __receive_data(socket):
    global __dataBufferSize
    received = b''
    buf = b'a'
    while buf != b'':
        try: buf = socket.recv(__dataBufferSize)
        except: buf = b''
        received += buf
    log("Received " + str(len(received)) + " bytes")
    return received

# Formats the raw response of LIST to (name, size) tuples
def __format_files_list(list):
    res = []
    for file in list.splitlines():
        parts = file.split(None, 8)
        res.append((parts[8], int(parts[4])))
    return res

# Goes to the given directory
def __change_directory(dir):
    __send_request("CWD " + dir)

# Returns the current working directory
def __get_working_directory():
    return __send_request("PWD").decode("ascii").split('"')[1]

# Extracts the file size from a connection openning message (after a RETR)
def __extract_file_size(message):
    begin = b" ("
    end = b" bytes)"
    sizestr = message[message.find(begin)+len(begin):message.find(end)]
    return int(sizestr)

# Downloads the file with given name and returns the raw binary data
# as well as the expected size of this data (bytes) in a tuple
def __fetch_file(name):
    global __timeout
    # Establishes a data connection
    dataSocket, dataPort = __connect_data_channel()
    # Asks for a file download
    response = __send_request("RETR " + name)
    expectedsize = __extract_file_size(response)
    # Downloads the file
    log("Receiving data from " + name + "...")
    filedata = __receive_data(dataSocket)
    # Closes the data connection
    __close_data_channel(dataSocket)
    time.sleep(__timeout*2)
    __receive()
    # Returns the data and the size sent by the server
    return filedata, expectedsize

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
def connect():
    global __socket
    global __serverIP
    global __hostName
    global __timeout
    global __username
    global __password
    global __storageDir
    # Finds the ip address
    log("Finding ip of host " + __hostName + "...")
    try: __serverIP = socket.gethostbyname(__hostName)
    except:
        log("Could not resolve host " + __hostName, "E: ")
        raise Exception("Could not resolve host " + __hostName)
    # Connects the socket
    log("Connecting to " + __serverIP + " at port 21...")
    __socket = socket.socket()
    __socket.settimeout(__timeout)
    try: __socket.connect((__serverIP, 21))
    except:
        log("Could not connect to " + __serverIP, "E: ")
        raise Exception("Could not connect to " + __serverIP)
    # Sends the authentication messages
    __receive()
    __send_request("AUTH SSL")
    __send_request("USER " + __username)
    __send_request("PASS " + __password)
    # Sets the connection up
    __send_request("TYPE I")
    __change_directory(__storageDir)

# Sends a file to the server
def send_file(path, destName=None):
    global __timeout
    if not destName: destName = __extract_name(path)
    # Establishes a data connection
    dataSocket, dataPort = __connect_data_channel()
    # Asks for a file upload
    __send_request("STOR " + destName)
    # Sends the file data
    datafile = open(path, "rb")
    filedata = datafile.read()
    log("Sending data from " + path + "...")
    dataSocket.send(filedata)
    datafile.close()
    # Closes the data connection
    __close_data_channel(dataSocket)
    time.sleep(__timeout*2)
    __receive()

# Downloads the file with given name to given path
# Will retry if the download fails.
# If the download fails too many time (maxTries), returns False
def fetch_file(name, destPath=None):
    global __maxFetchRetries
    if not destPath: destPath = name
    tries = 0
    while tries < __maxFetchRetries:
        if tries > 0: log("Retrying...")
        # Downloads the file
        data, expectedsize = __fetch_file(name)
        actualsize = len(data)
        # If the download succeeded, writes the file and exits
        if actualsize == expectedsize:
            file = open(destPath, "wb+")
            file.write(data)
            file.close()
            return True
        # If the download failed, logs it
        log("Download failed, received " + str(actualsize) + " bytes instead of " + str(expectedsize), source="E: ")
        tries += 1
    # If the max number of retries is reached, gives up
    log("Max retries reached, aborted the download")
    return False

# Returns a list of all the files in the current working directory
# The list elements are tuples (name, size_bytes)
def list_files():
    # Establishes a data connection
    dataSocket, dataPort = __connect_data_channel()
    # Asks for the files list
    __send_request("LIST")
    log("Receiving list of files...")
    # Receives the list
    rawData = __receive_data(dataSocket).decode("ascii")
    files = __format_files_list(rawData)
    log("Found " + str(len(files)) + " files")
    # Closes the data connection
    __close_data_channel(dataSocket)
    return files

# Moves the target file to the backup folder
def backup_file(name):
    global __backupDir
    global __storageDir
    __send_request("RNFR " + __storageDir + "/" + name)
    __send_request("RNTO " + __backupDir + "/" + name)

# Disconnects from the server
def disconnect():
    global __socket
    __socket.close()
    __socket = None
    log("Disconnecting...")


'''
# TEST
import logfile
logfile.start()
connect("192.168.1.44", "pi", open("password", "r").read())
#list_files()
#send_file("..\\TestLocalDir\\angry choke.png")
#backup_file("angry table flip.jpg")
#fetch_file("angry table flip.jpg")
disconnect()
'''
