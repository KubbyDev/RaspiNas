import socket
import time

# Config -----------------------------------------------------------------------

__commandBufferSize = 64    # Length of the command TCP buffer
__dataBufferSize = 1024     # Length of the data TCP buffer
__timeout = 0.1             # Time before considering the message is over

# Global variables -------------------------------------------------------------

__socket = socket.socket() # Socket of the command TCP connection
__socket.settimeout(__timeout)
serverIP = "" # Set by connect()

__logFileLocation = "client.log"
__logFile = open(__logFileLocation, "w+", newline="\n")

# Tools ------------------------------------------------------------------------

# Receives all the data the server sends and returns it (on the command socket)
def __receive():
    global __socket
    global __commandBufferSize
    global __logFile
    received = b''
    buf = b'a'
    while buf != b'':
        try: buf = __socket.recv(__commandBufferSize)
        except: buf = b''
        received += buf
    __logFile.write("<< " + received.decode("ascii"))
    return received

# Sends a request and returns the response
def __send_request(request):
    global __socket
    global __logFile
    global __timeout
    __socket.send(bytes(request, "ascii") + b"\r\n")
    __logFile.write(">> " + request + "\r\n")
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
    global serverIP
    global __logFile
    global __timeout
    # Establishes a data connection
    pasvResp = __send_request("PASV")
    dataPort = __decode_pasv(pasvResp)
    __logFile.write("I: Connecting data channel at port " + str(dataPort) + "...\r\n")
    dataSocket = socket.socket()
    dataSocket.connect((serverIP, dataPort))
    dataSocket.settimeout(__timeout)
    return dataSocket, dataPort

# Receives data from a data channel
def __receive_data(socket):
    global __dataBufferSize
    global __logFile
    received = b''
    buf = b'a'
    while buf != b'':
        try: buf = socket.recv(__dataBufferSize)
        except: buf = b''
        received += buf
    __logFile.write("I: Received " + str(len(received)) + " bytes\n")
    return received

# Code -------------------------------------------------------------------------

# Changes the location of the client logs (default is ./client.log)
def changeLogsLocation(path):
    global __logFileLocation
    global __logFile
    __logFileLocation = path
    __logFile.close()
    __logFile = open(__logFileLocation, "w+")

# Connects and authenticates to the server
def connect(ip, user, password):
    global __socket
    global serverIP
    global __logFile
    # Connects the socket
    __logFile.write("I: Connecting to " + ip + " at port 21...\r\n")
    __socket.connect((ip, 21))
    serverIP = ip
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

# Sends a file to the server
def send_file(path, destName=None):
    global __logFile
    if not destName: destName = __extract_name(path)
    # Establishes a data connection
    dataSocket, dataPort = __connect_data_channel()
    # Asks for a file upload
    __send_request("STOR " + destName)
    # Sends the file
    filedata = open(path, "rb").read()
    __logFile.write("I: Sending data from " + path + "...\r\n")
    dataSocket.send(filedata)
    dataSocket.close()
    __receive()
    __logFile.write("I: Closed data channel at port " + str(dataPort) + "\r\n")

# Downloads the file with given name to given path
def fetch_file(name, destPath=None):
    global __logFile
    if not destPath: destPath = name
    # Establishes a data connection
    dataSocket, dataPort = __connect_data_channel()
    # Asks for a file download
    __send_request("RETR " + name)
    # Downloads the file
    __logFile.write("I: Receiving data from " + name + "...\r\n")
    filedata = __receive_data(dataSocket)
    open(destPath, "wb+").write(filedata)
    dataSocket.close()
    __receive()
    __logFile.write("I: Closed data channel at port " + str(dataPort) + "\r\n")

def disconnect():
    global __socket
    global __logFile
    __socket.close()
    __logFile.write("I: Disconnecting...\r\n\r\n")
    __logFile.close()

"""
# TEST
connect("192.168.1.42", "pi", open("password", "r").read())
change_directory("storage")
send_file("test2.png")
fetch_file("angry.jpg")
disconnect()
"""
