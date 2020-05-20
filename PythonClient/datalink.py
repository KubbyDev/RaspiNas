import socket
import commandlink
from commandlink import send_request
from logfile import log

# Config -----------------------------------------------------------------------

_dataBufferSize = 1024      # Length of the data TCP buffer
_connection_timeout = 10    # Maximum time to connect the socket
_transmission_timeout = 2   # Timeout of the data transfert

# Tools ------------------------------------------------------------------------

# Decodes the pasv command response and returns the port
def _decode_pasv(resp):
    resp = resp[resp.find('(')+1:resp.find(')')]
    numbers = resp.split(',')
    return int(numbers[4])*256 + int(numbers[5])

# Public functions -------------------------------------------------------------

class DataLink:

    # Establishes a data connection with the server
    def __init__(self, ip):
        global _connection_timeout
        global _transmission_timeout
        # Establishes a data connection
        pasvResp = send_request("PASV", startsWith="227")
        dataPort = _decode_pasv(pasvResp)
        log("Connecting data channel at port " + str(dataPort) + "...")
        self.socket = socket.socket()
        self.socket.settimeout(_connection_timeout)
        self.socket.connect((ip, dataPort))
        self.socket.settimeout(_transmission_timeout)
        # Sets up a callback to know when the transfer is done
        self.transfer_complete = False
        def action(line):
            nonlocal self
            self.transfer_complete = True
        filter = lambda line: line.startswith("226")
        commandlink.add_callback(action, filter)
        
    # Closes a data connection
    def close(self):
        port = str(self.socket.getpeername()[1])
        self.socket.close()
        log("Closed data channel at port " + port)

    # Receives data from the DataLink
    def receive_data(self):
        global _dataBufferSize
        received = b''
        # Starts receiving
        while not self.transfer_complete:
            received += self.socket.recv(_dataBufferSize)
        log("Received " + str(len(received)) + " bytes")
        return received
