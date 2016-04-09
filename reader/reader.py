# This is the reader component of the e-book/server system

import socket
import select
import threading
from sys import argv
import sys
import os
import os.path
import time

# ----------------------------------------------------
# CLASSES
# ----------------------------------------------------

# This class represents a book
class Book(object):

	# Constants
	UNREAD_POST = 1
	READ_POST = 2

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

	# Return the string in a particular page with message indication
	# Note: Assumes pageNum starts at 1 (NOT index based)
	def displayPage(self,pageNum):
		if (not self.hasPage(pageNum)):
			print "Page %d does not exist." % (pageNum)
			return
		print "%s Page %d:" % (self.bookname, pageNum)
		self.pages[pageNum-1].showPage()

	# Link up the book with a database for queries about post statuses
	def linkDB(self, dbObj):
		self.db = dbObj
	
	# Updates the book by changing the post status on certain lines
	# Involves querying the linked database
	def update(self):
		
		# Obtain the list of posts with their statuses
		postsStatuses = self.db.getBookPostStatuses(self.bookname)
		
		# Loop through each post and set read/unread accordingly
		for postTuple in postsStatuses:
			# Format: [ (status, bookname, pagenum, linenum) ]
			status, pagenum, linenum = postTuple
			if (status == self.UNREAD_POST):
				self.setPostUnread(pagenum, linenum)
			elif (status == self.READ_POST):
				self.setPostRead(pagenum, linenum)

	# Display the posts for a particular page and line
	# Involves querying the linked database
	# NOTE: The given pageNum and lineNum are NOT index based
	def displayPosts(self, pageNum, lineNum):
	
		try:
			# Check that the lineNum is valid
			if (not self.pages[pageNum-1].hasLine(lineNum)):
				print "Error: line number %d not found." % lineNum
				return ""

			# Obtain the list of posts for the particular page and line
			# Format: [ (postID, senderName, content, read/unread) ]
			posts = self.db.getPosts(self.bookname, pageNum, lineNum)
		
			# Display the retrieved posts to the user
			print "From book by %s, Page %d, Line number %d:" % (self.author, pageNum, lineNum)	
			print '"%s"' % self.pages[pageNum-1].getLineContent(lineNum)
			print "Displaying posts:"
			if (len(posts) == 0):
				print "\tNo posts to display."
			else:
				for post in posts:
					postID, senderName, postcontent, readStatus = post
		
					# Construct the string to be printed, containing the post
					printStr = ""
					if (readStatus == self.UNREAD_POST):
						printStr = printStr + "[UNREAD]"
					printStr = printStr + "\t" + str(postID) + " " + senderName + ": " + postcontent
					print printStr

					# Set the post to be read in the database
					self.db.setRead(postID)

				# Set the posts on the line to be 'read'
				self.setPostRead(pageNum, lineNum)

		except KeyError:
			print "Error: Page not found"		

	# Set a post to be read at a particular line in a particular page
	# NOTE: Page and Line are NOT index based as arguments
	def setPostRead(self, pageNum, lineNum):
		try:
			self.pages[pageNum-1].setPostRead(lineNum)
		except IndexError:
			print "No such page exists"

	# Set a post to be read at a particular line in a particular page
	# NOTE: Page and Line are NOT index based as arguments
	def setPostUnread(self, pageNum, lineNum):
		try:
			self.pages[pageNum-1].setPostUnread(lineNum)
		except IndexError:
			print "No such page exists"

	# Checks whether the page exists
	# NOTE: pageNum is NOT index based
	def hasPage(self, pageNum):
		return (pageNum-1 in range(0, len(self.pages)))	

	# Checks whether book has a line on a particular page
	# NOTE: pageNum and lineNum are NOT index based
	def hasLine(self, pageNum, lineNum):
		try:
			return self.pages[pageNum-1].hasLine(lineNum)
		except IndexError:
			print "No such page exists"
		
			

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

	# Show the contents of the page with message indication on each line
	def showPage(self):
		pageStr = ""
		for line in self.lines:
			line.showLine()

	# Return the contents of a line
	# NOTE: lineNum is NOT index based
	def getLineContent(self, lineNum):
		return self.lines[lineNum-1].getLineContent()

	# Set a post to be read at a particular line
	# NOTE: lineNum is NOT index based
	def setPostRead(self, lineNum):
		try:
			self.lines[lineNum-1].setPostRead()
		except IndexError:
			print "No such line exists"

	# Set a post to be read at a particular line in a particular page
	# NOTE: Page and Line are NOT index based as arguments
	def setPostUnread(self, lineNum):
		try:
			self.lines[lineNum-1].setPostUnread()
		except IndexError:
			print "No such page exists"

	# Returns whether there is a particular line number in the page
	# NOTE: lineNum is NOT index based
	def hasLine(self, lineNum):
		return (lineNum-1 in range(0, len(self.lines)))
	

