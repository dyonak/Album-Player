#!/bin/bash

# deploy-to-pi.sh - Quick deployment script for Album Player development
# Syncs code changes to the Pi and restarts services

set -e

# Change to project root directory
cd "$(dirname "$0")/.."

# Configuration (override with environment variables)
PI_USER="${PI_USER:-dyonak}"
PI_HOST="${PI_HOST:-fruit-loops.local}"
PI_CODE_DIR="${PI_CODE_DIR:-/home/${PI_USER}/album-player}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Album Player Deploy ===${NC}"
echo "Target: ${PI_USER}@${PI_HOST}:${PI_CODE_DIR}"
echo ""

# Step 1: Check connection
echo -e "${YELLOW}[1/5] Checking connection to Pi...${NC}"
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes ${PI_USER}@${PI_HOST} exit 2>/dev/null; then
    echo -e "${RED}Error: Cannot connect to ${PI_USER}@${PI_HOST}${NC}"
    echo ""
    echo "Please check:"
    echo "  - Pi is powered on and connected to network"
    echo "  - SSH keys are set up: ssh-copy-id ${PI_USER}@${PI_HOST}"
    echo "  - Hostname is correct"
    echo ""
    echo "Override with environment variables:"
    echo "  PI_HOST=192.168.1.x PI_USER=myuser ./deploy-to-pi.sh"
    exit 1
fi
echo -e "${GREEN}Connected${NC}"

# Step 2: Ensure target directory exists
echo -e "${YELLOW}[2/5] Ensuring target directory exists...${NC}"
ssh ${PI_USER}@${PI_HOST} "mkdir -p ${PI_CODE_DIR}"
echo -e "${GREEN}Directory ready${NC}"

# Step 3: Sync code files
echo -e "${YELLOW}[3/5] Syncing code files...${NC}"
rsync -avz --progress \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.venv' \
    --exclude='venv' \
    --exclude='my_venv' \
    --exclude='db' \
    --exclude='.DS_Store' \
    --exclude='*.swp' \
    --exclude='.idea' \
    --exclude='.vscode' \
    --exclude='.claude' \
    ./ \
    ${PI_USER}@${PI_HOST}:${PI_CODE_DIR}/
echo -e "${GREEN}Files synced${NC}"

# Step 4: Update service files and configs
echo -e "${YELLOW}[4/5] Updating service files and configs...${NC}"
ssh ${PI_USER}@${PI_HOST} << 'ENDSSH'
cd ~/album-player

# Update spotifyd config
if [ -f spotifyd.conf ]; then
    mkdir -p ~/.config/spotifyd
    cp spotifyd.conf ~/.config/spotifyd/spotifyd.conf
    echo "  spotifyd.conf updated"
fi

# Update service files if changed
for service in wificonnect webapp spotifyd albumplayer; do
    if [ -f "services/${service}.service" ]; then
        sudo cp "services/${service}.service" /etc/systemd/system/
    fi
done
sudo systemctl daemon-reload
echo "  Service files updated"
ENDSSH
echo -e "${GREEN}Configs updated${NC}"

# Step 5: Restart services
echo -e "${YELLOW}[5/5] Restarting services...${NC}"
ssh ${PI_USER}@${PI_HOST} << 'ENDSSH'
# Restart each service, ignoring errors if not installed
sudo systemctl restart spotifyd.service 2>/dev/null && echo "  spotifyd restarted" || echo "  spotifyd not running"
sudo systemctl restart webapp.service 2>/dev/null && echo "  webapp restarted" || echo "  webapp not running"
sudo systemctl restart albumplayer.service 2>/dev/null && echo "  albumplayer restarted" || echo "  albumplayer not running"
ENDSSH
echo -e "${GREEN}Services restarted${NC}"

echo ""
echo -e "${GREEN}=== Deployment Complete! ===${NC}"
echo ""
echo "View logs:"
echo "  journalctl -u albumplayer -f    # NFC + playback"
echo "  journalctl -u webapp -f         # Web interface"
echo "  journalctl -u spotifyd -f       # Spotify Connect"
echo ""
echo "Web UI: http://${PI_HOST}:3029"
echo ""
