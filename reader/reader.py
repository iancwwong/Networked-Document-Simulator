# This is the reader component of the e-book/server system
# Written by: Ian Wong

import socket
import select
import threading
from sys import argv
import sys

# ----------------------------------------------------
# CLASSES
# ----------------------------------------------------
		
# This class represents the database for the reader that contains forum posts
# Format:
#
# db = { "postID" : (postInfo, postContents) }
# postInfo = (senderName, bookName, pageNum, lineNum, readStatus)
# postContents = postContent
#
class ReaderDB(object):

	# Constants
	UNREAD = 0
	READ = 1

	# Corresponding Post Characters
	post_status_chars = { -1: ' ', 0: 'n', 1: 'm' }

	# Constructor
	def __init__(self):
		# Storing forum posts for each book
		self.db = {}

	# Insert a new post, given two strings:
	# postInfoString: 	'#PostInfo#Id#SenderName#BookName#PageNumber#LineNumber'
	# postContentString: 	'#PostContent#Id#Content' 
	# NOTE: postID, pagenumber, and linenumber are interpreted as ints (NOT strings)
	def insertPost(self, postInfoStr, postContentStr):

		# Parse the given strings

		# Split strings on '#'
		postInfoComponents = postInfoStr.split('#')		
		postContentComponents = postContentStr.split('#')

		# Check that the two given id's are the same
		if (postInfoComponents[2] != postContentComponents[2]):
			print "Error creating forum post object - ID's are not the same!"
			return
		
		# Parse and set the forum post based on the split strings
		postID = int(postInfoComponents[2])
		sendername = postInfoComponents[3]	
		bookname = postInfoComponents[4]
		pagenumber = int(postInfoComponents[5])
		linenumber = int(postInfoComponents[6])
		readstatus = self.UNREAD	
		postcontent = '#'.join(postContentComponents[3:])
		
		# Construct the postInfo and postContent tuple
		postInfo = (sendername, bookname, pagenumber, linenumber, readstatus)
		postContent = postcontent
		
		# Insert tuple into database
		self.db[postID] = (postInfo, postContent)

	# Given a postID, returns a tuple, containing info and content of a forum post
	def getPost(self, postID):
		try:
			return self.db[postID]
		except KeyError:
			print "Error: No such post with id %d found." % postID

	# Set a post read status to be 'Read', given a particular post ID
	def setRead(self, readPostID):
		try:
			# Get the post tuple
			postInfo, postContent = self.getPost(readPostID)
			
			# Manipulate the read status
			sender, book, page, line, _ = postInfo
			readstatus = self.READ
			
			# Re-insert tuple into database
			newPostInfo = (sender, book, page, line, readstatus)
			self.db[readPostID] = (newPostInfo, postContent)

		except:
			print "Error: No such post with id %d found." % readPostID

	# Export db as a string
	# Post ID [id]:
	# Info: [sender], [bookname], [pagenum], [linenum], [readstatus]
	# Content: [post content]
	# 
	def exportAsStr(self):
		dbStr = ""
		for postID in self.db.keys():
			dbStr = dbStr + "Post ID " + str(postID) + ":\n"
			postInfo, postContent = self.db[postID]
			sender, book, page, line, readStatus = postInfo
			dbStr = dbStr + "Info: " + sender + "," + book + "," + str(page) + \
				"," + str(line) + "," + str(readStatus) + "\n"
			dbStr = dbStr + "Content: " + postContent + "\n\n"
		return dbStr

	# Obtains a list of post ID's in the entire database
	def getAllPostIDs(self):
		return self.db.keys()

	# Gets a single character corresponding to whether a particular line (in a book/page)
	# contains read / unread posts, or nothing otherwise.
	def consultPostsStatus(self, bookname, pagenum, linenum):
		
		postIDs = self.getPostIDs(bookname, pagenum, linenum)
	
		# Check if list is empty
		if (len(postIDs) == 0):
			return self.post_status_chars[-1]

		# Check if there are any unread posts
		for postID in postIDs:
			postInfo, _ = self.getPost(postID)
			_, _, _, _, status = postInfo
			if (status == self.UNREAD):
				return self.post_status_chars[self.UNREAD]
		
		# At this point, all messages are read
		return self.post_status_chars[self.READ]

	# Return a list of post ID's for a particular book, page, and line
	# Args could be at least one of the following from the list: bookname, pagenum, and linenum
	# NOTE: Based on number of arguments, they are interpreted as follows: 
	#    1 argument = bookname given (AT LEAST this is given)
	#    2 arguments = bookname and pagenum given
	#    3 arguments = bookname, pagenum, and linenum given
	def getPostIDs(self, *args):
		args = list(args)
		numargs = len(args)
		bookName = args[0]
		if (numargs > 1):
			pageNum = int(args[1])
		if (numargs > 2):
			lineNum = int(args[2])

		# Loop through all posts, returning the ones that match the condition
		idList = []
		for postID in self.db.keys():
			i = 0
			postInfo, _ = self.getPost(postID)
			_, bookname, page, line, _ = postInfo
			if (bookname == bookName):
				i = i+1
				if (numargs > 1 and page == pageNum):
					i = i+1
					if (numargs > 2 and line == lineNum):
						i = i+1
			if (i == numargs):
				idList.append(postID)	
		return idList

