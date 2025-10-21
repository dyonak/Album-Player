#!/bin/bash

# deploy-to-pi.sh - Quick deployment script for Album Player development
# This syncs code changes to the Pi and restarts the container

cd ../
set -e  # Exit on error

# Configuration
PI_USER="${PI_USER:-dyonak}"
PI_HOST="${PI_HOST:-fruit-loops.local}"
PI_CODE_DIR="${PI_CODE_DIR:-/home/${PI_USER}/album-player}"
CONTAINER_NAME="${CONTAINER_NAME:-album-player}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Album Player Quick Deploy ===${NC}"
echo "Target: ${PI_USER}@${PI_HOST}:${PI_CODE_DIR}"
echo ""

# Check if we can reach the Pi
echo -e "${YELLOW}[1/4] Checking connection to Pi...${NC}"
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes ${PI_USER}@${PI_HOST} exit 2>/dev/null; then
    echo -e "${RED}Error: Cannot connect to ${PI_USER}@${PI_HOST}${NC}"
    echo "Please check:"
    echo "  - Pi is powered on and connected to network"
    echo "  - SSH keys are set up (run: ssh-copy-id ${PI_USER}@${PI_HOST})"
    echo "  - Hostname is correct (you can override with: PI_HOST=192.168.1.x ./deploy-to-pi.sh)"
    exit 1
fi
echo -e "${GREEN}✓ Connected${NC}"

# Ensure the target directory exists
echo -e "${YELLOW}[2/4] Ensuring target directory exists...${NC}"
ssh ${PI_USER}@${PI_HOST} "mkdir -p ${PI_CODE_DIR}"
echo -e "${GREEN}✓ Directory ready${NC}"

# Sync code files
echo -e "${YELLOW}[3/4] Syncing code files...${NC}"
rsync -avz --progress \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.venv' \
    --exclude='venv' \
    --exclude='db' \
    --exclude='.DS_Store' \
    --exclude='*.swp' \
    --exclude='.idea' \
    --exclude='.vscode' \
    ./ \
    ${PI_USER}@${PI_HOST}:${PI_CODE_DIR}/
echo -e "${GREEN}✓ Files synced${NC}"

# Restart the container with docker compose to ensure volume mounts are active
echo -e "${YELLOW}[4/4] Restarting container...${NC}"
ssh ${PI_USER}@${PI_HOST} "cd ${PI_CODE_DIR} && docker compose down && docker compose up -d"
echo -e "${GREEN}✓ Container restarted${NC}"

echo ""
echo -e "${GREEN}=== Deployment Complete! ===${NC}"
echo ""
echo "Next steps:"
echo "  - View logs: ssh ${PI_USER}@${PI_HOST} 'docker logs -f ${CONTAINER_NAME}'"
echo "  - SSH to Pi: ssh ${PI_USER}@${PI_HOST}"
echo ""
echo "To customize settings, set environment variables:"
echo "  PI_HOST=192.168.1.100 PI_USER=myuser ./deploy-to-pi.sh"