# This is a class that represents a line on a page
class Line(object):

	# Constants	
	NO_POST = 0
	UNREAD_POST = 1
	READ_POST = 2

	# Corresponding Post Characters
	post_chars = { NO_POST: ' ', UNREAD_POST: 'n', READ_POST: 'm' }
		
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
		
		# Set the line post status
		self.poststatus = self.NO_POST

	# Show the contents of the page with message indication on each line
	# with format: post status, 2 spaces, line number, 1 space, line content		
	def showLine(self):
		print (self.post_chars[self.poststatus] + '  ' + str(self.linenum) + ' ' + self.linecontent)

	# Get the contents of the line
	def getLineContent(self):
		return self.linecontent
		
	# Set the status of forum posts on this line as 'Read'
	def setPostRead(self):
		self.poststatus = self.READ_POST

	# Set the status of forum posts on this line as 'Unread'
	def setPostUnread(self):
		self.poststatus = self.UNREAD_POST
		
# This class represents the database for the reader
# Contains a database dict with tuples of the post info, and post content
# ie db = { "bookname": (postInfo, postContent) }
#    postInfo = { "postID": (senderName, pageNumber, lineNumber, read/unread) }
#    postContent = { "postID": content }
class ReaderDB(object):

	# Constants
	UNREAD = 1
	READ = 2
	
	# Storing forum posts for each book
	db = {}

	# Constructor, given the parsed information from the 'booklist' file
	def __init__(self, booklist):
		# Initialise the dicts
		for book in booklist:
			bookname, bookauthor = book
			self.db[bookname] = {}

	# Insert a new post, given two strings:
	# postInfoString: 	'#PostInfo#Id#SenderName#BookName#PageNumber#LineNumber#Read/Unread'
	# postContentString: 	'#PostContent#Id#Content' 
	# NOTE: Each postID corresponds to exactly 1 postInfo and postContent entry
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
		postID = postInfoComponents[2]
		sendername = postInfoComponents[3]	
		bookname = postInfoComponents[4]
		pagenumber = int(postInfoComponents[5])
		linenumber = int(postInfoComponents[6])
		readstatus = int(postInfoComponents[7])		# ToFix: This should NOT be here. It should be, by default, 'UNREAD'
		postcontent = postContentComponents[3]		# ToFix: If content string has a '#', this will be wrong

		try:
			# Check whether there are tuples in the db for the book
			if (bool(self.db[bookname]) == False):
				# Initialise the post info and post content dicts
				postInfo = {}
				postContent = {}
				self.db[bookname] = (postInfo, postContent)

			# Complete the post info and post content dicts
			postInfo, postContent = self.db[bookname]
			postInfo[postID] = (sendername, bookname, pagenumber, linenumber, readstatus)
			postContent[postID] = postcontent
			
		except KeyError:
			print "Error: Book %s does not exist in database" % (bookname)

	# Send a list of post statuses at a specific book, on pages and lines
	# Format: [ (status, pagenum, linenum) ]
	def getBookPostStatuses(self, bookname):
		statusList = []
		
		# Examine posts in the given bookname
		try:
			if (not self.db[bookname]):
				return []
			postInfo, postContent = self.db[bookname]
			for postID in postInfo.keys():
				
				# Add post status to list
				sender, bookname, pagenumber, linenumber, readstatus = postInfo[postID]
				statusList.append((readstatus, pagenumber, linenumber))
				
			return statusList

		except KeyError:
			print "Error: Book %s does not exist in database" % (bookname)

	# Return a list of posts for a particular book, page, and line
	# Format: [ (postID, senderName, postcontent, read/unread) ]
	def getPosts(self, bookName, pageNum, lineNum):

		# Loop through all posts in the given book, filtering only those
		# with the given page and line number
		postList = []
		
		# Check whether there are any posts for the book, page, and line
		try:
			if (bool(self.db[bookName] == False)):
				return []
			postInfo, postContent = self.db[bookName]
			for postID in postInfo.keys():
				sendername, bookname, pagenumber, linenumber, readstatus = postInfo[postID]
				postcontent = postContent[postID]
				if (bookname == bookName and pagenumber == pageNum and linenumber == lineNum):
					postList.append((postID, sendername, postcontent, readstatus))

			return postList			

		except KeyError:
			print "Error: book name %s not found." % bookName

	# Set a post read status to be 'Read'
	# NOTE: Assumes postID's are unique
	def setRead(self, readPostID):
		# Find the post with the given postID
		for bookName in self.db.keys():
			# Check whether it's empty
			if (bool(self.db[bookName]) == False):
				return
			postInfo, postContent = self.db[bookName]
			
			# Check whether there is a post with the given id
			if readPostID in postInfo.keys():
				sendername, bookname, pagenumber, linenumber, readstatus = postInfo[readPostID]
				postInfo[readPostID] = (sendername, bookname, pagenumber, linenumber, self.READ)
				return	

	# Export db as a string
	# postInfoString: 	'#PostInfo#Id#SenderName#BookName#PageNumber#LineNumber#Read/Unread'
	# postContentString: 	'#PostContent#Id#Content'
	def exportAsStr(self):
		# Loop through all books and posts
		dbStr = ""
		for bookName in self.db.keys():
			if (bool(self.db[bookName]) == False):
				continue
			postInfo, postContent = self.db[bookName]	
			for postID in postInfo.keys():
				sendername, bookname, pagenumber, linenumber, readstatus = postInfo[postID]
				dbStr = dbStr + "#PostInfo#" + str(postID) + "#" + sendername + "#" \
					+ bookname + "#" + str(pagenumber) + "#" + str(linenumber) + "#" \
					+ str(readstatus) + "\n"
				postcontent = postContent[postID]
				dbStr = dbStr + "#PostContent#" + str(postID) + "#" + postcontent + "\n"
		return dbStr