# This class is the thread that runs when reader is listening for input from server
# NOTE: All messages sent by server should start with '#', followed by a phrase
# that helps reader identify what message it is
class ListenThread(threading.Thread):

	# Constructor given the socket connected to the server
	def __init__(self,socket):
		threading.Thread.__init__(self)
		self.event = threading.Event()
		self.socket = socket

	# Execute thread - constantly listen for messages
	# from the connected server
	def run(self):

		# Constantly listen for messages until event is set
		while not self.event.isSet():
				
			data = selectRecv(BUFFER_SIZE)
			if (data == ""):
				continue
			data_components = data.split('#')

			# Server is returning a stream of new posts
			# Patiently receive the stream of strings from server
			if (data_components[1] == 'NewPosts'):

				# Accept the list of new posts
				postComponentsList = []
				receiveStream(postComponentsList, 'BeginNewPosts', 'PostComponentRecvd', 'EndNewPosts')
				self.processNewPosts(postComponentsList)
		
		sock.close()

	# Process each new post in a given string list
	# Involves examing each item in the format:
	# '#NewPostData#PostInfo#[postID]#[sender]#[bookname]#[pagenum]#[linenum]|#PostContent#[postId]#[postContent]''
	def processNewPosts(self, newPostsList):

		# Parse and insert each post item into db
		for newPostStr in newPostsList:
			postData = newPostStr.split('#NewPostData')[1]
			postInfoStr = postData.split('|')[0]
			postContentStr = postData.split('|')[1]			
			readerDB.insertPost(postInfoStr, postContentStr)

		# Update all the books	
		for bookname in books.keys():
			books[bookname].update()	
	

# ----------------------------------------------------
# FUNCTIONS
# ----------------------------------------------------

def runDBTests():
	# DEBUGGING

	# Test inserting forum posts
	# postInfoString: 	'#PostInfo#Id#SenderName#BookName#PageNumber#LineNumber'
	# postContentString: 	'#PostContent#Id#Content'
	postInfoStr = "#PostInfo#3093#iancwwong#shelley#2#9"
	postContentStr = "#PostContent#3093#Why is this line blank?"
	readerDB.insertPost(postInfoStr, postContentStr)

	postInfoStr = "#PostInfo#3094#thetoxicguy#shelley#2#9"
	postContentStr = "#PostContent#3094#Because the author wrote it that way, you retard?"
	readerDB.insertPost(postInfoStr, postContentStr)

	postInfoStr = "#PostInfo#2041#jasonng#exupery#3#4"
	postContentStr = "#PostContent#2041#What's this line # talking about?"
	readerDB.insertPost(postInfoStr, postContentStr)

	postInfoStr = "#PostInfo#5699#mohawk#joyce#1#2"
	postContentStr = "#PostContent#5699#Repetition of 'my' is used."
	readerDB.insertPost(postInfoStr, postContentStr)

	readerDB.setRead(5699)
	print "Database:"
	print readerDB.exportAsStr()
	print ""

	print readerDB.getPostIDs('shelley', 2, 9)
	print ""

	displayPosts('shelley', 2, 9)

