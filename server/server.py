# This is the server component of the e-book reader/server system
# Written by: Ian Wong

import socket
import select
import threading
import random
from sys import argv
import os

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

# This class represents a book
class Book(object):

	def __init__(self, bookName, bookAuthor):
		self.bookname = bookName
		self.author = bookAuthor
		
		# Construct the book with pages and lines
		self.pages = []

		# Determine number of pages
		self.numpages = len([name for name in os.listdir(bookName)])

		# Initialise the page objects by reading each page file
		for pagenum in range(1,self.numpages+1):
			pageObj = Page(bookName, pagenum)	# page numbers need an offset
			self.pages.append(pageObj)

	# Return a list of strings containing all lines in a particular page
	# Note: Assumes pageNum starts at 1 (NOT index based)
	def getPageContent(self,pageNum):

		# Check if pagenum is valid
		if (not self.hasPage(pageNum)):
			errorStr = "#Error#Page %d does not exist." % (pageNum)
			return [errorStr]

		return self.pages[pageNum-1].getContent()

	# Checks whether the page exists
	# NOTE: pageNum is NOT index based
	def hasPage(self, pageNum):
		return (pageNum-1 in range(0, len(self.pages)))	

	# Returns a page object given a specific page number
	# NOTE: page number is NOT index based
	def getPageObj(self, pageNum):
		return self.pages[pageNum-1]

# This class represents a page
# Note: a page has directory '[bookname]/[bookname]_page[pagenumber]'
class Page(object):

	def __init__(self,bookName,pageNum):
		self.bookname = bookName
		self.pagenum = pageNum
		self.lines = []

		# Construct the line objects
		page_filename = self.bookname + "/" + self.bookname + "_page" + str(self.pagenum)
		page_file = open(page_filename, 'r')
		lineNum = 0
		for line in page_file:
			# Remove the trailing newline character if  any
			line = line.rstrip()
			lineNum = lineNum + 1
			lineObj = Line(line, lineNum)
			self.lines.append(lineObj)
		self.numlines = lineNum

	# Retrieve the contents on the page
	def getContent(self):
		pageLines = []
		for line in self.lines:
			lineStr = '#' + str(line.linenum) + '#' + line.getContent()
			pageLines.append(lineStr)
		return pageLines	

	# Returns whether there is a particular line number in the page
	# NOTE: lineNum is NOT index based
	def hasLine(self, lineNum):
		return (lineNum-1 in range(0, len(self.lines)))
	

# This is a class that represents a line on a page
class Line(object):
		
	def __init__(self,lineStr,lineNum):
		# Set the line number
		self.linenum = lineNum

		# Set the line content
		# Parse the line according to the format:
		# 3 spaces, line number, 1 space, line content
		lineStr = lineStr.split('   ')[1]
		lineStr = lineStr.split(' ')
		lineStr.pop(0)
		lineStr = ' '.join(lineStr)
		self.linecontent = lineStr

	# Show the contents of the page with message indication on each line
	# with format: post status, 2 spaces, line number, 1 space, line content		
	def showLine(self):
		print (self.post_chars[self.poststatus] + '  ' + str(self.linenum) + ' ' + self.linecontent)

	# Get the contents of the line
	def getContent(self):
		return self.linecontent

