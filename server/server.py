# This is the server component of the e-book reader/server system

import socket
import select
from sys import argv

# Extract the port number from args
script, port_number_str = argv
port_number = int(port_number_str)

# Prepare message buffer size
BUFFER_SIZE = 1024

# Maximum number of connections to this computer via TCP
MAX_CONNECTIONS = 1

# Create the socket
serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)		# TCP connection
serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)	# re-usable socket
serversock.bind((socket.gethostname(), port_number))
serversock.listen(MAX_CONNECTIONS)

# Prepare the list of sockets to listen for
# Initially no clients, only the server socket
listen_sockets = [serversock]

while True:

	# Obtain lists of ready sockets returned by Select
	read_sockets, write_sockets, error_sockets = select.select(listen_sockets, [], [])

	# Check each ready-to-read socket	
	for rs in read_sockets:
	
		# Incoming connection request to server socket
		if (rs == serversock):
			# Accept the client
			clientsocket, addr = serversock.accept()

			# Add the client to list of listen sockets
			listen_sockets.append(clientsocket)

			# Print confirmation message
			print "Connection made with: ", addr

		# Information from other sockets
		# Assume client
		else:
			# Obtain the message
			recv_msg = rs.recv(BUFFER_SIZE)
			print "Received data: %s" % recv_msg
	
			# Extract information
			msg_components = recv_msg.split('#');

			# Determine the type of information received
			if (msg_components[1] == "Intro"):
				# Intro message received
				reply_msg = "I see! You're: " + msg_components[2]
				rs.send(reply_msg)				

			elif (msg_components[1] == "Exit"):
				# Exit message received - close connection
				reply_msg = "Alright, laters!"
				rs.send(reply_msg)
				rs.close()
				listen_sockets.remove(rs)

			elif (msg_components[1] == "Debug"):
				# Debugging message received:
				reply_msg = \
					"Debug message received. Parameters:" + msg_components[2]
				rs.send(reply_msg)		

			else:
				# Unknown type of message
				reply_msg = "Invalid message."
				rs.send(reply_msg)

serversock.close()
