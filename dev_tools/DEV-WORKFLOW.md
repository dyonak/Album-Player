# Album Player - Development Workflow Guide

This guide explains how to quickly test code changes on your Raspberry Pi during development.

## Overview

The development workflow is simple:
1. Make changes on your dev machine
2. Run `./dev_tools/deploy-to-pi.sh`
3. Test on the Pi

Changes are synced via rsync and services are automatically restarted.

## Initial Setup (One-Time)

### 1. Set Up SSH Key Authentication

SSH keys allow password-less deployment:

```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519

# Copy your key to the Pi
ssh-copy-id dyonak@fruit-loops.local

# Test it works (should not ask for password)
ssh dyonak@fruit-loops.local exit
```

### 2. Install Album Player on the Pi

On your Raspberry Pi:

```bash
# Clone the repository
git clone https://github.com/yourusername/Album-Player.git
cd Album-Player

# Run installation
chmod +x install.sh
./install.sh

# Reboot
sudo reboot
```

### 3. Verify Services Running

After reboot:

```bash
# Check all services are running
sudo systemctl status albumplayer
sudo systemctl status webapp
sudo systemctl status spotifyd
```

## Daily Development Workflow

### Making Code Changes

1. **Edit files on your dev machine** using your preferred editor/IDE

2. **Deploy to Pi**:
   ```bash
   ./dev_tools/deploy-to-pi.sh
   ```

   This will:
   - Sync all code files to the Pi
   - Update configuration files
   - Restart affected services

3. **Watch logs** to verify changes:
   ```bash
   # In a separate terminal, SSH to Pi and watch logs
   ssh dyonak@fruit-loops.local
   journalctl -u albumplayer -f
   ```

4. **Test your changes**
   - Scan an NFC tag
   - Use the web interface at http://fruit-loops.local:3029
   - Check Bluetooth functionality

### Customizing Deploy Settings

Override defaults with environment variables:

```bash
# Different Pi hostname or IP
PI_HOST=192.168.1.100 ./dev_tools/deploy-to-pi.sh

# Different username
PI_USER=pi ./dev_tools/deploy-to-pi.sh

# Different target directory
PI_CODE_DIR=/opt/album-player ./dev_tools/deploy-to-pi.sh

# Combine them
PI_HOST=192.168.1.100 PI_USER=pi ./dev_tools/deploy-to-pi.sh
```

Create a `.env` file for persistent settings:

```bash
# .env (in project root)
export PI_HOST=fruit-loops.local
export PI_USER=dyonak
export PI_CODE_DIR=/home/dyonak/album-player
```

Then:
```bash
source .env && ./dev_tools/deploy-to-pi.sh
```

## Useful Commands

### On Your Dev Machine

```bash
# Quick deploy
./dev_tools/deploy-to-pi.sh

# Deploy and immediately watch logs
./dev_tools/deploy-to-pi.sh && ssh dyonak@fruit-loops.local 'journalctl -u albumplayer -f'

# SSH to Pi
ssh dyonak@fruit-loops.local
```

### On the Raspberry Pi

```bash
# View logs for each service
journalctl -u albumplayer -f    # NFC + playback
journalctl -u webapp -f         # Web interface
journalctl -u spotifyd -f       # Spotify Connect

# View recent logs (last 50 lines)
journalctl -u albumplayer -n 50

# Restart a service
sudo systemctl restart albumplayer
sudo systemctl restart webapp
sudo systemctl restart spotifyd

# Check service status
sudo systemctl status albumplayer

# Stop a service (for manual testing)
sudo systemctl stop albumplayer
python3 ~/album-player/AlbumPlayer.py  # Run manually

# Re-enable service
sudo systemctl start albumplayer
```

## Troubleshooting

### "Permission denied" when running deploy script

```bash
chmod +x dev_tools/deploy-to-pi.sh
```

### "Cannot connect" error

Check:
1. Pi is powered on and on the network
2. SSH keys are set up: `ssh-copy-id dyonak@fruit-loops.local`
3. Hostname is correct (try IP address instead)

### Changes not taking effect

1. Check the service restarted:
   ```bash
   ssh dyonak@fruit-loops.local 'systemctl status albumplayer'
   ```

2. Check for Python errors:
   ```bash
   ssh dyonak@fruit-loops.local 'journalctl -u albumplayer -n 20'
   ```

3. Verify files were synced:
   ```bash
   ssh dyonak@fruit-loops.local 'ls -la ~/album-player/*.py'
   ```

### Service keeps crashing

Check logs for the specific error:
```bash
journalctl -u albumplayer --no-pager -n 100
```

Common issues:
- Database permissions: `chmod 755 ~/album_db`
- NFC device not accessible: Check SPI is enabled
- Missing dependencies: Re-run `install.sh`

### Testing without services

Stop services and run manually for debugging:

```bash
# On the Pi
sudo systemctl stop albumplayer
cd ~/album-player
python3 AlbumPlayer.py

# Or for webapp
sudo systemctl stop webapp
python3 Webapp.py
```

## Project Structure

```
Album-Player/
├── AlbumPlayer.py        # Main NFC reader and playback logic
├── Webapp.py             # Flask web interface
├── PlaybackManager.py    # Orchestrates Sonos/Bluetooth output
├── SonosController.py    # Sonos speaker control
├── BluetoothController.py # Bluetooth audio control
├── BluetoothManager.py   # Bluetooth device management
├── SpotifyClient.py      # Spotify Web API client
├── DBConnector.py        # SQLite database access
├── Registrar.py          # Album registration logic
├── install.sh            # Installation script
├── run.sh                # Manual startup script
├── spotifyd.conf         # Spotify Connect configuration
├── services/             # systemd service files
│   ├── albumplayer.service
│   ├── webapp.service
│   ├── spotifyd.service
│   └── wificonnect.service
├── templates/            # Flask HTML templates
├── static/               # Static web assets
└── dev_tools/
    ├── deploy-to-pi.sh   # Development deploy script
    └── DEV-WORKFLOW.md   # This file
```

## Tips for Faster Development

1. **Keep logs open** in a separate terminal while coding

2. **Use VS Code Remote SSH** for direct Pi editing if preferred

3. **Test locally** when possible (some features work without hardware)

4. **Use git branches** for experimental features

5. **Commit working versions** before major changes

## Service Dependencies

```
albumplayer.service
  └── Requires: network-online.target, bluetooth.target

webapp.service
  └── Requires: network-online.target

spotifyd.service
  └── Requires: network-online.target, sound.target, bluetooth.target, dbus.service
```
