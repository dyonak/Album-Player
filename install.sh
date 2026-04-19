#!/bin/bash
# Album Player Installation Script
# Run this on a fresh Raspberry Pi to set up the Album Player

set -e

echo "============================================"
echo "Album Player Installation"
echo "============================================"

# Update system
echo "1/6 - Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install base dependencies
echo "2/6 - Installing base dependencies..."
sudo apt-get install -y python3-pip python3-venv git

# Enable SPI for NFC reader
echo "3/6 - Enabling SPI..."
sudo dtparam spi=on

# Install WiFi provisioning dependencies
echo "4/6 - Installing WiFi provisioning dependencies..."
sudo apt-get install -y \
    network-manager \
    dnsmasq \
    iproute2 \
    iw \
    iptables \
    curl

# Install Python dependencies for wificonnect.py (system-wide)
sudo pip3 install flask --break-system-packages

# Set up wificonnect service
echo "5/6 - Setting up WiFi provisioning service..."
mkdir -p ~/album-player
sudo cp services/wificonnect.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable wificonnect.service
echo "WiFi provisioning service installed (will start after code is deployed)"

# Install Docker
echo "6/6 - Installing Docker..."
curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
chmod +x /tmp/get-docker.sh
/tmp/get-docker.sh
sudo usermod -aG docker $USER

echo ""
echo "============================================"
echo "Installation Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Log out and back in (for Docker group permissions)"
echo "2. From your dev machine, run: ./dev_tools/deploy-to-pi.sh"
echo "3. The WiFi provisioning and Album Player will start automatically"
echo ""
