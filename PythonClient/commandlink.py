import threading
import time
import socket
from logfile import log

# Config -----------------------------------------------------------------------

__line_ending = b"\r\n"       # The line ending mark for responses sent by the server
__commandBufferSize = 64     # Length of the command TCP buffer
__request_timeout = 2        # Maximum time to receive the response of a request (seconds)
__connection_timeout = 10    # Maximum time to connect the socket

# Global variables -------------------------------------------------------------

__continue_listening = False # Set this variable to false to stop the listening thread
__callbacks = []             # Functions to call when a message is received from the server
__cblock = threading.Lock()  # Thread lock object for the callbacks list
__socket = None              # The socket used for the tcp connection

# Tools ------------------------------------------------------------------------

# Processes incomming lines
def __line_received(line):
    global __callbacks
    global __cblock
    log(line, "<< ")
    # Locks the list of callbacks during the processing
    __cblock.acquire()
    # Goes through the filters and triggers the actions for the filters that match
    for filter, action in __callbacks:
        if filter(line):
            action(line)
            __callbacks.remove((filter, action))
    __cblock.release()

# Listen to the incomming data and triggers __line_received when a line is received
def __listen(socket):
    global __continue_listening
    global __line_ending
    global __commandBufferSize
    received = b''
    log("Started listening to the command socket")
    while __continue_listening:
        # Receives data
        try: received += __socket.recv(__commandBufferSize)
        except: continue
        # If the data contains the line ending, splits it and calls __line_received
        index = received.find(__line_ending)
        while index != -1:
            __line_received(received[:index].decode("ascii"))
            received = received[index+len(__line_ending):]
            index = received.find(__line_ending)
    log("Stopped listening to the command socket")
    return received

# Public functions -------------------------------------------------------------

# Opens the command connection at the given ip
def open(ip):
    global __continue_listening
    global __socket
    # Connects the socket
    log("Connecting to " + ip + " at port 21...")
    __socket = socket.socket()
    __socket.settimeout(__connection_timeout)
    try: __socket.connect((ip, 21))
    except:
        log("Could not connect to " + ip, "E: ")
        raise Exception("Could not connect to " + ip)
    __socket.settimeout(0.01)
    # Starts the listening thread
    __continue_listening = True
    thread = threading.Thread(target=__listen, args=(socket,))
    thread.start()

# Close the command connection
def close():
    global __continue_listening
    global __socket
    __continue_listening = False
    time.sleep(0.05)
    __socket.close()

# Adds a callback for an incomming line from the server
# Whenever a line is received from the server, each filter function is called
# and corresponding actions are called if the filter returns True. When an action
# is called, it is automatically removed from the list Actions are functions that
# take a string (the incomming line) in parameter and return nothing
# Warning: the callbacks are executed asynchronously, make sure nothing breaks
def add_callback(action=None, filter=None):
    global __callbacks
    global __cblock
    if not action: action = lambda line : None
    if not filter: filter = lambda line : True
    __cblock.acquire()
    __callbacks.append((filter, action))
    __cblock.release()

# Sends a request and returns the response
def send_request(request, filter=None, startsWith=None):
    global __socket
    global __request_timeout
    # Sets a callback to know when the response has arrived*
    response = None
    def action(line):
        nonlocal response
        response = line
    if startsWith: filter = lambda line : line.startswith(startsWith)
    add_callback(action, filter)
    # Sends the request
    __socket.send(bytes(request, "ascii") + b"\r\n")
    log(request, ">> ")
    # Blocks while the response is not received
    start = time.time()
    while response is None:
        if time.time() - start > __request_timeout:
            raise Exception("Didn't receive response for request: " + request)
        time.sleep(0.005)
    # Returns the response
    return response

