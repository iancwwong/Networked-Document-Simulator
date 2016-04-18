# This is the server component of the e-book reader/server system
# Written by: Ian Wong

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

	# Format of database:
	# db = {
	# 	"postID" : (postInfo, postContent)
	# }
	# postInfo = (sender, bookname, page, line)
	# postConent = postContent
	db = {}

	# Constructor
	def __init__(self):
		
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
		pagenum = int(postInfoString[4])
		linenum = int(postInfoString[5])
		postcontent = postContentString[2]

		# Generate an id for the post
		new_post_id = self.generatePostID()
		
		# Prepare the tuples to insert
		postInfo = (sendername, bookname, pagenum, linenum)		
		postContent = postcontent
		
		# Insert into database
		self.db[new_post_id] = (postInfo, postContent)

		# Print successful message
		newPostTuple = (bookname, pagenum, linenum, new_post_id)
		print "Post added to the database and given serial number", newPostTuple
	
		# return postID
		return new_post_id

	# Export db as a string
	# postInfoString: 	'#PostInfo#Id#SenderName#BookName#PageNumber#LineNumber'
	# postContentString: 	'#PostContent#Id#Content'
	def exportAsStr(self):
		# Loop through all books and posts
		dbStr = ""
		for postID in self.db.keys():
			postInfo, postContent = self.db[postID]
			sendername, bookname, pagenum, linenum = postInfo
			postcontent = postContent
			dbStr = dbStr + "#PostInfo#" + str(postID) + "#" + sendername + "#" \
				+ bookname + "#" + str(pagenum) + "#" + str(linenum) + "\n"
			dbStr = dbStr + "#PostContent#" + str(postID) + "#" + postcontent + "\n"
		return dbStr

	# Return a list of postID's that are NOT in the given compareList
	def consult(self, compareList):
		returnList = []
		for postID in self.db.keys():
			if not (postID in compareList):
				returnList.append(postID)
		return returnList

	# Convert a post with given ID into a tuple consisting of two strings
	# in the format:
	# (postInfoStr, postContentStr)
	# postInfoStr: '#PostInfo#[postID]#[sender]#[bookname]#[page]#[line]'
	# postContentStr: '#PostContent#[postID]#[post content]'
	def getPostAsStr(self, postID):
		try:
			# Obtain and parse the info in the db
			postInfo, postContent = self.db[postID]
			sendername, bookname, pagenum, linenum = postInfo		
			postContent = postContent

			# Construct the return strings and final tuple
			postInfoStr = "#PostInfo#" + str(postID) + "#" + sendername + "#" \
					+ bookname + "#" + str(pagenum) + "#" + str(linenum)
			postContentStr = "#PostContent#" + str(postID) + "#" + postContent

			return (postInfoStr, postContentStr)

		except KeyError:
			print "Error: postID of %d not found." % postID


	# Generate a unique forum post serial ID
	def generatePostID(self):	
		new_post_id = random.randint(self.MIN_ID_VAL, self.MAX_ID_VAL)		
		while (new_post_id in self.post_ids):
			new_post_id = random.randint(self.MIN_ID_VAL, self.MAX_ID_VAL)
		self.post_ids.append(new_post_id)
		return new_post_id

