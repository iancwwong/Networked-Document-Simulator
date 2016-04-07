# This is the reader component of the e-book/server system

import time
import socket
from sys import argv
import os
import os.path

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
		try:
			print self.pages[pageNum-1].showPage()
		except IndexError:
			print "No such page exists"

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

		# Check that the lineNum is valid
		if (not self.pages[pageNum-1].hasLine(lineNum)):
			print "Error: page number %d not found." % pageNum

		# Obtain the list of posts for the particular page and line
		# Format: [ (postID, senderName, content, read/unread) ]
		posts = self.db.getPosts(self.bookname, pageNum, lineNum)
		
		# Display the retrieved posts to the user
		print "From book by %s, Page %d, Line number %d" % (self.author, pageNum, lineNum)
		print "Displaying posts for the line: %s" % (self.pages[pageNum-1].getLineContent(lineNum))
		for post in posts:
			postID, senderName, postcontent, readStatus = post
		
			# Construct the string to be printed, containing the post
			printStr = ""
			if (readStatus == self.UNREAD_POST):
				printStr = printStr + "[UNREAD]"
			printStr = printStr + "\t" + str(postID) + " " + senderName + ": " + postcontent
			print printStr
			print "\n"

			# Set the post to be read in the database
			self.db.setRead(postID)
		
		# Set the posts on the line to be 'read'
		self.setPostRead(pageNum, lineNum)		

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
			pageStr = pageStr + line.showLine() + "\n"
		return pageStr	

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
		linenum = lineNum-1
		if (linenum >= 0 and linenum < len(self.lines)):
			return True
		else: 
			return False
	

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
		return (self.post_chars[self.poststatus] + '  ' + str(self.linenum) + ' ' + self.linecontent)

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

	# Insert a new post, given a ForumPostObj
	# NOTE: Assumes the ForumPostObj is complete (ie contains ALL information)
	# NOTE: Each postID corresponds to exactly 1 postInfo and postContent entry
	def insertPost(self, forumPost):
		try:
			# Check whether there are tuples in the db for the book
			if (bool(self.db[forumPost.bookname]) == False):
				# Initialise the post info and post content dicts
				postInfo = {}
				postContent = {}
				self.db[forumPost.bookname] = (postInfo, postContent)

			# Complete the post info and post content dicts
			postInfo, postContent = self.db[forumPost.bookname]
			postInfo[forumPost.postID] = \
				(forumPost.sendername, forumPost.bookname, forumPost.pagenumber, \
				forumPost.linenumber, forumPost.readstatus)
			postContent[forumPost.postID] = forumPost.postcontent
			
		except KeyError:
			print "Error: Book %s does not exist in database" % (forumPost.bookname)

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
		

# This class represents a forum post
class ForumPostObj(object):
	
	# Constants
	UNREAD = 1
	READ = 2	

	# Constructor given the two strings that formulate the post
	# postInfoString: 	'#PostInfo#Id#SenderName#BookName#PageNumber#LineNumber#Read/Unread'
	# postContentString: 	'#PostContent#Id#Content'
	def __init__(self, postInfoString, postContentString):
		# Split strings on '#'
		postInfoComponents = postInfoString.split('#')		
		postContentComponents = postContentString.split('#')

		# Check that the two given id's are the same
		if (postInfoComponents[2] != postContentComponents[2]):
			print "Error creating forum post object - ID's are not the same!"
			return
		
		# Parse and set the forum post based on the split strings
		self.postID = postInfoComponents[2]
		self.sendername = postInfoComponents[3]	
		self.bookname = postInfoComponents[4]
		self.pagenumber = int(postInfoComponents[5])
		self.linenumber = int(postInfoComponents[6])
		self.readstatus = int(postInfoComponents[7])
		self.postcontent = postContentComponents[3]


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
	forumPostObj = ForumPostObj(postInfoStr, postContentStr)
	readerDB.insertPost(forumPostObj)

	postInfoStr = "#PostInfo#3094#thetoxicguy#shelley#2#9#1"
	postContentStr = "#PostContent#3094#Because the author wrote it that way, you retard?"
	forumPostObj = ForumPostObj(postInfoStr, postContentStr)
	readerDB.insertPost(forumPostObj)

	postInfoStr = "#PostInfo#2041#jasonng#exupery#3#4#1"
	postContentStr = "#PostContent#2041#What's this line talking about?"
	forumPostObj = ForumPostObj(postInfoStr, postContentStr)
	readerDB.insertPost(forumPostObj)

	postInfoStr = "#PostInfo#5699#mohawk#joyce#1#2#1"
	postContentStr = "#PostContent#5699#Repetition of 'my' is used."
	forumPostObj = ForumPostObj(postInfoStr, postContentStr)
	readerDB.insertPost(forumPostObj)

	# Update the books
	books['shelley'].displayPage(2)
	print "Updating the book..."
	books['shelley'].update()
	books['shelley'].displayPage(2)

#Usage: python reader.py mode polling_interval user_name server_name server_port_number

# Extract information from arguments provided
if (len(argv) < 6):
	print "Usage: python reader.py [mode] [poll interval] [user_name] [server_name] [server_port_number]"
	exit()
script, opmode, poll_interval_str, user_name, server_name, server_port_str = argv
server_port = int(server_port_str)
poll_interval = int(poll_interval_str)

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

# Initialise global currentBookname, currentPagenum, and currentLinenum
currentBookname = ""
currentPagenum = 0
currentLinenum = 0

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

# Send intro message with info about this client
intro_message = "#Intro#" + user_name + "#" + opmode + "#" + str(poll_interval)
sock.send(intro_message)

# Run the reader
reader_exit_req = False
while (not reader_exit_req):
	
	# Read and parse the user input
	user_input = raw_input('> ')
	user_input = user_input.split(' ')

	# Send an exit message to server before shutting down reader
	if (user_input[0] == 'exit'):	
		print "Saying goodbye to server..."
		exit_message = "#Exit#" + user_name
		sock.send(exit_message)
		reader_exit_req = True

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

	# Display the posts for a particular line number on the current book and page
	elif (user_input[0] == 'read_post'):
		if (len(user_input) < 2):
			print "Usage: read_post [line number]"
			continue
		
		postsLine = int(user_input[1])
		books[currentBookname].displayPosts(currentPagenumber, postsLine)

	else:
		print "Unrecognised command:", user_input[0]

# close the connection
print "Shutting down reader..."
sock.close()