# Display the page contents from a particular book and page number
def displayPage(bookName, pageNum):
	
	# Submit a request for the contents of a page
	reqStr = '#DisplayReq#' + str(bookName) + '#' + str(pageNum)
	sock.send(reqStr)
		
	# Listen for response from server
	listenFor('DisplayResp')

	# Obtain the page contents
	pageContents = receiveStream('BeginDisplayResp', 'DisplayRespRcvd', 'EndDisplayResp')

	# Check if response contained no errors (response will contain a single error message)
	if (len(pageContents) == 1):
		pageContents = pageContents[0].split('#')
		if (pageContents[1] == 'Error'):
			return ('Error: ' + pageContents[2])

	# No errors - print each line on the page
	print "Book '%s', Page %s:" % (bookName, str(pageNum))
	for pageContent in pageContents:
		# Parse the string
		_, linenum, linecontent = pageContent.split('#')
		lineNum = int(linenum)

		# Determine whether any posts are read/unread on this line
		linePostsStatus = readerDB.consultPostsStatus(bookName, pageNum, lineNum)

		# Print appropriately
		print "%c  %d %s" % (linePostsStatus, lineNum, linecontent)

	return MSG_SUCCESS

# Request to find new posts for a particular bookname and page number
def updateLocalPosts(bookname, pagenum):
	
	# Request for a list of postID's that are associated with the bookname 
	# and page number
	reqStr = "#GetPostsIDReq#" + bookname + '#' + str(pagenum)
	sock.send(reqStr)

	# Listen for response from server
	# Format: '#PostsResp#[Postid],[Postid]...'
	msg = sock.recv(BUFFER_SIZE)
	msg_components = msg.split('#')
	if (msg_components[1] == 'Error'):
		return 'Error: ' + msg_components[2]
	
	# Extract list of postID's that are sent from server
	serverPostIDs = msg_components[2].split(',')
	serverPostIDs = [ int(postID) for postID in serverPostIDs ]		# Convert all into ints

	# Get a list of ID's that are in the list from the server, but
	# not owned locally at reader
	unknownPostIDs = [ postID for postID in serverPostIDs if postID not in readerDB.getPostIDs(bookname, pagenum) ]
	
	# Check if any posts are needed to be downloaded
	if (len(unknownPostIDs) == 0):
		print "Database is up to date!"
		return MSG_SUCCESS

	# Download the posts for each of these unknown post ID's'
	# Construct the string to send to server
	downloadReqStr = "#GetPostsReq#"
	for i in range(0, len(unknownPostIDs)):
		downloadReqStr = downloadReqStr + str(unknownPostIDs[i])
		if (i < len(unknownPostIDs) - 1):
			downloadReqStr = downloadReqStr + ','
	sock.send(downloadReqStr)

	# Listen for server response
	listenFor('GetPostsResp')
	
	# Receive the new posts as a stream
	# Each post will be of format:
	# '#PostInfo...|#PostContent'
	# postInfoString: 	'#PostInfo#Id#SenderName#BookName#PageNumber#LineNumber'
	# postContentString: 	'#PostContent#Id#Content'
	newPosts = receiveStream('BeginGetPostsResp', 'PostRcvd', 'EndGetPostsResp')
	print "New posts received: ", newPosts

	# Check for any errors

	# Insert each post into the database
	for post in newPosts:
		# Check for error
		post_components = post.split('#')
		if (post_components[1] == 'Error'):
			print 'Error: ' + post_components[2]
			continue

		postInfoString = post.split('|')[0]
		postContentString = post.split('|')[1]
		readerDB.insertPost(postInfoString, postContentString)
	print "Database updated!"

	return MSG_SUCCESS

# Display the posts for a particular book, page, and line
# Involves querying the database, given the bookName, pageNum, and lineNum
# NOTE: The given pageNum and lineNum are NOT index based
def displayPosts(bookName, pageNum, lineNum):

	print "Displaying posts:"

	# Obtain the list of post ids for the particular page and line
	postids = readerDB.getPostIDs(bookName, pageNum, lineNum)

	# Display the retrieved posts to the user
	print "From book '%s', Page %d, Line number %d:" % (bookName, pageNum, lineNum)
	if (len(postids) == 0):
		print "\tNo posts to display."
	else:
		for postid in postids:
			postInfo, postContent = readerDB.getPost(postid)
			senderName, _, _, _, readStatus = postInfo

			# Construct the string to be printed, containing the post
			printStr = ""
			if (readStatus == readerDB.UNREAD):
				printStr = printStr + "[UNREAD]"
			else:
				printStr = printStr + "        "
			printStr = printStr + " " + str(postid) + " " + senderName + ": " + postContent
			print printStr

			# Set the post to be read in the database
			readerDB.setRead(postid)

