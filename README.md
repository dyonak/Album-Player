# NFC Album Player

An NFC-based album player for Raspberry Pi that plays music through Sonos speakers or Bluetooth audio devices via Spotify.

## Features

- **NFC Tag Recognition**: Place an album with an NFC tag on the reader to start playback
- **Automatic Registration**: First-time albums are registered by playing them on Sonos, then the NFC tag is linked
- **Multiple Audio Outputs**: Play to Sonos speakers or Bluetooth audio devices
- **Spotify Connect**: Uses spotifyd as a Spotify Connect receiver for Bluetooth playback
- **Web Interface**: Manage albums, configure speakers, pair Bluetooth devices
- **WiFi Provisioning**: Captive portal for easy WiFi setup on new devices

## Supported Hardware

- **Raspberry Pi**: Pi Zero 2 W, Pi 4, Pi 5 (both 32-bit and 64-bit OS)
- **NFC Reader**: PN532 module connected via SPI
- **Audio Output**: Sonos speakers (any model) or Bluetooth speakers/headphones

## Quick Start

### 1. Prepare the Raspberry Pi

Use Raspberry Pi Imager to flash **Pi OS Lite 64-bit** (recommended) to your SD card.

Configure in Imager settings:
- Enable SSH
- Set hostname (e.g., `albumplayer`)
- Configure WiFi (optional - can use captive portal later)

### 2. Wire the NFC Reader

Connect the PN532 NFC module to the Pi via SPI:

| PN532 Pin | Pi GPIO Pin |
|-----------|-------------|
| VCC       | 3.3V (Pin 1) |
| GND       | GND (Pin 6) |
| SCK       | GPIO 11 / SCLK (Pin 23) |
| MISO      | GPIO 9 / MISO (Pin 21) |
| MOSI      | GPIO 10 / MOSI (Pin 19) |
| SS/CS     | GPIO 8 / CE0 (Pin 24)* |

*Note: The CS pin varies by board. Waveshare HAT uses GPIO 4, Adafruit uses GPIO 7. See Troubleshooting if your reader isn't detected.

Set the PN532 DIP switches to SPI mode.

### 3. Install Album Player

SSH into your Pi and run:

```bash
# Install git
sudo apt install git

# Clone the repository
git clone https://github.com/dyonak/Album-Player.git
cd Album-Player

# Run the installation script
chmod +x install.sh
./install.sh

# Reboot (required for SPI and permissions)
sudo reboot
```

The installer will:
- Install all dependencies (Python, Bluetooth, spotifyd)
- Set up systemd services
- Enable SPI interface
- Configure user permissions

### 4. Configure the Player

After reboot, access the web interface at `http://albumplayer.local:3029`

1. **Config Tab**: Select your Sonos speaker for playback and registration prompts
2. **Bluetooth Tab**: Pair Bluetooth speakers for portable use
3. **Spotify Tab**: Connect your Spotify account (Premium required for playback control)

### 5. Register Albums

1. Place an NFC-tagged album on the reader
2. You'll hear a voice prompt on your Sonos speaker
3. Open the Sonos app and play the album you want to register
4. Wait 10 seconds - the album is now linked to that NFC tag
5. Remove and replace the album to start playback anytime

## Architecture

All services run natively on the Pi (no Docker):

```
┌─────────────────────────────────────────────────────────────┐
│                    Raspberry Pi                              │
├─────────────────────────────────────────────────────────────┤
│  albumplayer.service   │  Main NFC reader + playback logic  │
│  webapp.service        │  Web UI (Flask) on port 3029       │
│  spotifyd.service      │  Spotify Connect receiver          │
│  wificonnect.service   │  WiFi captive portal (if needed)   │
└─────────────────────────────────────────────────────────────┘
         │                        │                    │
         ▼                        ▼                    ▼
    ┌─────────┐            ┌───────────┐        ┌──────────┐
    │ PN532   │            │   Sonos   │        │ Bluetooth│
    │ NFC     │            │  Speaker  │        │  Speaker │
    └─────────┘            └───────────┘        └──────────┘
```

