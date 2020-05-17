import socket
import commandlink
from commandlink import send_request

# Config -----------------------------------------------------------------------

__dataBufferSize = 1024      # Length of the data TCP buffer
__connection_timeout = 10    # Maximum time to connect the socket
__transmission_timeout = 2   # Timeout of the data transfert

# Global variables ------------------------------------------------------------

__serverIP = ""

# Tools ------------------------------------------------------------------------

# Decodes the pasv command response and returns the port
def __decode_pasv(resp):
    resp = resp[resp.find('(')+1:resp.find(')')]
    numbers = resp.split(',')
    return int(numbers[4])*256 + int(numbers[5])

# Public functions -------------------------------------------------------------

# Establishes a data connection with the server
def connect(ip):
    global __connection_timeout
    global __transmission_timeout
    # Establishes a data connection
    pasvResp = send_request("PASV", startsWith="227")
    dataPort = __decode_pasv(pasvResp)
    log("Connecting data channel at port " + str(dataPort) + "...")
    dataSocket = socket.socket()
    dataSocket.settimeout(__connection_timeout)
    dataSocket.connect((ip, dataPort))
    dataSocket.settimeout(__transmission_timeout)
    return dataSocket

# Closes a data connection
def close(socket):
    port = str(socket.getpeername()[1])
    socket.close()
    log("Closed data channel at port " + port)

# Receives the file data and returns it (bytes)
def receive_data(socket):
    global __dataBufferSize
    received = b''
    # Sets up a callback to know when the transfer is done
    transfer_complete = False
    def action():
        nonlocal transfer_complete
        transfer_complete = True
    filter = lambda line: line.starts_with("226")
    commandlink.addcallback(action, filter)
    # Starts receiving
    while not transfer_complete:
        received += socket.recv(__dataBufferSize)
    log("Received " + str(len(received)) + " bytes")
    return received