# This class is responsible for holding and pushing messages to clients
# Uses a list of clients
class MessagePusher(object):

	# Constructor - given a list of client threads
	def __init__(self, clientThreads):
		self.clientThreads = clientThreads

	# Push a forum post
	def pushPost(self, postInfoStr, postContentStr):
		for thread in clientThreads:
			thread.pushPost(postInfoStr, postContentStr)

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
		self.serve_client()
		print "Closing connection with", addr

	# Serve the client
	def serve_client(self):

		# Constants within scope of client thread
		newPostInfo = ()
		newPostContent = ()

		while not self.client_stop:
			
			data = self.selectRecv(BUFFER_SIZE)
			msg_components = data.split('#')

			# Determine the type of information received
			# Intro message received
			if (msg_components[1] == "Intro"):
				# Parse information about client
				client_user_name = msg_components[2]
				client_opmode = msg_components[3]
				self.client.user_name = client_user_name
				self.client.opmode = client_opmode		

			# Clean exit message received
			elif (msg_components[1] == "Exit"):
				# Cut connection with client
				self.listen_sockets.remove(self.client.sock)
				self.client_stop = True

			# Reader is uploading a new forum post
			# '#UploadPost#PostInfo...|#PostContent...
			elif (msg_components[1] == 'UploadPost'):

				print "New post received from %s!" % self.client.user_name

				# parse the strings that contain information of the post
				postDataStr = data.split('#UploadPost')[1]
				postInfoStr = postDataStr.split('|')[0]
				postContentStr = postDataStr.split('|')[1]
	
				# Insert the new post into database
				newPostID = serverDB.insertPost(postInfoStr, postContentStr)

				# Trigger the messagePusher to push the new post
				postInfoStr, postContentStr = serverDB.getPostAsStr(newPostID)
				messagePusher.pushPost(postInfoStr, postContentStr)

			# New Posts Request message received, in the format:
			# '#NewPostsRequest#[postID],[postID]...'
			elif (msg_components[1] == 'NewPostsRequest'):

				print "Query for new posts received from %s!" % self.client.user_name
				
				clientPostIDs = msg_components[2].split(',')
				
				# Consult the database for a list of ID's that are not in 
				# the client's list
				newPostIDList = serverDB.consult(clientPostIDs)

				# Construct a list of posts that client does not have
				# in the format:
				# [ (postInfoStr, postContentStr) ]
				# postInfoStr: '#PostInfo#[postID]#[sender]#[bookname]#[page]#[line]'
				# postContentStr: '#PostContent#[postID]#[post content]'
				newPostTupleList = []
				for newPostID in newPostIDList:
					postTuple = serverDB.getPostAsStr(newPostID)
					newPostTupleList.append(postTuple)

				# Append the two parts and send it off in the format:
				# 'NewPostData#PostInfo...|#PostContent...'
				newPostStrList = []
				for postTuple in newPostTupleList:
					postInfoStr, postContentStr = postTuple
					postStr = "#NewPostData" + postInfoStr + '|' + postContentStr
					newPostStrList.append(postStr)
				
				# Send the list of posts client does NOT have
				self.sendStream(newPostStrList, 'NewPosts', 'BeginNewPosts', 'PostComponentRecvd', 'EndNewPosts')
				print "New posts successfully sent to %s!" % self.client.user_name
				
			else:
				# Unknown type of message
				reply_msg = "Invalid message."
				rsock.send(reply_msg)

		# Close the socket
		self.client.sock.close()

	# Send a single post to the client
	# postInfoStr: '#PostInfo#[postID]#[sender]#[bookname]#[page]#[line]'
	# postContentStr: '#PostContent#[postID]#[post content]'
	def pushPost(self, postInfoStr, postContentStr):

		# If client is not in 'push' mode, then ignore
		if (self.client.opmode != "push") return

		# Construct the post string, and send it
		newSinglePost = "#NewSinglePost" + postInfoStr + '|' + postContentStr
		self.client.sock.send(newSinglePost)

	# Send a stream of data to client, while controlling when the server
	# should continue sending
	# Note: Tacks on a '#' to endMsg and ackPhrase to adhere to message format rules
	def sendStream(self, listToSend, startMsg, startAckPhrase, ackPhrase, endMsg):

		# Send start message
		self.client.sock.send('#' + startMsg)

		# Wait for an ack from client to start stream before sending stream items
		msg = self.selectRecv(BUFFER_SIZE)
		while (msg != ('#' + startAckPhrase)):
			msg = self.selectRecv(BUFFER_SIZE)

		# Ack received. Start sending stream
		for listItem in listToSend:
			self.client.sock.send(listItem)

			# Wait for user acknowledgement
			msg = self.selectRecv(BUFFER_SIZE)
			while (msg != ('#' + ackPhrase)):
				msg = self.selectRecv(BUFFER_SIZE)

		# Send end message to indicate (to client) end of stream
		self.client.sock.send('#' + endMsg)

	# Use 'select' module to obtain data from buffer
	def selectRecv(self, bufferSize):
		read_sockets, write_sockets, error_sockets = select.select(self.listen_sockets, [], [])
		for rs in read_sockets:
			if (rs == self.client.sock):
				data = self.client.sock.recv(bufferSize)
				return data

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
	

# Global Variables
clientThreadList = []		# Maintain a list of client threads
BUFFER_SIZE = 1024		# max message size
MAX_CONNECTIONS = 1		# Num queued connections

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

# Create the messagePusher object
print "Creating message pusher..."
messagePusher = MessagePusher(clientThreadList)

# DEBUGGING
runDBTests()
#exit()

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

			# Add to list of client threads
			clientThreadList.append(clientThread)

serversock.close()
