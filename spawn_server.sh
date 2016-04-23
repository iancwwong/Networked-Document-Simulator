#!/usr/bin/sh

# Spawn the server terminal
cd server
xterm -hold -title "Server" -e "python server_ex.py 25001"

