#!/usr/bin/sh

cd reader

# Spawn the pull clients
xterm -hold -title "Sheldon" -e "python reader_ex.py pull 180 Sheldon ubuntu 25001" & 

xterm -hold -title "Leonard" -e "python reader_ex.py pull 180 Leonard ubuntu 25001" & 

xterm -hold -title "Penny" -e "python reader_ex.py pull 180 Penny ubuntu 25001" &

# Spawn the push clients
xterm -hold -title "Amy" -e "python reader_ex.py push 180 Amy ubuntu 25001"
