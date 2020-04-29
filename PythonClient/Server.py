import socket
import time

# Config -----------------------------------------------------------------------

__commandBufferSize = 64    # Length of the command TCP buffer
__dataBufferSize = 1024     # Length of the data TCP buffer
__timeout = 0.1             # Time before considering the message is over

# Global variables -------------------------------------------------------------

__socket = socket.socket() # Socket of the command TCP connection
__socket.settimeout(__timeout)
__serverIP = "" # Set by connect()
logFile = None # Initialised by main.py

# Tools ------------------------------------------------------------------------

# Receives all the data the server sends and returns it (on the command socket)
def __receive():
    global __socket
    global __commandBufferSize
    global logFile
    received = b''
    buf = b'a'
    while buf != b'':
        try: buf = __socket.recv(__commandBufferSize)
        except: buf = b''
        received += buf
    logFile.write("<< " + received.decode("ascii"))
    return received

# Sends a request and returns the response
def __send_request(request):
    global __socket
    global logFile
    global __timeout
    __socket.send(bytes(request, "ascii") + b"\r\n")
    logFile.write(">> " + request + "\r\n")
    time.sleep(__timeout*2)
    return __receive()

# Decodes the pasv command response and returns the port
def __decode_pasv(resp):
    respStr = resp.decode("ascii")
    respStr = respStr[respStr.find('(')+1:respStr.find(')')]
    numbers = respStr.split(',')
    return int(numbers[4])*256 + int(numbers[5])

# Extracts the file name from a path
def __extract_name(path):
    return path[path.rfind('/')+1:]

# Establishes a data connection with the server and returns (socket, port)
def __connect_data_channel():
    global __serverIP
    global logFile
    global __timeout
    # Establishes a data connection
    pasvResp = __send_request("PASV")
    dataPort = __decode_pasv(pasvResp)
    logFile.write("I: Connecting data channel at port " + str(dataPort) + "...\r\n")
    dataSocket = socket.socket()
    dataSocket.connect((__serverIP, dataPort))
    dataSocket.settimeout(__timeout)
    return dataSocket, dataPort

# Closes a data connection
def __close_data_channel(socket):
    port = str(socket.getsockname()[1])
    socket.close()
    logFile.write("I: Closed data channel at port " + port + "\r\n")

# Receives data from a data channel
def __receive_data(socket):
    global __dataBufferSize
    global logFile
    received = b''
    buf = b'a'
    while buf != b'':
        try: buf = socket.recv(__dataBufferSize)
        except: buf = b''
        received += buf
    logFile.write("I: Received " + str(len(received)) + " bytes\n")
    return received

# Formats the raw response of LIST to (name, size) tuples
def __format_files_list(list):
    res = []
    for file in list.splitlines():
        parts = file.split(None, 8)
        res.append((parts[8], int(parts[4])))
    return res
    
# Code -------------------------------------------------------------------------

# Connects and authenticates to the server
def connect(ip, user, password):
    global __socket
    global __serverIP
    global logFile
    # Connects the socket
    logFile.write("I: Connecting to " + ip + " at port 21...\r\n")
    __socket.connect((ip, 21))
    __serverIP = ip
    # Sends the authentication messages
    __receive()
    __send_request("AUTH SSL")
    __send_request("USER " + user)
    __send_request("PASS " + password)
    # Sets the connection up
    __send_request("TYPE I")

# Goes to the given directory
def change_directory(dir):
    __send_request("CWD " + dir)

# Returns the current working directory
def get_working_directory():
    return __send_request("PWD").decode("ascii").split('"')[1]

# Sends a file to the server
def send_file(path, destName=None):
    global logFile
    if not destName: destName = __extract_name(path)
    # Establishes a data connection
    dataSocket, dataPort = __connect_data_channel()
    # Asks for a file upload
    __send_request("STOR " + destName)
    # Sends the file
    filedata = open(path, "rb").read()
    logFile.write("I: Sending data from " + path + "...\r\n")
    dataSocket.send(filedata)
    __receive()
    # Closes the data connection
    __close_data_channel(dataSocket)

# Downloads the file with given name to given path
def fetch_file(name, destPath=None):
    global logFile
    if not destPath: destPath = name
    # Establishes a data connection
    dataSocket, dataPort = __connect_data_channel()
    # Asks for a file download
    __send_request("RETR " + name)
    # Downloads the file
    logFile.write("I: Receiving data from " + name + "...\r\n")
    filedata = __receive_data(dataSocket)
    open(destPath, "wb+").write(filedata)
    __receive()
    # Closes the data connection
    __close_data_channel(dataSocket)

# Returns a list of all the files in the current working directory
# The list elements are tuples (name, size_bytes)
def list_files():
    # Establishes a data connection
    dataSocket, dataPort = __connect_data_channel()
    # Asks for the files list
    __send_request("LIST")
    logFile.write("I: Receiving list of files...\r\n")
    # Receives the list
    rawData = __receive_data(dataSocket).decode("ascii")
    files = __format_files_list(rawData)
    logFile.write("I: Received " + str(len(files)) + " files\r\n")
    # Closes the data connection
    __close_data_channel(dataSocket)
    return files

# Disconnects from the server
def disconnect():
    global __socket
    global logFile
    __socket.close()
    logFile.write("I: Disconnecting...\r\n\r\n")

"""
# TEST
logFile = open("client.log", "w+", newline="\n")
connect("192.168.1.44", "pi", open("password", "r").read())
#print(get_working_directory())
change_directory("storage")
#print(list_files())
#print(get_working_directory())
#send_file("test2.png")
#fetch_file("angry.jpg")
disconnect()
"""
