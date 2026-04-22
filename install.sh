#!/bin/bash
# Album Player Installation Script
# Run this on a fresh Raspberry Pi to set up the Album Player
# Supports: Pi Zero 2 W (armhf/arm64), Pi 4, Pi 5 (arm64)

set -e

echo "============================================"
echo "Album Player Installation"
echo "============================================"
echo ""

# Detect architecture
ARCH=$(uname -m)
DEB_ARCH=$(dpkg --print-architecture)
echo "Detected architecture: $ARCH ($DEB_ARCH)"
echo ""

# Step 1: Update system
echo "[1/10] Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Step 2: Install base dependencies
echo "[2/10] Installing base dependencies..."
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    git \
    bluez \
    wget \
    tar

# Step 3: Install WiFi provisioning dependencies
echo "[3/10] Installing WiFi and network dependencies..."
sudo apt-get install -y \
    network-manager \
    dnsmasq \
    iproute2 \
    iw \
    iptables \
    curl

# Step 4: Install Python system packages
echo "[4/10] Installing Python dependencies..."
sudo apt-get install -y \
    python3-flask \
    python3-requests \
    python3-gevent \
    python3-pip \
    python3-rpi.gpio

# Step 5: Install Python packages (via pip for packages not in apt)
echo "[5/10] Installing Python packages..."
sudo pip3 install --break-system-packages \
    soco \
    spotipy \
    nfcpy \
    adafruit-circuitpython-pn532 \
    cryptography

# Step 6: Install Bluetooth audio dependencies
echo "[6/10] Installing Bluetooth audio support..."
sudo apt-get install -y \
    pulseaudio \
    pulseaudio-module-bluetooth \
    alsa-utils \
    playerctl \
    mpv

# Step 7: Install spotifyd (Spotify Connect daemon)
echo "[7/10] Installing spotifyd..."

SPOTIFYD_VERSION="0.4.2"

# spotifyd requires libssl1.1 which isn't in Bookworm by default
# Add Debian Bullseye repo temporarily to get it
if ! dpkg -l | grep -q "libssl1.1"; then
    echo "  Installing libssl1.1 from Debian Bullseye..."
    echo "deb http://deb.debian.org/debian bullseye main" | sudo tee /etc/apt/sources.list.d/bullseye.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y libssl1.1
    sudo rm /etc/apt/sources.list.d/bullseye.list
    sudo apt-get update
    echo "  libssl1.1 installed"
fi

# Download spotifyd binary based on architecture
if ! command -v spotifyd &> /dev/null; then
    echo "  Downloading spotifyd v${SPOTIFYD_VERSION}..."

    if [ "$ARCH" = "aarch64" ] || [ "$DEB_ARCH" = "arm64" ]; then
        # 64-bit ARM (Pi 4, Pi 5, Pi Zero 2 W with 64-bit OS)
        SPOTIFYD_URL="https://github.com/Spotifyd/spotifyd/releases/download/v${SPOTIFYD_VERSION}/spotifyd-linux-aarch64-slim.tar.gz"
    elif [ "$ARCH" = "armv7l" ] || [ "$DEB_ARCH" = "armhf" ]; then
        # 32-bit ARM (Pi Zero 2 W with 32-bit OS, older Pis)
        SPOTIFYD_URL="https://github.com/Spotifyd/spotifyd/releases/download/v${SPOTIFYD_VERSION}/spotifyd-linux-armv7-slim.tar.gz"
    else
        echo "  Warning: Unknown architecture $ARCH. Skipping spotifyd."
        SPOTIFYD_URL=""
    fi

    if [ -n "$SPOTIFYD_URL" ]; then
        wget -O /tmp/spotifyd.tar.gz "$SPOTIFYD_URL" || {
            echo "  Error: Failed to download spotifyd. You may need to install it manually."
            echo "  URL: $SPOTIFYD_URL"
        }

        if [ -f /tmp/spotifyd.tar.gz ]; then
            tar -xzf /tmp/spotifyd.tar.gz -C /tmp/
            sudo mv /tmp/spotifyd /usr/local/bin/
            sudo chmod +x /usr/local/bin/spotifyd
            rm /tmp/spotifyd.tar.gz
            echo "  spotifyd installed to /usr/local/bin/"
            spotifyd --version
        fi
    fi
else
    echo "  spotifyd already installed: $(spotifyd --version)"
fi

# Configure spotifyd
echo "  Configuring spotifyd..."
mkdir -p ~/.config/spotifyd
mkdir -p ~/.cache/spotifyd
cp spotifyd.conf ~/.config/spotifyd/spotifyd.conf
echo "  spotifyd config installed to ~/.config/spotifyd/"

# Step 8: Set up systemd services
echo "[8/10] Setting up systemd services..."
mkdir -p ~/album-player

# WiFi provisioning service
if [ -f services/wificonnect.service ]; then
    sudo cp services/wificonnect.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable wificonnect.service
    echo "  - wificonnect.service installed"
fi

# Webapp service
if [ -f services/webapp.service ]; then
    sudo cp services/webapp.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable webapp.service
    echo "  - webapp.service installed"
fi

# spotifyd service
if [ -f services/spotifyd.service ]; then
    sudo cp services/spotifyd.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable spotifyd.service
    echo "  - spotifyd.service installed"
fi

# Album Player service (NFC + playback)
if [ -f services/albumplayer.service ]; then
    sudo cp services/albumplayer.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable albumplayer.service
    echo "  - albumplayer.service installed"
fi

# Step 9: Configure user permissions
echo "[9/10] Configuring user permissions..."
sudo usermod -aG audio,bluetooth,spi,gpio $USER
echo "  Added $USER to audio, bluetooth, spi, gpio groups"

# Step 10: Enable SPI for NFC reader
echo "[10/10] Enabling SPI interface..."
if ! grep -q "^dtparam=spi=on" /boot/firmware/config.txt 2>/dev/null && \
   ! grep -q "^dtparam=spi=on" /boot/config.txt 2>/dev/null; then
    # Try new path first (Pi OS Bookworm+), fall back to old path
    if [ -f /boot/firmware/config.txt ]; then
        echo "dtparam=spi=on" | sudo tee -a /boot/firmware/config.txt > /dev/null
    else
        echo "dtparam=spi=on" | sudo tee -a /boot/config.txt > /dev/null
    fi
    echo "  SPI enabled (reboot required)"
else
    echo "  SPI already enabled"
fi

# Create database directory
mkdir -p ~/album_db
echo "  Database directory created at ~/album_db"

echo ""
echo "============================================"
echo "Installation Complete!"
echo "============================================"
echo ""
echo "Services installed (all run natively on the Pi):"
echo "  - wificonnect.service   (WiFi provisioning captive portal)"
echo "  - webapp.service        (Web UI + Bluetooth management)"
echo "  - spotifyd.service      (Spotify Connect receiver)"
echo "  - albumplayer.service   (NFC reader + playback control)"
echo ""
echo "IMPORTANT: A reboot is required for SPI and group changes!"
echo ""
echo "Next steps:"
echo "  1. Reboot the Pi:  sudo reboot"
echo "  2. After reboot, services start automatically"
echo "  3. Access the web UI at: http://$(hostname).local:3029"
echo ""
echo "View logs:"
echo "  journalctl -u albumplayer -f    # NFC + playback"
echo "  journalctl -u webapp -f         # Web interface"
echo "  journalctl -u spotifyd -f       # Spotify Connect"
echo ""
echo "For development, use: ./dev_tools/deploy-to-pi.sh"
echo ""