# This class is the thread that runs when reader is listening for input from server
class ListenThread(threading.Thread):

	# Constructor given the socket connected to the server
	def __init__(self,socket):
		threading.Thread.__init__(self)
		self.event = threading.Event()
		self.socket = socket

		# Add the client's socket to list of sockets
		self.listen_sockets = [self.socket]

	# Execute thread - constantly listen for messages
	# from the connected server
	def run(self):

		# Constantly listen for messages until event is set
		while not self.event.isSet():
				
			# Obtain lists of ready sockets
			read_sockets, write_sockets, error_sockets = select.select(self.listen_sockets, [], [])

			# Read any incoming data from the server	
			for rs in read_sockets:
				if rs == self.socket:
					data = rs.recv(BUFFER_SIZE)
					if data != "":
						print "Data received: ", data

		sock.close()
# ----------------------------------------------------
# MAIN
# ----------------------------------------------------

def runDBTests():
	# DEBUGGING

	# Test inserting forum posts
	# postInfoString: 	'#PostInfo#Id#SenderName#BookName#PageNumber#LineNumber#Read/Unread'
	# postContentString: 	'#PostContent#Id#Content'
	postInfoStr = "#PostInfo#3093#iancwwong#shelley#2#9#1"
	postContentStr = "#PostContent#3093#Why is this line blank?"
	readerDB.insertPost(postInfoStr, postContentStr)

	postInfoStr = "#PostInfo#3094#thetoxicguy#shelley#2#9#1"
	postContentStr = "#PostContent#3094#Because the author wrote it that way, you retard?"
	readerDB.insertPost(postInfoStr, postContentStr)

	postInfoStr = "#PostInfo#2041#jasonng#exupery#3#4#1"
	postContentStr = "#PostContent#2041#What's this line talking about?"
	readerDB.insertPost(postInfoStr, postContentStr)

	postInfoStr = "#PostInfo#5699#mohawk#joyce#1#2#1"
	postContentStr = "#PostContent#5699#Repetition of 'my' is used."
	readerDB.insertPost(postInfoStr, postContentStr)

	# Update the books
	#books['shelley'].displayPage(2)
	print "Updating the book..."
	books['shelley'].update()
	#books['shelley'].displayPage(2)
	books['exupery'].update()
	books['joyce'].update()
	
	print "Database:"
	print readerDB.exportAsStr()

