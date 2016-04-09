# This is the server component of the e-book reader/server system

import socket
import select
import threading
import random
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

# This class represents the database for the server
# ie postsDB = { "bookname": (postInfo, postContent) }
#    postInfo = { "postID": (senderName, pageNumber, lineNumber, read/unread) }
#    postContent = { "postID": content }
class ServerDB(object):

	# Constants
	# For generating serial numbers
	MIN_ID_VAL = 1000
	MAX_ID_VAL = 9999

	postsDB = {}

	# Constructor
	def __init__(self):

		# Initialise the dicts
		for book in booklist:
			bookname, bookauthor = book
			self.postsDB[bookname] = {}
		
		# Maintain a list of serial numbers / post ID's
		self.post_ids = []

	# Insert a new forum post into database
	# given two strings that contain information about the post:
	# postInfoString: 	'#NewPostInfo#SenderName#BookName#PageNumber#LineNumber'
	# postContentString: 	'#NewPostContent#Content'
	# Note: Assumes the strings given are in the correct format
	def insertPost(self, postInfoString, postContentString):

		# Parse the strings
		postInfoString = postInfoString.split('#')
		postContentString = postContentString.split('#')
		sendername = postInfoString[2]
		bookname = postInfoString[3]
		pagenum = postInfoString[4]
		linenum = postInfoString[5]
		postcontent = postContentString[2]

		# Insert into database
		try:
			# Check for no posts in database associated with bookname
			if (bool(self.postsDB[bookname]) == False):
				postInfo = {}
				postContent = {}
				self.postsDB[bookname] = (postInfo, postContent)

			postInfo, postContent = self.postsDB[bookname]

			# Generate an id for the post
			new_post_id = self.generatePostID()
			
			# Insert the information into database
			postInfo[new_post_id] = (sendername, bookname, pagenum, linenum)		
			postContent[new_post_id] = postcontent

		except KeyError:
			print "Error: Book name '%s' not found." % bookname

	# Export db as a string
	# postInfoString: 	'#PostInfo#Id#SenderName#BookName#PageNumber#LineNumber'
	# postContentString: 	'#PostContent#Id#Content'
	def exportAsStr(self):
		# Loop through all books and posts
		dbStr = ""
		for bookname in self.postsDB.keys():
			if (bool(self.postsDB[bookname]) == False):
				continue;
			postInfo, postContent = self.postsDB[bookname]
			for postID in postInfo.keys():
				sendername, bookname, pagenumber, linenumber = postInfo[postID]
				dbStr = dbStr + "#PostInfo#" + str(postID) + "#" + sendername + "#" \
					+ bookname + "#" + str(pagenumber) + "#" + str(linenumber) + "\n"
				postcontent = postContent[postID]
				dbStr = dbStr + "#PostContent#" + str(postID) + "#" + postcontent + "\n"
		return dbStr	

	# Generate a unique forum post serial ID
	def generatePostID(self):	
		new_post_id = random.randint(self.MIN_ID_VAL, self.MAX_ID_VAL)		
		while (new_post_id in self.post_ids):
			new_post_id = random.randint(self.MIN_ID_VAL, self.MAX_ID_VAL)
		self.post_ids.append(new_post_id)
		return new_post_id

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
						# Intro message received - process information
						client_user_name = msg_components[2]
						client_opmode = msg_components[3]
						self.client.user_name = client_user_name
						self.client.opmode = client_opmode
						#rsock.send("Hello!")			

					elif (msg_components[1] == "Exit"):
						# Exit message received - cut connection with client
						self.listen_sockets.remove(rsock)
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

# Basic testing for database
def runDBTests():

	print "Current database:"
	print serverDB.exportAsStr()

	# postInfoString: 	'#NewPostInfo#SenderName#BookName#PageNumber#LineNumber'
	# postContentString: 	'#NewPostContent#Content'
	postInfoStr = "#NewPostInfo#iancwwong#shelley#2#9"
	postContentStr = "#NewPostContent#Why is this line blank?"
	serverDB.insertPost(postInfoStr, postContentStr)

	postInfoStr = "#NewPostInfo#thetoxicguy#shelley#2#9"
	postContentStr = "#NewPostContent#Because the author wrote it that way, you retard?"
	serverDB.insertPost(postInfoStr, postContentStr)

	postInfoStr = "#NewPostInfo#jasonng#exupery#3#4"
	postContentStr = "#NewPostContent#What's this line talking about?"
	serverDB.insertPost(postInfoStr, postContentStr)

	postInfoStr = "#NewPostInfo9#mohawk#joyce#1#2"
	postContentStr = "#NewPostContent#Repetition of 'my' is used."
	serverDB.insertPost(postInfoStr, postContentStr)

	print "Database with info:"
	print serverDB.exportAsStr()
	

# Extract the port number from args
script, port_number_str = argv
port_number = int(port_number_str)

# Parse information about the books contained in the 'booklist' file
# with format: [book folder name],[book author]
print "Loading booklist..."
booklist_file = open('booklist','r').read().split('\n')
booklist_file.remove('')
booklist = []
for line in booklist_file:
	line = line.split(',')
	booklist.append((line[0], line[1]))

# Create the server database
print "Intitialising database..."
serverDB = ServerDB()

# DEBUGGING
runDBTests()
exit()

# Prepare message buffer size
BUFFER_SIZE = 1024

# Maximum number of queued connections
MAX_CONNECTIONS = 1

# Create the socket
serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)		# TCP connection
serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)	# re-usable socket
serversock.bind((socket.gethostname(), port_number))
serversock.listen(MAX_CONNECTIONS)
print "Listening on port number:", port_number
print "Name of this server:",socket.gethostname()

# Prepare the server socket to listen for
listen_sockets = [serversock]

while True:

	# Obtain lists of sockets that are listenable
	read_sockets, write_sockets, error_sockets = select.select(listen_sockets, [], [])

	# Find the socket for the server in the list of ready sockets	
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
