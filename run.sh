#!/bin/bash

# run.sh - Manual startup script for Album Player
# Note: In production, use systemd services instead:
#   sudo systemctl start albumplayer
#   sudo systemctl start webapp

echo "============================================"
echo "Album Player - Manual Start"
echo "============================================"
echo ""
echo "For production use, enable and start the systemd services:"
echo "  sudo systemctl enable --now albumplayer"
echo "  sudo systemctl enable --now webapp"
echo "  sudo systemctl enable --now spotifyd"
echo ""
echo "Starting Album Player NFC service..."
echo ""

python3 ./AlbumPlayer.py
