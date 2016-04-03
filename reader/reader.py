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

	def __init__(self, bookname):
		self.bookname = bookname
		
		# Construct the book with pages and lines
		self.pages = []

		# Determine number of pages
		self.numpages = len([name for name in os.listdir(bookname)])

		# Initialise the page objects by reading each page file
		for pagenum in range(1,self.numpages+1):
			pageObj = Page(bookname, pagenum)	# page numbers need an offset
			self.pages.append(pageObj)

	# Return the string in a particular page with message indication
	# Note: Assumes pageNum starts at 1 (NOT index based)
	def displayPage(self,pageNum):
		print self.pages[pageNum-1].showPage()

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

# This is a class that represents a line
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

# Determine list of books based on the file
# containing information about all books
bookListInfo = open('booklist','r').read().split('\n')
for line in bookListInfo
bookList.remove('')

# Initialise Book objects, storing them into a dict
print "Loading books..."
books = {}
for bookname in bookList:
	books[bookname] = Book(bookname)

# DEBUGGING
books["joyce"].displayPage(3)
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

	if (user_input == 'exit'):	
		# Send an exit message to server before shutting down reader
		print "Saying goodbye to server"
		exit_message = "#Exit#" + user_name
		sock.send(exit_message)
		reader_exit_req = True

	else:
		print "Unrecognised command:",user_input

# close the connection
print "Shutting down reader..."
sock.close()