# This class represents the database for the server
# ie postsDB = { "bookname": (postInfo, postContent) }
#    postInfo = { "postID": (senderName, pageNumber, lineNumber) }
#    postContent = { "postID": content }
# NOTE: After each operation that involves returning a result, it will
# pack the result with an error status. If there is an error, the result 
# will be the error message.
class ServerDB(object):

	# Constants
	# For generating serial numbers
	MIN_ID_VAL = 1000
	MAX_ID_VAL = 9999

	# Success phrase
	OP_FAILURE = 0		# OP = operation
	OP_SUCCESS = 1

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

		# Check if post information is valid - ie bookname, pagenum, and linenum
		try:
			if (not books[bookname].hasPage(pagenum)):
				errorStr = "Page '" + str(pagenum) + "' not found."
				return (self.OP_FAILURE, errorStr)
			if (not books[bookname].getPageObj(pagenum).hasLine(linenum)):
				errorStr = "Line '" + str(linenum) + "' not found."
				return (self.OP_FAILURE, errorStr)
		except KeyError:
			errorStr = "Book '" + str(bookname) + "' not found."
			return (self.OP_FAILURE, errorStr)

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
		return (self.OP_SUCCESS, new_post_id)

	# Return a list of post IDs for a particular book and page
	def getPosts(self, bookName, pageNum):

		# Loop through all posts, adding those that match the criteria to the final list
		postIDs = []
		for postID in self.db.keys():
			postInfo, _ = self.db[postID]
			_, bookname, pagenum, _ = postInfo
			if (bookname == bookName and pagenum == pageNum):
				postIDs.append(postID)

		return (self.OP_SUCCESS, postIDs)

	# Return the (postInfo, postContent) tuple, corresponding to a given ID
	def getPost(self, postID):
		try:
			postInfo, postContent = self.db[postID]
			return (self.OP_SUCCESS, (postInfo, postContent))

		except KeyError:
			errorStr = "No such postID exists."
			return (self.OP_FAILURE, errorStr)

	# Export db as a string
	# postInfoString: 	'#PostInfo#Id#SenderName#BookName#PageNumber#LineNumber'
	# postContentString: 	'#PostContent#Id#Content'
	def exportAsStr(self):
		# Loop through all  posts
		dbStr = ""
		for postID in self.db.keys():
			postInfo, postContent = self.db[postID]
			sendername, bookname, pagenum, linenum = postInfo
			postcontent = postContent
			dbStr = dbStr + "#PostInfo#" + str(postID) + "#" + sendername + "#" \
				+ bookname + "#" + str(pagenum) + "#" + str(linenum) + "\n"
			dbStr = dbStr + "#PostContent#" + str(postID) + "#" + postcontent + "\n"
		return dbStr

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
		
				print "Client details received."
				print "Username: ",self.client.user_name
				print "Opmode: ",self.client.opmode	

			# Clean exit message received
			elif (msg_components[1] == "Exit"):
				# Cut connection with client
				self.listen_sockets.remove(self.client.sock)
				self.client_stop = True

			# Display request received from client
			elif (msg_components[1] == 'DisplayReq'):
			
				# Load parameters
				bookname = msg_components[2]
				pagenum = int(msg_components[3])
				print "Client requested to print page %d from %s." % (pagenum, bookname)

				# Obtain a list of strings to send
				displayMsg = []
				try:
					displayMsg = books[bookname].getPageContent(pagenum)

				except KeyError:
					errorStr = "#Error#Book name '%s' not found." % bookname
					displayMsg.append(errorStr)

				# Send the list of strings as a stream of messages
				print "Sending display stream..."
				self.sendStream(displayMsg, 'DisplayResp', 'BeginDisplayResp', 'DisplayRespRcvd', 'EndDisplayResp')

			# Reader is uploading a new forum post
			# '#UploadPost#PostInfo...|#PostContent...
			elif (msg_components[1] == 'UploadPost'):

				print "New post received from %s!" % self.client.user_name

				# parse the strings that contain information of the post
				postDataStr = data.split('#UploadPost')[1]
				postInfoStr = postDataStr.split('|')[0]
				postContentStr = postDataStr.split('|')[1]
	
				# Insert the new post into database, and obtain response
				resp, result = serverDB.insertPost(postInfoStr, postContentStr)

				# Check if any errors inserting into database
				if (resp == serverDB.OP_FAILURE):
					uploadResp = "#Error#" + result
					self.client.sock.send(uploadResp)
					continue

				# Send the response back to the client
				self.client.sock.send(result)

				# Trigger the messagePusher to push the new post
				#postInfoStr, postContentStr = serverDB.getPostAsStr(newPostID)
				#messagePusher.pushPost(postInfoStr, postContentStr)

			# Posts Request message received (to obtain post IDs for a particular book/page), in the format:
			# '#GetPostsIDReq#[bookname]#[pagenum]'
			elif (msg_components[1] == 'GetPostsIDReq'):

				# Extract information given
				print "Query for new posts received from %s!" % self.client.user_name
				bookName = msg_components[2]
				pageNum = int(msg_components[3])

				# Get a list of all post ID's for the associated page/book,
				resp, result = serverDB.getPosts(bookName, pageNum)

				# Check if any errors retrieving post ids
				if (resp == serverDB.OP_FAILURE):
					postsResp = "#Error#" + result
					self.client.sock.send(postsResp)
					continue

				# Construct the response string, and send to client
				postsIDs = result
				postsRespStr = "#GetPostsIDResp#"
				for i in range(0, len(postsIDs)):
					postsRespStr = postsRespStr + str(postsIDs[i])
					if (i < len(postsIDs) - 1):
						postsRespStr = postsRespStr + ','
				self.client.sock.send(postsRespStr)
				
			else:
				# Unknown type of message
				reply_msg = "Invalid message: ", data

		# Close the socket
		self.client.sock.close()

	# Send a single post to the client
	# postInfoStr: '#PostInfo#[postID]#[sender]#[bookname]#[page]#[line]'
	# postContentStr: '#PostContent#[postID]#[post content]'
	def pushPost(self, postInfoStr, postContentStr):

		# If client is not in 'push' mode, then ignore
		if (self.client.opmode != "push"):
			return

		# Construct the post string, and send it
		newSinglePost = "#NewSinglePost" + postInfoStr + '|' + postContentStr
		self.client.sock.send(newSinglePost)

	# Send a stream of data to client, while controlling when the server
	# should continue sending
	# Note: Tacks on a '#' to all parameter messages to adhere to message formatting
	def sendStream(self, listToSend, startMsg, startAckPhrase, ackPhrase, endMsg):

		# Send start message
		self.client.sock.send('#' + startMsg)

		# Confirm client is ready for stream receipt
		self.listenFor(startAckPhrase)

		# Ack received. Start sending stream
		for listItem in listToSend:
			self.client.sock.send(listItem)
			self.listenFor(ackPhrase)

		# Send end message to indicate (to client) end of stream
		self.client.sock.send('#' + endMsg)

	# Wait for a particular message from the socket before terminating
	# NOTE: Tacks on a '#' to adhere to format rules
	def listenFor(self, listenMsg):
		msg = self.selectRecv(BUFFER_SIZE)		
		while (msg != ('#' + listenMsg)):
			msg = self.selectRecv(BUFFER_SIZE)
			

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

# Basic testing for books
def runBookTests():

	# Print out all the pages in each book
	for bookname in books.keys():
		print 'Book %s:' % bookname
		for pageNum in range(0, books[bookname].numpages+1):
			print "Page number %d:" % pageNum
			print books[bookname].getPageContent(pageNum)
			print ""
		print ""
	
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

# Load the books into memory
print "Loading books..."
books = {}
for book in booklist:
	book_dir, book_author = book			# Book_dir is equivalent to book's name
	books[book_dir] = Book(book_dir, book_author)

# Create the server database
print "Intitialising database..."
serverDB = ServerDB()

# DEBUGGING
#runBookTests()
runDBTests()
#exit()

# Create the messagePusher object
print "Creating message pusher..."
messagePusher = MessagePusher(clientThreadList)

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
