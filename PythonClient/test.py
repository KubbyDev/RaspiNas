import socket
import time

# Config -----------------------------------------------------------------------

ip = "192.168.1.42"                         # IP of the FTP server
password = open("password", "r").read()     # Password to access the FTP server
bufferSize = 32                             # Length of the TCP buffers
timeout = 2                                 # Timeout of the TCP connections

# Global variables -------------------------------------------------------------

command = socket.socket()
data = socket.socket()
receivedData = b''

# Tools ------------------------------------------------------------------------

def decode_pasv(resp):
    respStr = resp.decode("ascii")
    respStr = respStr[respStr.find('(')+1:respStr.find(')')]
    numbers = respStr.split(',')
    return int(numbers[4])*256 + int(numbers[5])

def receive_data():
    global data
    print("Receiving data:")
    received = b''
    buf = "a"*bufferSize
    while len(buf) == bufferSize:
        buf = data.recv(bufferSize)
        received += buf
    print(received.decode("ascii"))
    print("Data reception end")

def receive_line():
    global receivedData
    global command
    index = receivedData.find(b'\r\n')
    print("Receiving...")
    while index == -1:
        rcvData = command.recv(bufferSize)
        print(rcvData.decode("ascii"), end='')
        receivedData += rcvData
        index = receivedData.find(b'\r\n')
    print("Reception end")
    line = receivedData[:index]
    receivedData = receivedData[index+2:]
    print("Extracted: " + line.decode("ascii"))
    return line

def send_request(request):
    global command
    print("Sent: %s" % request)
    command.send(bytes(request, "ascii") + b"\r\n")
    return receive_line()

# Code -------------------------------------------------------------------------

# Establishes the command connection
command.connect((ip, 21))

# Connection protocol
receive_line()
send_request("AUTH SSL")
send_request("USER pi")
send_request("PASS " + password)
pasvResp = send_request("PASV")
dataPort = decode_pasv(pasvResp)

# Establishes the data connection
print("Connecting data channel at port " + str(dataPort))
data.connect((ip, dataPort))

# Asks for a file
send_request("RETR test")

# Receives the file
receive_data()