## Services

| Service | Description | Port |
|---------|-------------|------|
| `albumplayer` | NFC reader and playback orchestration | - |
| `webapp` | Web interface for configuration | 3029 |
| `spotifyd` | Spotify Connect receiver for Bluetooth output | 4381 (zeroconf) |
| `wificonnect` | Captive portal for WiFi provisioning | 80 (when active) |

### Managing Services

```bash
# View service status
sudo systemctl status albumplayer
sudo systemctl status webapp
sudo systemctl status spotifyd

# View logs
journalctl -u albumplayer -f
journalctl -u webapp -f
journalctl -u spotifyd -f

# Restart a service
sudo systemctl restart albumplayer
```

## Development

For development workflow, see [dev_tools/DEV-WORKFLOW.md](dev_tools/DEV-WORKFLOW.md).

Quick deploy from your dev machine:
```bash
./dev_tools/deploy-to-pi.sh
```

## Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| `spotifyd.conf` | `~/.config/spotifyd/spotifyd.conf` | Spotify Connect settings |
| `albums.db` | `~/album_db/albums.db` | SQLite database of registered albums |

## Troubleshooting

### NFC reader not detected
```bash
# Check SPI is enabled
ls /dev/spidev*
# Should show /dev/spidev0.0 and /dev/spidev0.1

# If not, enable SPI:
sudo raspi-config
# Interface Options → SPI → Enable
sudo reboot
```

### NFC reader detected but not working (wrong GPIO pin)

Different PN532 boards use different GPIO pins for the chip select (CS) line. If your reader is not detected, you may need to edit `NFCPoller.py` to use the correct pin.

| Board | Pin | GPIO |
|-------|-----|------|
| Standard PN532 breakout | `board.D8` | GPIO 8 (CE0) |
| Adafruit PN532 | `board.D7` | GPIO 7 (CE1) |
| Waveshare PN532 NFC HAT | `board.D4` | GPIO 4 |

Edit line 22 in `NFCPoller.py`:
```python
# Change this line to match your board:
self.cs_pin = DigitalInOut(board.D4)  # Waveshare HAT
# self.cs_pin = DigitalInOut(board.D8)  # Standard breakout (default)
# self.cs_pin = DigitalInOut(board.D7)  # Adafruit PN532
```

After changing, restart the service:
```bash
sudo systemctl restart albumplayer
```

### spotifyd not showing as Spotify device
```bash
# Check spotifyd is running
sudo systemctl status spotifyd
journalctl -u spotifyd -f

# Ensure your Spotify account is connected in the web UI
# Try opening Spotify app on phone and look for "Album Player" device
```

### Bluetooth speaker not connecting
```bash
# Check Bluetooth is on
bluetoothctl power on
bluetoothctl scan on

# Pair manually if needed
bluetoothctl pair XX:XX:XX:XX:XX:XX
bluetoothctl connect XX:XX:XX:XX:XX:XX
```

### Album plays to wrong output
- If Bluetooth speaker is connected, it takes priority
- Disconnect Bluetooth to play to Sonos
- Or use the web UI to manage Bluetooth connections

## Hardware Build Tips

- Place NFC tags about 1" inside album covers, 1" from the bottom
- Position the PN532 reader where tags will naturally align
- Consider a 3D-printed enclosure for a clean look
- Use quality NFC tags (NTAG213 or NTAG215 work well)

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- [spotifyd](https://github.com/Spotifyd/spotifyd) - Spotify Connect daemon
- [SoCo](https://github.com/SoCo/SoCo) - Sonos control library
- [spotipy](https://github.com/spotipy-dev/spotipy) - Spotify Web API wrapper
- [nfcpy](https://github.com/nfcpy/nfcpy) - NFC library for Python
