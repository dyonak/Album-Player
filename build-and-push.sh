#!/bin/bash

# build-and-push.sh - Build and push Album Player Docker image to Docker Hub
# Usage: ./build-and-push.sh [tag]
# Example: ./build-and-push.sh v1.2.3
# If no tag is provided, defaults to 'latest'

set -e  # Exit on error

# Configuration
DOCKER_USERNAME="${DOCKER_USERNAME:-dyonak}"
IMAGE_NAME="albumplayer"
TAG="${1:-latest}"
FULL_IMAGE_NAME="${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Album Player Docker Build & Push Script     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Image:${NC} ${FULL_IMAGE_NAME}"
echo ""

# Check if Docker is running
echo -e "${YELLOW}[1/5] Checking Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    echo "Please start Docker and try again"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"

# Check if logged in to Docker Hub
echo -e "${YELLOW}[2/5] Checking Docker Hub authentication...${NC}"
if ! docker info 2>/dev/null | grep -q "Username"; then
    echo -e "${YELLOW}! Not logged in to Docker Hub${NC}"
    echo "Please log in to Docker Hub:"
    docker login
fi
echo -e "${GREEN}✓ Authenticated to Docker Hub${NC}"

# Build the image
echo -e "${YELLOW}[3/5] Building Docker image...${NC}"
echo -e "${BLUE}Building: ${FULL_IMAGE_NAME}${NC}"
docker build -t "${FULL_IMAGE_NAME}" .

# Also tag as latest if a specific version tag was provided
if [ "${TAG}" != "latest" ]; then
    echo -e "${YELLOW}[4/5] Tagging as latest...${NC}"
    docker tag "${FULL_IMAGE_NAME}" "${DOCKER_USERNAME}/${IMAGE_NAME}:latest"
    echo -e "${GREEN}✓ Tagged as ${DOCKER_USERNAME}/${IMAGE_NAME}:latest${NC}"
else
    echo -e "${YELLOW}[4/5] Skipping additional tag (already latest)${NC}"
fi

# Push to Docker Hub
echo -e "${YELLOW}[5/5] Pushing to Docker Hub...${NC}"
echo -e "${BLUE}Pushing: ${FULL_IMAGE_NAME}${NC}"
docker push "${FULL_IMAGE_NAME}"

# Push latest tag if we created it
if [ "${TAG}" != "latest" ]; then
    echo -e "${BLUE}Pushing: ${DOCKER_USERNAME}/${IMAGE_NAME}:latest${NC}"
    docker push "${DOCKER_USERNAME}/${IMAGE_NAME}:latest"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          Build & Push Complete! ✓              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Published images:${NC}"
echo -e "  • ${FULL_IMAGE_NAME}"
if [ "${TAG}" != "latest" ]; then
    echo -e "  • ${DOCKER_USERNAME}/${IMAGE_NAME}:latest"
fi
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  • Pull on Pi: ${BLUE}docker pull ${FULL_IMAGE_NAME}${NC}"
echo -e "  • Deploy to Pi: ${BLUE}./deploy-to-pi.sh${NC}"
echo -e "  • Or restart compose: ${BLUE}docker compose down && docker compose pull && docker compose up -d${NC}"
echo ""
echo -e "${YELLOW}View on Docker Hub:${NC}"
echo -e "  https://hub.docker.com/r/${DOCKER_USERNAME}/${IMAGE_NAME}/tags"
echo ""
