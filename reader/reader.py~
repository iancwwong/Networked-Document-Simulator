# This is the reader component of the e-book/server system

import time
import socket
from sys import argv

#Usage: python reader.py mode polling_interval user_name server_name server_port_number

# Extract information from arguments provided
script, user_name, server_name, server_port_str = argv
server_port = int(server_port_str)

# DEBUGGING
print "Username: ", user_name
print "Connecting to: ", server_name
print "At port: ", server_port

# Prepare the buffer size
BUFFER_SIZE = 1024

# Prepare the socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)	# TCP
sock.connect((server_name, server_port))

# Send intro message
intro_message = "#Intro#" + user_name
sock.send(intro_message)

# receive acknowledgement
reply = sock.recv(BUFFER_SIZE)
print "Received data: %s" % reply

# Run the reader
i = 0
while (i < 10):
	# Every second, send a message
	troll_message = "#Troll#" + str(i)
	sock.send(troll_message)
	reply = sock.recv(BUFFER_SIZE)
	print "Received data: %s" % reply
	time.sleep(1)
	i = i+1

# Send an exit message
exit_message = "#Exit#" + user_name
sock.send(exit_message)
reply = sock.recv(BUFFER_SIZE)
print "Received data: %s" % reply

# close the connection
sock.close()