# Uploads a new post to the server
def sendNewPost(postInfoStr, postContentStr):

	# Use socket to send post
	newPostStr = '#UploadPost' + postInfoStr + '|' + postContentStr
	sock.send(newPostStr)

	# Listen for response from server
	msg = sock.recv(BUFFER_SIZE)
	msg_components = msg.split('#')
	if (msg_components[1] == 'Error'):
		return 'Error: ' + msg_components[2]
	else:
		return MSG_SUCCESS

# Send a stream of data to server, while controlling when the client
# should continue sending. Uses the reader socket to send messages.
# Note: Tacks on a '#' to endMsg and ackPhrase to adhere to message format rules
def sendStream(listToSend, startMsg, startAckPhrase, ackPhrase, endMsg):
	
	# Send start message
	sock.send('#' + startMsg)
	
	# Wait for an ack from server to start stream before sending stream items
	msg = selectRecv(BUFFER_SIZE)
	while (msg != ('#' + startAckPhrase)):
		msg = selectRecv(BUFFER_SIZE)

	# Ack received. Start sending stream
	# Ack received. Start sending stream
	for listItem in listToSend:
		sock.send(listItem)

		# Wait for user acknowledgement
		msg = selectRecv(BUFFER_SIZE)
		while (msg != ('#' + ackPhrase)):
			msg = selectRecv(BUFFER_SIZE)

	# Send end message to indicate (toserver) end of stream
	sock.send('#' + endMsg)

# Obtain a stream of data from server
# Returns a list of all the messages
# NOTE: Tacks on a '#' to ackPhrase to adhere to message format rules
def receiveStream(startAckPhrase, ackPhrase, endMsg):

	recvList = []
	
	# Send the startAckPhrase to indicate the server can begin stream sending
	sock.send('#' + startAckPhrase)

	# Begin receiving the stream
	msg = selectRecv(BUFFER_SIZE)
	while (msg == ""):
		msg = selectRecv(BUFFER_SIZE)
	msgComponents = msg.split('#')

	# Parse each stream message
	while (msgComponents[1] != endMsg):
		recvList.append(msg)
		
		# Send an ack that a stream message is received
		sock.send('#' + ackPhrase)
	
		# Re-listen for a stream message
		msg = selectRecv(BUFFER_SIZE)
		while (msg == ""):
			msg = selectRecv(BUFFER_SIZE)
		msgComponents = msg.split('#')
	return recvList	

# Listen for a particular message from the socket
def listenFor(listenMsg):
	msg = selectRecv(BUFFER_SIZE)
	while (msg != '#' + listenMsg):
		msg = selectRecv(BUFFER_SIZE)
	# Terminate waiting

# Use 'select' module to obtain data from buffer
def selectRecv(bufferSize):
	listen_sockets = [sock]
	read_sockets, write_sockets, error_sockets = select.select(listen_sockets, [], [])
	for rs in read_sockets:
		if (rs == sock):
			data = sock.recv(bufferSize)
			return data

# ----------------------------------------------------
# MAIN
# ----------------------------------------------------

#Usage: python reader.py mode polling_interval user_name server_name server_port_number

# Extract information from arguments provided
if (len(argv) < 6):
	print "Usage: python reader.py [mode] [poll interval] [user_name] [server_name] [server_port_number]"
	exit()
script, opmode, poll_interval_str, user_name, server_name, server_port_str = argv
server_port = int(server_port_str)
poll_interval = int(poll_interval_str)

# Initialise global variables
currentBookname = ""
currentPagenumber = 0
reader_exit_req = False
MSG_SUCCESS = 'OK'

# Constants
BUFFER_SIZE = 1024

# DEBUGGING
print "Username: \t", user_name
print "Connecting to: \t", server_name
print "At port: \t", server_port
print "Mode: \t\t",opmode
print "Poll interval: \t",poll_interval

