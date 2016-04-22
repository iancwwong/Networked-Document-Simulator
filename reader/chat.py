# This file contains the code that executes as chat session (over udp)
# between this host and another given host

import socket
from sys import argv

# Extract the arguments
if (len(argv) < 3):
	print "Usage: python chat.py [port #] [target IP] [target port #]"
	exit()

script, myPortStr, targetIPStr, targetPortStr = argv
myPort = int(myPortStr)
targetIP = targetIPStr			# ToDO: convert this to long
targetPort = int(targetPortStr)

print "Setting up UDP connection with:"
print "IP:",targetIP
print "Port #:",targetPort
