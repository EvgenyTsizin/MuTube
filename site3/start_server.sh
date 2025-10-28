#!/bin/bash
# Start Python HTTP server on port 8000
python3 -m http.server 8000
# Wait for user input to close
read -p "Press [Enter] key to stop the server..."

