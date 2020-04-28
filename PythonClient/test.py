import socket
import time

# Config -----------------------------------------------------------------------

ip = "192.168.1.42"                         # IP of the FTP server
password = open("password", "r").read()     # Password to access the FTP server
bufferSize = 128                            # Length of the TCP buffers
timeout = 2                                 # Timeout of the TCP connections

# Global variables -------------------------------------------------------------

command = socket.socket()
data = None
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
    print(received.decode("charmap"))
    print("Data reception end")
    return received

def send_data(binarydata):
    data.send(binarydata)       

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

"""
# Establishes the command connection
command.connect((ip, 21))

# Connection protocol
receive_line()
send_request("AUTH SSL")
send_request("USER pi")
send_request("PASS " + password)
send_request("TYPE I")

# Establishes a data connection
pasvResp = send_request("PASV")
dataPort = decode_pasv(pasvResp)
print("Connecting data channel at port " + str(dataPort))
data = socket.socket()
data.connect((ip, dataPort))

# Asks for a file
send_request("CWD storage")
send_request("RETR angry.jpg")

# Receives the file
datafile = receive_data()
open("test.jpg", "wb+").write(datafile)
receive_line()
data.close()

# Establishes a data connection
pasvResp = send_request("PASV")
dataPort = decode_pasv(pasvResp)
print("Connecting data channel at port " + str(dataPort))
data = socket.socket()
data.connect((ip, dataPort))

# Asks for a file upload
send_request("STOR test2.png")

# Sends the file
filedata = open("test2.png", "rb").read()
send_data(filedata)
data.close()
"""
