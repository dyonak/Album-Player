#!/bin/bash

# upgrade.sh - Upgrade Album Player to latest Docker image
# Run this script on the Raspberry Pi to pull the latest image and restart the container

set -e  # Exit on error

# Configuration
DOCKER_USERNAME="${DOCKER_USERNAME:-dyonak}"
IMAGE_NAME="albumplayer"
TAG="${1:-latest}"
FULL_IMAGE_NAME="${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}"
COMPOSE_FILE="docker-compose.yml"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      Album Player Upgrade Script              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Image:${NC} ${FULL_IMAGE_NAME}"
echo ""

# Check if docker-compose.yml exists
if [ ! -f "${COMPOSE_FILE}" ]; then
    echo -e "${RED}Error: ${COMPOSE_FILE} not found${NC}"
    echo "This script must be run from the album-player directory"
    exit 1
fi

# Check if Docker is available
echo -e "${YELLOW}[1/5] Checking Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not available${NC}"
    echo "Try running with sudo: sudo ./upgrade.sh"
    exit 1
fi
echo -e "${GREEN}✓ Docker is available${NC}"

# Show current container status
echo -e "${YELLOW}[2/5] Current container status...${NC}"
docker compose ps 2>/dev/null || true

# Pull the latest image
echo -e "${YELLOW}[3/5] Pulling latest image from Docker Hub...${NC}"
echo -e "${BLUE}Pulling: ${FULL_IMAGE_NAME}${NC}"
docker compose pull

# Stop the current container
echo -e "${YELLOW}[4/5] Stopping current container...${NC}"
docker compose down

# Start with the new image
echo -e "${YELLOW}[5/5] Starting updated container...${NC}"
docker compose up -d

# Wait a moment for the container to start
sleep 3

# Show new container status
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║            Upgrade Complete! ✓                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Container status:${NC}"
docker compose ps

echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  • View logs: ${BLUE}docker compose logs -f${NC}"
echo -e "  • Check status: ${BLUE}docker compose ps${NC}"
echo -e "  • Restart: ${BLUE}docker compose restart${NC}"
echo ""
