# This is the server component of the e-book reader/server system

import socket
import select
import threading
import time
from sys import argv

# ----------------------------------------------------
# CLASSES
# ----------------------------------------------------

# This class represents a client from the server's perspective
class ClientObj(object):

	# Constructor given the client's username, mode, and socket
	def __init__(self, sock, addr):
		self.user_name = ""
		self.opmode = ""
		self.sock = sock
		self.addr = addr
	
	# Send a message to the client
	def sendmsg(msg):
		self.sock.send(msg)

	# Show details of client
	def showDetails():
		print "Username: \t",self.user_name
		print "Operation mode: \t",self.opmode
		print "Address: \t",self.addr

# This is the thread that is executed when a server serves a single client
class ClientThread(threading.Thread):

	# Constructor
	def __init__(self,clientsocket, addr):
		threading.Thread.__init__(self)

		# Create the client object
		self.client = ClientObj(clientsocket, addr)

		# Add the client's socket to list of sockets
		self.listen_sockets = [self.client.sock]

		# Set the client_stop flag to false (ie client does not want to terminate 
		# connection)
		self.client_stop = False

	# Execute thread
	def run(self):
		print "Starting thread for client at addr:",self.client.addr
		self.serve_client()
		print "Exiting thread for client at addr:", self.client.addr

	# Serve the client
	def serve_client(self):
		while not self.client_stop:
			
			# Obtain lists of ready sockets returned by Select
			read_sockets, write_sockets, error_sockets = select.select(self.listen_sockets, [], [])

			# Find the socket for this particular client
			# and read any incoming data	
			for rsock in read_sockets:

				# Ready to read client's socket
				if (rsock == self.client.sock):

					# Obtain the message (if any)
					recv_msg = rsock.recv(BUFFER_SIZE)
					print "Received data: %s" % recv_msg
	
					# Extract information
					msg_components = recv_msg.split('#');

					# Determine the type of information received
					if (msg_components[1] == "Intro"):
						# Intro message received
						reply_msg = "I see! You're: " + msg_components[2]
						rsock.send(reply_msg)				

					elif (msg_components[1] == "Exit"):
						# Exit message received
						reply_msg = "Alright, laters!"
						rsock.send(reply_msg)
						listen_sockets.remove(rsock)
						self.client_stop = True

					elif (msg_components[1] == "Debug"):
						# Debugging message received:
						reply_msg = \
							"Debug message received. Parameters:" + msg_components[2]
						rsock.send(reply_msg)		

					else:
						# Unknown type of message
						reply_msg = "Invalid message."
						rsock.send(reply_msg)

		# Close the socket
		self.client.sock.close()		 		

# ----------------------------------------------------
# MAIN
# ----------------------------------------------------

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
print "Listening on port number: ", port_number

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

			# Create the client thread
			clientThread = ClientThread(clientsocket, addr)

			# Run the thread
			clientThread.start()

			# Print confirmation message
			print "Connection made with: ", addr

serversock.close()
