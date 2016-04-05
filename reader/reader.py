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
	
	db = {}

	# Constructor, given the parsed information from the 'booklist' file
	def __init__(self, booklist):
		# Initialise the dicts
		for book in booklist:
			bookname, bookauthor = book
			self.db[bookname] = {}

	# Insert a new post, given a ForumPostObj
	#def insertPost(self, forumPost):
		
		

# This class represents a forum post
# postInfoString: '#PostInfo#Id#SenderName#PageNumber#LineNumber#Read/Unread'
# postContent: '#PostContent#Id#Content'
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

		print "Postinfcomp:",postInfoComponents
		print "PostContComp:",postContentComponents

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

	# Show details
	def showPostDetails(self):
		print "ID:",self.postID
		print "Sender:",self.sendername
		print "Book name:",self.bookname
		print "Page:",self.pagenumber
		print "Line:",self.linenumber
		if (self.readstatus == self.UNREAD):
			print "Read: Unread"
		elif (self.readstatus == self.READ):
			print "Read: Read"
		print "Content:",self.postcontent


# ----------------------------------------------------
# MAIN
# ----------------------------------------------------

#Usage: python reader.py mode polling_interval user_name server_name server_port_number

# Extract information from arguments provided
if (len(argv) < 6):
	print "Usage: python reader.py [mode] [poll interval] [user_name] [server_name] [server_port_number]"
	exit()
script, opmode, poll_interval, user_name, server_name, server_port_str = argv
server_port = int(server_port_str)

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

# Initialise Book objects, storing them into a dict
print "Loading books..."
books = {}
for book in booklist:
	book_dir, book_author = book			# Book_dir is equivalent to book's name
	books[book_dir] = Book(book_dir, book_author)

# Initialise Reader Database
print "Initialising reader database..."
readerDB = ReaderDB(booklist)

# DEBUGGING
	# postInfoString: 	'#PostInfo#Id#SenderName#BookName#PageNumber#LineNumber#Read/Unread'
	# postContentString: 	'#PostContent#Id#Content'
postInfoStr = "#PostInfo#3093#iancwwong#shelley#2#9#1"
postContentStr = "#PostContent#3093#Why is this line blank?"
forumPostObj = ForumPostObj(postInfoStr, postContentStr)
forumPostObj.showPostDetails()
exit()

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
intro_message = "#Intro#" + user_name + "#" + opmode
sock.send(intro_message)

# Run the reader
reader_exit_req = False
while (not reader_exit_req):
	
	# Read and parse the user input
	user_input = raw_input('> ')
	user_input = user_input.split(' ')

	if (user_input[0] == 'exit'):	
		# Send an exit message to server before shutting down reader
		print "Saying goodbye to server"
		exit_message = "#Exit#" + user_name
		sock.send(exit_message)
		reader_exit_req = True

	elif (user_input[0] == 'display'):
		if (len(user_input) < 3):
			print "Usage: display [book_name] [page_number]"
			continue
		
		# Display the page of the specified book
		book_name = user_input[1]
		page_num = int(user_input[2])
		try:
			books[book_name].displayPage(page_num)
		except KeyError:
			print "Book name '%s' invalid" % book_name
			continue	

	else:
		print "Unrecognised command:", user_input[0]

# close the connection
print "Shutting down reader..."
sock.close()