# Initialise Reader Database
print "Initialising reader database..."
readerDB = ReaderDB()

# DEBUGGING
#runDBTests()
#exit()

# Prepare the socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)	# TCP

# Attempt to connect to server
print "Connecting to server '%s'..." % server_name
try:
	sock.connect((server_name, server_port))
except socket.error, e:
	print "Error connecting to server: %s" % e
	exit()
print "Successfully connected to server!"

# Start the listening thread
#print "Starting listening thread..."
#listenThread = ListenThread(sock)
#listenThread.start()

# Send intro message with info about this client
intro_message = "#Intro#" + user_name + "#" + opmode + "#" + str(poll_interval)
sock.send(intro_message)
print "Sent message: ", intro_message

# Run the reader
commands = ['exit', 'help', 'display', 'post_to_forum', 'read_post']
while (not reader_exit_req):
	print ""	# formatting

	user_input = raw_input('> ')
	user_input = user_input.split(' ')

	# Send an exit message to server before shutting down reader
	if (user_input[0] == 'exit' or user_input[0] == 'q'):	
		print "Saying goodbye to server..."
		exit_message = "#Exit#" + user_name
		sock.send(exit_message)
		reader_exit_req = True

	# Print documentation of valid commands
	elif (user_input[0] == 'help'):
		print "Valid commands:"	
		print commands

	# Display the page of the specified book
	elif (user_input[0] == 'display'):
		if (len(user_input) < 3):
			print "Usage: display [book_name] [page_number]"
			continue
		bookname = user_input[1]
		pagenum = int(user_input[2])
		
		# Display the page
		resp = displayPage(bookname, pagenum)

		# Examine if display was without errors
		if (resp == MSG_SUCCESS):
			currentBookname = bookname
			currentPagenumber = pagenum
		else:
			print "Could not display page. %s" % resp

	# Send a new post to the server
	elif (user_input[0] == 'post_to_forum'):

		# Check if currentBookname/cuirrentPagenum is initialised
		if (currentBookname == "" or currentPagenumber == ""):
			print "Uncertain book and page. Use the command 'display' to initialise."
			continue

		# Check if command is used properly
		if (len(user_input) < 3):
			print "Usage: post_to_forum [line number] [post content]"
			continue

		# Check if given line number is valid
		try:
			postLine = int(user_input[1])
		except ValueError:
			print "Invalid line number '%s' to post to." % user_input[1]
			continue			

		# Construct the post content string
		postContent = ' '.join(user_input[2:])	

		# Create the two strings for the post:
		# postInfoString: 	'#NewPostInfo#SenderName#BookName#PageNumber#LineNumber'
		# postContentString: 	'#NewPostContent#Content'
		postInfoStr = "#NewPostInfo#" + user_name + "#" + currentBookname + "#" \
				+ str(currentPagenumber) + "#" + str(postLine)
		postContentStr = "#NewPostContent#" + postContent

		print "Posting to forum..."
		resp = sendNewPost(postInfoStr, postContentStr)
		
		# Examine if post was successfully posted
		if (resp == MSG_SUCCESS):
			print "Successfully posted!"
		else:
			print "Could not post. %s" % resp

	# Display the posts for a particular line number on the current book and page
	elif (user_input[0] == 'read_post'):
		if (len(user_input) < 2):
			print "Usage: read_post [line number]"
			continue
		postsLine = int(user_input[1])
	
		# Check if currentBookname is initialised
		if (currentBookname == ""):
			print "Uncertain book. Use the command 'display' to initialise."
			continue

		# Display posts at the current book, page, and line
		displayPosts(currentBookname, currentPagenumber, postsLine)

	# Update the database with server
	elif (user_input[0] == 'serversync'):
		
		# Check if currentBookname/cuirrentPagenum is initialised
		if (currentBookname == "" or currentPagenumber == 0):
			print "Uncertain book and page. Use the command 'display' to initialise."
			continue

		resp = updateLocalPosts(currentBookname, currentPagenumber)

		# Examine if posts were successfully updated
		if (resp != MSG_SUCCESS):
			print "Could not update posts. %s" % resp
	
	# Unknown command
	else:
		print "Unrecognised command:", user_input[0]

# close the connection
print "Shutting down reader..."
#listenThread.event.set()
print "Exiting..."
