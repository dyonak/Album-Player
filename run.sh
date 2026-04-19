#!/bin/bash

# Start the main application services
echo "Starting Album Player services..."
python3 ./Webapp.py &
python3 ./AlbumPlayer.py