# Uploads a new post to the server
def sendNewPost(postInfoStr, postContentStr):
	sock.send(postInfoStr)
	time.sleep(0.5)
	sock.send(postContentStr)

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
currentPagenum = 0
currentLinenum = 0
reader_exit_req = False

# DEBUGGING
print "Username: \t", user_name
print "Connecting to: \t", server_name
print "At port: \t", server_port
print "Mode: \t\t",opmode
print "Poll interval: \t",poll_interval

# Parse information about the books contained in the 'booklist' file
# with format: [book folder name],[book author]
booklist_file = open('booklist','r').read().split('\n')
booklist_file.remove('')
booklist = []
for line in booklist_file:
	line = line.split(',')
	booklist.append((line[0], line[1]))

# Initialise Reader Database
print "Initialising reader database..."
readerDB = ReaderDB(booklist)

# Initialise Book objects, storing them into a dict
print "Loading books..."
books = {}
for book in booklist:
	book_dir, book_author = book			# Book_dir is equivalent to book's name
	books[book_dir] = Book(book_dir, book_author)
	
	# Link the book with the database
	books[book_dir].linkDB(readerDB)

# DEBUGGING
runDBTests()

# Prepare the buffer size
BUFFER_SIZE = 1024

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
print "Starting listening thread..."
listenThread = ListenThread(sock)
listenThread.start()

# Send intro message with info about this client
intro_message = "#Intro#" + user_name + "#" + opmode + "#" + str(poll_interval)
sock.send(intro_message)

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

		book_name = user_input[1]
		page_num = int(user_input[2])
		try:
			books[book_name].displayPage(page_num)
			currentBookname = book_name
			currentPagenumber = page_num

		except KeyError:
			print "Book name '%s' invalid" % book_name
			continue

	# Send a new post to the server
	elif (user_input[0] == 'post_to_forum'):
		if (len(user_input) < 3):
			print "Usage: post_to_forum [line number] [post content]"
			continue

		# Check if book has line
		postLine = int(user_input[1])
		if (not books[currentBookname].hasLine(currentPagenumber, postLine)):
			print "Line %d does not exist on page %d in book '%s'" \
				% (postLine, currentPagenumber, currentBookname)
			continue
	
		# Construct the post content string
		postContent = ' '.join(user_input[2:])	

		# Create the two strings for the post:
		# postInfoString: 	'#NewPostInfo#SenderName#BookName#PageNumber#LineNumber'
		# postContentString: 	'#NewPostContent#Content'
		# NOTE: By default, the read status of a post composed by this client
		#       is 'READ'
		postInfoStr = "#NewPostInfo#" + user_name + "#" + currentBookname + "#" \
				+ str(currentPagenumber) + "#" + str(postLine)
		postContentStr = "#NewPostContent#" + postContent

		print "Posting to forum..."
		sendNewPost(postInfoStr, postContentStr)


	# Display the posts for a particular line number on the current book and page
	elif (user_input[0] == 'read_post'):
		if (len(user_input) < 2):
			print "Usage: read_post [line number]"
			continue
		postsLine = int(user_input[1])
	
		# Check if currentBookname is initialised
		if (currentBookname == ""):
			print "Uncertain book and page. Use the command 'display' to initialise."
			continue

		# Display posts at the current book, page, and line
		books[currentBookname].displayPosts(currentPagenumber, postsLine)
	
	# Unknown command
	else:
		print "Unrecognised command:", user_input[0]

# close the connection
print "Shutting down reader..."
listenThread.event.set()
print "Exiting..."
